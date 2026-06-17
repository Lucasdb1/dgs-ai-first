---
name: devils-advocate-review
description: Critique a technical document as a skeptical senior reviewer. Use after producing a v1 of any AI First exercise deliverable (viability analysis, system prompt, ADR, RAG proposal) to surface weak points, optimistic estimates, hidden assumptions, and unconsidered risks. Produces a structured critique that drives a v2 revision.
---

# Devil's Advocate Review

## When to use

A v1 document exists (analysis, ADR, spec, prompt, code proposal). The user needs a **rigorous adversarial critique** before iterating to v2. Every AI First exercise mandates this iteration step — graders explicitly check that the v2 is verifiably better than the v1.

## How to read the document

Read it twice before writing anything:

1. **Pass 1 — Comprehension.** What is the author claiming? What artifacts/decisions are they proposing? Restate the thesis in one sentence to yourself.
2. **Pass 2 — Hunt.** Now you read adversarially.

## What to hunt for

Score each finding by severity (**High / Medium / Low**) and category. Categories:

| Category | What it means | Example |
|---|---|---|
| **Optimistic estimate** | Number presented as fact but actually assumes the best case | "OCR has 95% accuracy" without saying for what document type |
| **Unstated assumption** | A "given" that isn't a given | Assumes embeddings will be in English when the corpus is Portuguese |
| **Missed failure mode** | A scenario the design doesn't handle | What if two PROC-042 versions both match a query? |
| **Ungrounded recommendation** | Choice without trade-off justification | "Use 512-token chunks" with no reasoning |
| **Single point of failure** | One component whose break kills the system | Manual ingestion pipeline mentioned in passing |
| **Outdated reference** | Cites a fact that has changed | "GPT-4 has 8K context" — outdated; current models have 128K+ |
| **Untestable claim** | Asserted quality that no one could verify | "Responses will be accurate" without a metric |
| **Domain blindness** | Generic LLM wisdom that ignores the actual domain | Ignores that the docs are normative and contradictions matter legally |

## Output format

```markdown
## Devil's Advocate Review — <document name>

### Strengths (keep these in v2)
- <2-4 short bullets — be honest, this isn't pure attack>

### Critical findings (must address)
**[High] <one-line title>**
- *Where:* <section/page reference>
- *What's wrong:* <concise problem statement>
- *Why it matters:* <consequence if shipped as-is>
- *Suggested fix:* <concrete action, not "consider X">

**[High] <next finding>**
...

### Secondary findings (should address)
**[Medium] ...**

### Minor (optional polish)
**[Low] ...**

### Unanswered questions
- <questions the document doesn't answer but should>
```

## Rules of the critique

1. **No empty corrections.** Every "wrong" must come with a concrete fix.
2. **Severity discipline.** High = ship-blocker. Medium = costs time/money post-launch. Low = polish. If everything is High, none of it is.
3. **Quote the document.** When pointing out a problem, quote the exact phrase from the v1. Hand-wavy critique ("the chunking section is weak") is rejected — write "the line 'use 512 tokens' doesn't justify the number relative to the question types listed".
4. **Be specific about consequences.** "This could fail" is rejected. "If `PROC-042` and `PROC-042-v2` both match, the assistant will silently pick one, and an agent quoting the wrong multiplier exposes NovaTech to incorrect billing" is accepted.
5. **Don't smuggle in scope creep.** The critique judges *the current v1 against its own goals*, not against a different document the reviewer wishes existed.
6. **Acknowledge strengths.** A pure-negative review is suspicious and unhelpful for revision.

## When the critique is done

Hand the result back to the author. The author writes v2 and **explicitly maps** v1 findings → v2 changes (one paragraph per High finding). Both versions stay in the deliverable.

## Related

- [[rag-viability-analysis]] — most common upstream skill that feeds this one.
- [[novatech-context]] — load to ground critiques in the actual case study.
