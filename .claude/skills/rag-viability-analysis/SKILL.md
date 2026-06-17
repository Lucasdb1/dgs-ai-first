---
name: rag-viability-analysis
description: Produce a technical viability analysis for a RAG project. Use for Exercise 1.1 of the DGS AI First training, or any task that asks "can we build this RAG system given these documents?" Outputs a 4-section document covering source-type challenges, token estimation, context budget, and chunking strategy — grounded in 2026 research on lost-in-the-middle and context rot.
---

# RAG Viability Analysis

## When to use

A stakeholder (Tech Lead, architect) needs a written analysis that proves a RAG project is technically feasible given the documentation it has to ingest. They want **trade-offs**, not a sales pitch. Output is a markdown document.

## Output structure (4 sections + iteration)

### Section 1 — Source-type challenges

For **each** distinct source type in the user's corpus (PDFs with tables, scanned PDFs, wikis, spreadsheets, etc.), produce a row with:

| Field | What it must contain |
|---|---|
| **Challenge** | The specific extraction/parsing problem (e.g., "tables flatten into cell soup when PDF→text loses the header row association") |
| **Impact on answers** | The downstream effect on the LLM ("the model can't link `multiplier 1.8` to `region Norte`") |
| **Treatment strategy** | A concrete tool or technique (e.g., "use `pdfplumber` for table extraction, store as Markdown in the chunk text") |

**Don't be generic.** "PDFs are hard" is rejected. "PDF tables with 15+ columns lose row-column association in naive text extraction" is accepted.

### Section 2 — Token estimation

Show the math explicitly so the reader can audit it. Use this formula:

```
tokens ≈ words / 0.75
```

Compute per source, then sum. Example for NovaTech-like corpus:

```
800 PDFs × 10 pages × ~500 words/page = 4,000,000 words → ~5.3M tokens
400 wiki pages × 1,500 words           =   600,000 words → ~0.8M tokens
 50 spreadsheets × ~3,000 words        =   150,000 words → ~0.2M tokens
─────────────────────────────────────────────────────────────────────
Total                                                       ~6.3M tokens
```

The exact number isn't the point — **showing you can estimate is**. State the assumption ranges explicitly.

### Section 3 — Context budget analysis

This is where the analysis distinguishes itself from a naive proposal. Three sub-points:

**3a. Hard budget arithmetic.** Given the target model (e.g. GPT-4o = 128K, Claude Sonnet 4.6 = 200K), subtract overhead:
```
128,000   model window
-  2,000   system prompt + instructions
-    100   user question
-  1,000   reserved for the generated answer
= 124,900  tokens available for chunks
÷    500   tokens/chunk
= ~250 chunks per query (theoretical maximum)
```

**3b. Practical budget — lost in the middle.** Cite the established finding: LLMs attend strongly to the **start and end** of the context window and poorly to the **middle**. Stanford/UC-Berkeley first documented this in 2023; positional encoding (RoPE) introduces a decay effect that as of 2026 no production model has fully eliminated. Accuracy on retrieval tasks drops 30%+ when the answer sits in the middle of long contexts. Practical chunk budget is therefore **~5–15 well-ranked chunks**, not 250.

**3c. Context rot.** Long multi-turn conversations (e.g., a chatbot session in Teams) compound three failures: lost-in-the-middle gaps, attention dilution as token count grows, and distractor interference from semantically similar but irrelevant retrieved content. Build the pipeline to truncate or summarize conversation history aggressively.

### Section 4 — Chunking strategy (justified)

Reject fixed-size chunking without justification. Cover all four:

- **Granularity** — size range, justified by document structure and likely query type. For technical/normative docs (policies, procedures, SLAs), prefer **256–512 tokens**. For narrative content prefer 1024–2048. Cite recent research: Chroma's 2025 study showed **recursive splitting at ~400 tokens hits 85–90% recall**; semantic chunking reaches 91–92% but at the cost of embedding every sentence.
- **Boundaries** — semantic/heading-based when documents have structure (Markdown headers, numbered sections), not blind character splits. **Never split tables mid-row.**
- **Overlap** — start with **10–15%**. Mention the January 2026 arXiv finding that overlap provided **no measurable benefit** in their tested setup, so overlap is a tunable, not a default. Above 25% overlap adds noise without quality gains.
- **Retrieval-time ordering** — apply **reorder/rerank** (e.g., place the most relevant chunk last to exploit recency bias and avoid the middle-attention sink). Limit retrieved chunks to ~5 for normative QA.

## Iteration requirement (mandatory)

After producing the v1 of the document, invoke [[devils-advocate-review]] on it to surface weak points, optimistic estimates, and unconsidered risks. Produce a **v2** that incorporates the feedback. Both versions + the critique log are part of the deliverable.

## Style rules for the output document

- Brazilian Portuguese, formal but not academic.
- Markdown. Tables where they help comparison.
- Numbers in arithmetic shown as visible math (not just "approximately X million").
- Cite the model and version assumed (GPT-4o, Claude Sonnet 4.6, etc.) when the budget math depends on it.
- **Do not invent figures.** If a number isn't given, state the assumption range.

## Related

- [[novatech-context]] — load this first when the analysis is for the NovaTech case.
- [[devils-advocate-review]] — required follow-up step.
