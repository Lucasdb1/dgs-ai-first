# Exercício 2.2 — Evidência de uso do GitHub Copilot

> **Papel:** Desenvolvedor | **Cenário 2**
> **Ferramenta:** GitHub Copilot (modo agente no VS Code)
> **Tarefa:** Implementar TASK-001 (HTTP trigger) + TASK-002 (validação Zod)

---

## Prompt usado com o Copilot

O Copilot foi acionado com o `plan.md` e o `AGENTS.md` no contexto do repositório. O prompt enviado foi:

```
Com base no plan.md do query endpoint e seguindo os padrões do AGENTS.md,
implemente a TASK-001 e TASK-002:

- TASK-001: Azure Function HTTP trigger v4 para POST /api/query. Retorna
  placeholder 200. Usa pino para logging. Arquivo em src/functions/query/handler.ts.

- TASK-002: Validação de input com Zod. Campos: question (string, obrigatório,
  não-vazio, max 1000 chars). Arquivo em src/functions/query/validator.ts.

Padrões obrigatórios: TypeScript strict, Azure Functions v4 API (app.http),
pino (nunca console.log), Zod safeParse.
```

---

## Output do Copilot — v1 (antes da revisão crítica)

O Copilot gerou a seguinte versão inicial do `handler.ts`:

```typescript
// v1 gerado pelo Copilot — ANTES da revisão crítica
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { z } from "zod";
import pino from "pino";

const logger = pino();

const QuerySchema = z.object({
  question: z.string().min(1),
});

export async function queryHandler(
  req: HttpRequest,
  context: InvocationContext
): Promise<HttpResponseInit> {
  if (req.method !== "POST") {
    return { status: 405, body: "Method Not Allowed" };
  }

  const body = await req.json();
  const parsed = QuerySchema.safeParse(body);

  if (!parsed.success) {
    console.log("Validation error:", parsed.error); // ← problema: console.log
    return { status: 400, body: parsed.error.message };
  }

  logger.info({ question: parsed.data.question }, "query recebida");

  return {
    status: 200,
    jsonBody: { answer: "not implemented", source_document: null }, // ← source_document: null
  };
}

app.http("queryEndpoint", {
  methods: ["POST"],  // ← guard 405 interno nunca executa
  authLevel: "function",
  handler: queryHandler,
});
```

---

## Problemas identificados na v1 → correções aplicadas na v2

| # | Problema no output do Copilot | Correção na v2 |
|---|---|---|
| 1 | `source_document: null` no placeholder — propaga null para futuras tasks | Mantido como placeholder explícito documentado com TODO. Schema de saída a ser definido na TASK-008 |
| 2 | `methods: ["POST"]` + guard `if (req.method !== "POST")` — guard nunca executa, runtime rejeita antes | Documentado como decisão a ser tomada pelo TL (ADR) |
| 3 | `console.log("Validation error:", ...)` — viola padrão pino | Substituído por `log.warn({ validationError: ... })` |
| 4 | `z.string().min(1)` aceita strings de espaços em branco | Adicionado `.trim()` antes do `.min(1)` na v2 do validator |
| 5 | `pino()` instanciado localmente — desconectado do logger compartilhado de `shared/logger` | Substituído por `import { logger } from "../../shared/logger"` + `logger.child(...)` |

---

## Output do Copilot — v2 (após revisão)

Após aplicar as correções, o código ficou conforme os arquivos em `src/functions/query/handler.ts` e `src/functions/query/validator.ts`.

As principais melhorias entre v1 e v2:
- Zero `console.log` — pino via `shared/logger` com `child({ requestId })`
- Mensagens de erro Zod com `required_error` e `invalid_type_error` explícitos
- `validator.ts` isolado e testável independentemente (TASK-009 não precisará de mocks)
