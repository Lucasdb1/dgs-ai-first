"""
Ingestão do pipeline de RAG — NovaTech

Estratégia de chunking (ver analise-tecnica-v2.md §4):
  - Dois perfis: standard (texto narrativo, ~256-512 tokens) e table (tabela inteira, cap ~2K tokens)
  - Fronteiras semânticas: divisão em headings H2/H3, nunca no meio de uma frase
  - Overlap de 40 palavras entre chunks sequenciais (evita perda em fronteiras de seção)
  - Metadados por chunk: doc_id, source_type, status, version — usados no re-ranking
"""

import re
import hashlib
import chromadb
from sentence_transformers import SentenceTransformer

from .config import DOCS_DIR, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL
from .config import DOC_METADATA, STANDARD_MAX_WORDS, TABLE_MAX_WORDS, OVERLAP_WORDS


def _has_table(text: str) -> bool:
    lines = text.splitlines()
    table_lines = [l for l in lines if l.strip().startswith("|")]
    return len(table_lines) >= 3


def _table_to_prose(text: str) -> str:
    """
    Converte tabela Markdown em prosa para melhorar a qualidade do embedding.

    Modelos de embedding pequenos (all-MiniLM-L6-v2) não embeddificam bem
    estrutura tabular com '|' — geram vetores que não capturam a relação
    semântica entre coluna e valor. Converter para prosa antes de embeddar
    é prática padrão em RAG para dados tabulares.
    """
    table_lines = [l.strip() for l in text.splitlines() if l.strip().startswith("|")]
    if len(table_lines) < 3:
        return ""

    headers = [c.strip() for c in table_lines[0].split("|") if c.strip()]
    # table_lines[1] é o separador (---)
    prose = []
    for line in table_lines[2:]:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) != len(headers):
            continue
        metric = cells[0]
        values = ", ".join(f"{headers[i]}: {cells[i]}" for i in range(1, len(headers)))
        prose.append(f"{metric} — {values}.")

    return " ".join(prose)


def _chunk_id(doc_id: str, section: str, index: int) -> str:
    raw = f"{doc_id}::{section}::{index}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _split_sections(text: str) -> list[dict]:
    """Split document into sections at H2/H3 heading boundaries.

    H1 is intentionally excluded from the split boundary so the document
    title + metadata block (version, responsible, classification) stays
    attached to the first section instead of becoming an orphan ~30-word chunk.
    """
    # Split keeping the delimiter (heading) with each section
    parts = re.split(r"(?=\n#{2,3} )", "\n" + text)
    sections = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Match any heading level (H1–H3) to extract the label
        heading_match = re.match(r"^#{1,3}\s+(.+)", part)
        heading = heading_match.group(1).strip() if heading_match else "header"
        sections.append({"heading": heading, "text": part})
    return sections


def _apply_overlap(sections: list[dict]) -> list[dict]:
    """Prepend the last OVERLAP_WORDS words of the previous section to each standard chunk."""
    result = []
    for i, sec in enumerate(sections):
        if i == 0 or sec.get("chunk_type") == "table":
            result.append(sec)
            continue
        prev_words = sections[i - 1]["text"].split()
        overlap_text = " ".join(prev_words[-OVERLAP_WORDS:])
        sec = dict(sec)
        sec["text"] = overlap_text + "\n\n" + sec["text"]
        result.append(sec)
    return result


def build_chunks(text: str, doc_id: str) -> list[dict]:
    sections = _split_sections(text)

    chunks = []
    for sec in sections:
        if _has_table(sec["text"]):
            # Table profile: keep intact, mas prepende prosa para melhorar embedding
            words = len(sec["text"].split())
            if words > TABLE_MAX_WORDS:
                sec["text"] = " ".join(sec["text"].split()[:TABLE_MAX_WORDS])
            prose = _table_to_prose(sec["text"])
            if prose:
                # Prosa no início (capturada pelo embedding) + tabela original (lida pelo LLM)
                sec["text"] = prose + "\n\n" + sec["text"]
            sec["chunk_type"] = "table"
            chunks.append(sec)
        else:
            words = sec["text"].split()
            if len(words) <= STANDARD_MAX_WORDS:
                sec["chunk_type"] = "standard"
                chunks.append(sec)
            else:
                # Sub-split large text sections at paragraph boundaries
                paragraphs = re.split(r"\n{2,}", sec["text"])
                buffer, buf_words = [], 0
                for para in paragraphs:
                    pw = len(para.split())
                    if buf_words + pw > STANDARD_MAX_WORDS and buffer:
                        chunks.append({
                            "heading": sec["heading"],
                            "text": "\n\n".join(buffer),
                            "chunk_type": "standard",
                        })
                        buffer, buf_words = [], 0
                    buffer.append(para)
                    buf_words += pw
                if buffer:
                    chunks.append({
                        "heading": sec["heading"],
                        "text": "\n\n".join(buffer),
                        "chunk_type": "standard",
                    })

    return _apply_overlap(chunks)


def ingest(reset: bool = True) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    model = SentenceTransformer(EMBEDDING_MODEL)
    total = 0

    for filename, meta in DOC_METADATA.items():
        filepath = DOCS_DIR / filename
        if not filepath.exists():
            print(f"[WARN] Arquivo não encontrado: {filepath}")
            continue

        text = filepath.read_text(encoding="utf-8")
        chunks = build_chunks(text, meta["doc_id"])

        print(f"\n[{meta['doc_id']}] {len(chunks)} chunks gerados")

        for i, chunk in enumerate(chunks):
            cid = _chunk_id(meta["doc_id"], chunk["heading"], i)
            embedding = model.encode(chunk["text"]).tolist()

            chunk_meta = {
                **{k: str(v) for k, v in meta.items()},
                "section": chunk["heading"][:200],
                "chunk_type": chunk["chunk_type"],
                "chunk_index": str(i),
            }

            collection.add(
                ids=[cid],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[chunk_meta],
            )

            approx_tokens = int(len(chunk["text"].split()) / 0.75)
            flag = " [TABLE]" if chunk["chunk_type"] == "table" else ""
            print(f"  {i:02d} | {chunk['heading'][:45]:<45} | ~{approx_tokens:>4} tokens{flag}")
            total += 1

    print(f"\nIngestão concluída: {total} chunks indexados em '{COLLECTION_NAME}'")
    return collection


if __name__ == "__main__":
    ingest()
