"""
Busca semântica no ChromaDB.

Re-ranking simples: chunks de source_type='superseded' recebem penalidade de score,
alinhado com a estratégia de hierarquia de fontes (analise-tecnica-v2.md §4.5).
"""

from dataclasses import dataclass
import chromadb
from sentence_transformers import SentenceTransformer

from .config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

SUPERSEDED_PENALTY = 0.15  # subtrai do score cosine para docs superseded
INFORMAL_PENALTY = 0.10    # subtrai do score cosine para fonte informal


@dataclass
class ChunkResult:
    chunk_id: str
    text: str
    score: float          # score ajustado (após penalidade)
    raw_score: float      # score bruto da busca vetorial
    doc_id: str
    section: str
    source_type: str
    status: str
    chunk_type: str


def buscar(
    pergunta: str,
    n_retrieve: int = 20,
    n_return: int = 8,
) -> list[ChunkResult]:
    """
    Busca os chunks mais relevantes para a pergunta.

    Fluxo:
      1. Gera embedding da pergunta
      2. Recupera top-n_retrieve por similaridade vetorial
      3. Aplica penalidade de re-ranking para fontes superseded/informais
      4. Retorna top-n_return após re-ranking, ordenado por score ajustado (desc)
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode(pergunta).tolist()

    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_retrieve, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    results = []
    for cid, doc, meta, dist in zip(
        raw["ids"][0],
        raw["documents"][0],
        raw["metadatas"][0],
        raw["distances"][0],
    ):
        # ChromaDB com espaço cosine retorna distância (0=idêntico, 2=oposto)
        # Converter para score de similaridade [0, 1]
        raw_score = 1.0 - (dist / 2.0)

        adjusted = raw_score
        if meta.get("status") == "superseded":
            adjusted -= SUPERSEDED_PENALTY
        if meta.get("source_type") == "informal":
            adjusted -= INFORMAL_PENALTY

        results.append(ChunkResult(
            chunk_id=cid,
            text=doc,
            score=round(adjusted, 4),
            raw_score=round(raw_score, 4),
            doc_id=meta.get("doc_id", ""),
            section=meta.get("section", ""),
            source_type=meta.get("source_type", ""),
            status=meta.get("status", ""),
            chunk_type=meta.get("chunk_type", ""),
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:n_return]


def imprimir_resultados(pergunta: str, resultados: list[ChunkResult]) -> None:
    print(f"\n{'='*70}")
    print(f"PERGUNTA: {pergunta}")
    print(f"{'='*70}")
    for i, r in enumerate(resultados, 1):
        flags = []
        if r.status == "superseded":
            flags.append(f"-{SUPERSEDED_PENALTY} superseded")
        if r.source_type == "informal":
            flags.append(f"-{INFORMAL_PENALTY} informal")
        penalty_flag = f" [{', '.join(flags)}]" if flags else ""
        print(f"\n[{i}] score={r.score:.4f} (raw={r.raw_score:.4f}{penalty_flag})")
        print(f"     {r.doc_id} | {r.section[:50]} | {r.source_type} | {r.status}")
        print(f"     {r.text[:200].replace(chr(10), ' ')}...")
