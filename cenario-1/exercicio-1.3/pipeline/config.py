from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR.parent.parent / "material-pratica-1"
CHROMA_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "novatech_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking
# STANDARD_MAX_WORDS: 400 palavras × (1/0.75) × 1.2 (PT-BR) ≈ 533 tokens por chunk.
# Orçamento calculado no Ex. 1.1: janela GPT-4o 128K, system prompt ~2K, margem ~1K,
# 5-8 chunks práticos → teto por chunk ≈ 500-600 tokens. 400 palavras fica dentro desse envelope.
STANDARD_MAX_WORDS = 400

# TABLE_MAX_WORDS: cap de 1500 palavras (~2000 tokens) evita que tabelas grandes
# dominem o contexto. Tabelas da NovaTech (multiplicadores, SLA) têm ~200-400 palavras —
# o cap é uma salvaguarda, não um limite ativo nos documentos atuais.
TABLE_MAX_WORDS = 1500

# OVERLAP_WORDS: 40 palavras = ~10% de um chunk padrão de 400 palavras.
# Garante continuidade de contexto em fronteiras de seção sem duplicar tokens em excesso.
OVERLAP_WORDS = 40

# Per-document metadata
DOC_METADATA = {
    "POL-001-politica-devolucao.md": {
        "doc_id": "POL-001",
        "source_type": "normative",
        "status": "active",
        "version": "3.1",
    },
    "PROC-042-frete-especial-v1.md": {
        "doc_id": "PROC-042",
        "source_type": "normative",
        "status": "superseded",
        "version": "1.0",
        "superseded_by": "PROC-042-v2",
    },
    "PROC-042-v2-frete-especial-revisado.md": {
        "doc_id": "PROC-042-v2",
        "source_type": "normative",
        "status": "active",
        "version": "2.0",
    },
    "SLA-2024-tabela-sla-clientes.md": {
        "doc_id": "SLA-2024",
        "source_type": "normative",
        "status": "active",
        "version": "2024.1",
    },
    "FAQ-atendimento.md": {
        "doc_id": "FAQ-Atendimento",
        "source_type": "informal",
        "status": "active",
        "validated": "false",
    },
}
