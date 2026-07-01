# Exercício 3.1 — Evidência de uso do GitHub Copilot

> **Papel:** Desenvolvedor | **Cenário 3**
> **Tarefa:** Gerar o schema Zod + response-validator.ts com Copilot, depois revisar com Claude

---

## Prompt usado com o Copilot (geração do schema e validator)

```
No projeto NovaTech Assistant (TypeScript strict, Azure Functions v4, Zod, pino),
crie o arquivo src/services/response-validator.ts com:

1. Schema Zod para structured output com campos:
   - answer: string obrigatório
   - source_document: string obrigatório (resposta sem fonte deve ser rejeitada)
   - confidence_score: number entre 0 e 1

2. Função validateResponse(raw: unknown): ValidationResult que:
   - Valida contra o schema
   - Guardrail 1: bloqueia se source_document estiver vazio
   - Guardrail 2: bloqueia resposta que mencione "carga perigosa" + "devolução"
     sem conter negativa (regra: POL-001 §3.2 — ANTT classes 1-6 não são
     elegíveis para devolução padrão)
   - Em qualquer falha: loga com pino e retorna SAFE_DEFAULT
   - Segue o AGENTS.md do projeto (sem as any, sem console.log, imports ESM)
```

---

## O que o Copilot gerou na v1

```typescript
// v1 — output bruto do Copilot
export const AssistantResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().optional(),   // ← problema: deveria ser obrigatório
  confidence_score: z.number().min(0).max(1),
});
// schema sem .strict() — aceita campos extras

// Guardrail 2 v1:
const hasDangerousCargo = answer.includes("carga perigosa");
const hasReturn = answer.includes("devolução");
// ← só cobre literais exatos, não variações
```

---

## Problemas identificados no code review (Claude)

| # | Problema | Por que é real |
|---|---|---|
| 1 | `source_document: z.string().optional()` — campo que deveria ser obrigatório estava opcional | Um modelo que omitir `source_document` passaria no schema sem bloqueio |
| 2 | Schema sem `.strict()` — aceita campos extras | Um modelo que retorne `{ answer, source, confiança }` passaria, com `source_document` nunca preenchido |
| 3 | Regex v1 só cobre `"carga perigosa"` e `"devolução"` literais | `"Cargas da classe 3 da ANTT podem ser retornadas"` não seria detectado (falso negativo) |

---

## Correções aplicadas (v2)

```typescript
// v2 — após code review
export const AssistantResponseSchema = z.object({
  answer: z.string().min(1),
  source_document: z.string().min(1, "source_document é obrigatório"),  // ← obrigatório
  confidence_score: z.number().min(0).max(1),
}).strict();  // ← rejeita campos extras

// Guardrail 2 v2 — regex com variações:
const DANGEROUS_CARGO_PATTERN =
  /carga[s]?\s*perigosa[s]?|classe[s]?\s+[1-6]\s+da\s+antt|antt\s+classe[s]?\s+[1-6]/i;
const RETURN_PATTERN =
  /devolu[cç][aã]o|devolver|devolv[ae]|retorno\s+de\s+produto/i;
const NEGATION_PATTERN =
  /não\s+(é\s+)?poss[ií]vel|não\s+pode[m]?|impossível|vetad[ao]|bloqueado/i;
```

---

## Resumo da iteração

| Versão | Gerado por | Problema principal |
|---|---|---|
| v1 | Copilot | `source_document` opcional, sem `.strict()`, regex literal |
| v2 | Copilot + revisão Claude | Campo obrigatório, `.strict()`, regex com variações |
