from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR.parent.parent / "material-pratica-1"
CHROMA_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "novatech_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking
STANDARD_MAX_WORDS = 400   # ~533 tokens (PT-BR ~1.2x factor)
TABLE_MAX_WORDS = 1500     # ~2000 tokens cap for table chunks
OVERLAP_WORDS = 40         # ~10% of standard chunk

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
