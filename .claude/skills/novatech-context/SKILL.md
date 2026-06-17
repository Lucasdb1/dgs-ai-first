---
name: novatech-context
description: Load the NovaTech case-study context for the DGS AI First training. Use whenever the user references "Prática 1", "Cenário 1", NovaTech, or any of the seeded documents (POL-001, PROC-042, SLA-2024, FAQ-Atendimento). Provides file locations, intentional traps, and evaluation criteria so deliverables align with what the graders score on.
---

# NovaTech Case Study — Quick Context

## The fictional scenario

NovaTech is a **1,200-person Brazilian logistics company**. DB1 was hired to build an internal **AI assistant** that lets 45 customer-service agents query company documentation in natural language. Goal: cut per-ticket lookup time from **12 min → < 2 min**. Stack constraint: Microsoft 365 E3 + Azure AI Services already provisioned. Budget: **3 months** discovery + dev + go-live.

Documentation lives in 3 fragmented sources: **SharePoint** (~800 PDFs/DOCX), **Confluence** (~400 wiki pages), **shared network drive** (~50 XLSX). Updates are monthly, by 3 different departments, **without unified revision** — so contradictory documents exist by design.

## Source materials on disk

All Cenário 1 source files are in **`material-pratica-1/`** inside the repo:

| File | Purpose |
|---|---|
| `exercicio-fase-1-entendimento.md` | Exercise statements for all 5 roles |
| `anexo-a-documentacao-simulada-novatech.md` | The 5 NovaTech documents combined (source of truth) |
| `anexo-b-chunks-referencia-rag.md` | Simulated RAG chunks + **question→chunk coverage map** (gabarito for retrieval tests) |
| `POL-001-politica-devolucao.md` | Doc 1 individual (return policy) |
| `PROC-042-frete-especial-v1.md` | Doc 2 (freight v1) |
| `PROC-042-v2-frete-especial-revisado.md` | Doc 3 (freight v2 — **contradictory version**) |
| `SLA-2024-tabela-sla-clientes.md` | Doc 4 (SLA table by tier) |
| `FAQ-atendimento.md` | Doc 5 (informal Q&A by experienced agents) |

## Intentional traps in the documents

The graders specifically check whether deliverables catch these. Any solution that ignores them loses points.

1. **PROC-042 vs PROC-042-v2** — Same document number, different multipliers, **no vigência flag**. The pipeline must surface this conflict, not silently pick one.
2. **POL-001 §3.2** — Hazardous cargo (ANTT classes 1–6) is **NOT eligible** for standard returns. An assistant that says "7 days for any cargo" is hallucinating by ignoring the exception.
3. **SLA-2024** has only **Gold / Silver / Standard** — there is **no "Platinum"**. If asked about Platinum the assistant must say it doesn't exist, not invent values.
4. **FAQ-Atendimento** is informal, written by agents without formal validation — it can contradict POL/PROC. Treat as lower-priority source.
5. The PROC-042 freight formula needs a **base value** that's not in the chunks — answering "the price is X" without that base is hallucination.

## Reference chunks (Anexo B)

When testing prompts, simulate the RAG retriever by selecting 3-5 chunks from Anexo B that would match the user question by semantic similarity. Available chunks:

- POL-001-A (return general rule), POL-001-B (exceptions), POL-001-C (procedure)
- PROC-042-A and -B (v1 multipliers — older)
- PROC-042-v2-A and -B (v2 multipliers — newer)
- SLA-2024-A (Gold/Silver/Standard table)
- FAQ-A, FAQ-B (informal answers, possibly contradicting POL/PROC)

The `anexo-b-chunks-referencia-rag.md` file has the **complete coverage map**: question → expected chunks. Use it as the gabarito for retrieval tests in Exercise 1.3.

## Deliverable structure

All Cenário 1 work goes in branch `cenario-1` with this structure:

```
cenario-1/
├── exercicio-1.1/   ← technical viability analysis
├── exercicio-1.2/   ← system prompt prototype + test logs
└── exercicio-1.3/   ← functional RAG pipeline (Python)
```

Every deliverable must include **evidence of AI tool use** (conversation logs / Copilot screenshots / iteration history) — it's part of the grade, not optional.

## Evaluation criteria common to all exercises

- Solutions are **specific to NovaTech**, not generic.
- The participant **iterated** with the LLM (v1 → critique → v2), not single-shot.
- Choices are **justified by trade-offs**, not by tool preference.
- Demonstrates understanding that **RAG quality is a data engineering problem**, not just an API call.

## Related skills

- [[rag-viability-analysis]] — use for Exercise 1.1 structure.
- [[devils-advocate-review]] — use for the v1→v2 iteration step required by every exercise.
