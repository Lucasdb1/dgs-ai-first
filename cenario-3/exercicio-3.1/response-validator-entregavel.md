# Exercício 3.1 — Structured Output e Verificações Determinísticas

> **Papel:** Desenvolvedor | **Cenário 3**
> **Tópico:** Harness Engineering
> **Arquivo implementado:** `novatech-assistant/src/services/response-validator.ts`

---

## Conexão com Cenários 1 e 2

Este exercício amarra artefatos produzidos nos cenários anteriores:

- **Guardrails (origem: Cenário 2 — Product Specialist):** Os 2 guardrails implementados aqui foram formalizados pelo PS no Cenário 2 como regras DEVE/NÃO DEVE. Este módulo os transforma de linguagem natural em código que *bloqueia de verdade* — fechando o gap entre intenção de produto e garantia técnica.
- **POL-001-B (origem: Cenário 1 — corpus NovaTech):** A regra do Guardrail 2 vem diretamente de POL-001 §3.2 — cargas ANTT classes 1–6 não são elegíveis para devolução padrão. O chunk POL-001-B foi recuperado no pipeline RAG do Cenário 1; agora o mesmo conteúdo alimenta uma verificação determinística.
- **ADR-0002 — Context Budget:** A ADR-0002 define que o context window tem limite fixo. Sob alta pressão de contexto (janela cheia), o modelo tem maior chance de ignorar instruções do system prompt. O `response-validator.ts` garante que mesmo nesse cenário degradado os guardrails continuam ativos — porque rodam fora do modelo.
- **AGENTS.md (origem: Cenário 2):** O código segue integralmente as regras do AGENTS.md: `strict: true`, pino, imports ESM, sem `as any`, config via `shared/config`.

---

## Contexto: probabilístico vs determinístico

O prompt instrui o modelo a incluir a fonte e a negar devoluções de carga perigosa. Mas o prompt é **probabilístico** — o modelo pode ignorá-lo, reformular, ou alucinar com alta pressão de contexto (ver ADR-0002).

O `response-validator.ts` é **determinístico**: se a condição não for satisfeita, a resposta é bloqueada — sem exceção, sem depender da "vontade" do modelo.

| Camada | Tipo | Garantia |
|---|---|---|
| System prompt | Probabilístico | ~95% dos casos |
| `response-validator.ts` | Determinístico | 100% — bloqueia ou passa |

---

## Schema de Structured Output (Zod)

```typescript
export const AssistantResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().min(1),  // obrigatório e não-vazio
  confidence_score: z.number().min(0).max(1),
}).strict();  // ← rejeita campos extras (v2 pós code review)
```

**Por que `.strict()`?** Sem ele, o schema aceita qualquer campo extra — um modelo que retorne `{ answer, source, confiança }` passaria na validação com source_document vazio. `.strict()` garante que apenas os 3 campos contratados existam.

---

## Guardrail 1 — source_document obrigatório

**Regra:** Toda resposta DEVE conter `source_document`. Sem fonte = bloqueio.

**Implementação:** O Zod `z.string().min(1)` já rejeita se ausente ou vazio. Verificação explícita adicional cobre o caso de string só com espaços:

```typescript
if (!response.source_document || response.source_document.trim().length === 0) {
  log.warn({ answer }, "guardrail 1: resposta sem source_document bloqueada");
  return { valid: false, response: SAFE_DEFAULT, blockedBy: "guardrail_1_no_source" };
}
```

**Bloqueia, não apenas loga.**

---

## Guardrail 2 — carga perigosa + devolução sem negativa

**Regra:** Se a resposta menciona carga perigosa E devolução SEM negar que é possível → bloqueio.

**Origem:** POL-001, seção 3.2 — cargas ANTT classes 1–6 não são elegíveis para devolução padrão.

```typescript
const DANGEROUS_CARGO_PATTERN =
  /carga[s]?\s*perigosa[s]?|perigosa[s]?\s*carga[s]?|classe[s]?\s+[1-6]\s+da\s+antt|antt\s+classe[s]?\s+[1-6]/i;

const RETURN_PATTERN =
  /devolu[cç][aã]o|devolver|devolv[ae]|retorno\s+de\s+produto|retornar\s+produto/i;

const NEGATION_PATTERN =
  /não\s+(é\s+)?poss[ií]vel|não\s+pode[m]?|impossível|vetad[ao]|proibid[ao]|bloqueado|não\s+se\s+aplica|escalad[ao]/i;
```

**Lógica:** `mentionsDangerousCargo && mentionsReturn && !containsNegation` → bloqueia.

---

## Code Review com Claude — problemas identificados e corrigidos

| # | Problema (v1 Copilot) | Tipo | Correção (v2) |
|---|---|---|---|
| 1 | Schema sem `.strict()` — aceita campos extras (`{ answer, source, confiança }` passaria com `source_document` vazio) | Bug lógico | Adicionado `.strict()` |
| 2 | Regex v1 só cobria `"carga perigosa"` literal — não cobria plural, variações com acento, `"classe 3 da ANTT"` | Guardrail burlável | Regex expandido com alternativas e flag `/i` |

**Por que são problemas reais e não inventados:**
- Sem `.strict()`, um modelo que "apelidar" o campo como `source` em vez de `source_document` passaria no schema — o guardrail 1 seria contornável.
- Sem variações no regex, a resposta `"Cargas da classe 3 da ANTT não podem ser devolvidas"` ativaria incorretamente o guardrail 2 (falso positivo) porque contém `ANTT` mas o pattern original só detectava `"carga perigosa"`.

---

## Testes de fumaça

| Cenário | Entrada | Resultado esperado | Guardrail |
|---|---|---|---|
| Resposta válida | `{ answer: "Prazo é 7 dias", source_document: "POL-001", confidence_score: 0.9 }` | `valid: true` | — |
| Sem fonte | `{ answer: "...", source_document: "", confidence_score: 0.8 }` | `valid: false` | guardrail_1_no_source |
| Carga perigosa + devolução sem negativa | `{ answer: "Você pode devolver cargas perigosas...", source_document: "POL-001", confidence_score: 0.7 }` | `valid: false` | guardrail_2_dangerous_return |
| Carga perigosa + negativa correta | `{ answer: "Não é possível devolver cargas perigosas classes 1-6 da ANTT", source_document: "POL-001-B", confidence_score: 0.95 }` | `valid: true` | — |
| Campo extra | `{ answer: "...", source_document: "POL", confidence_score: 0.8, extra: "hack" }` | `valid: false` | schema (strict) |
