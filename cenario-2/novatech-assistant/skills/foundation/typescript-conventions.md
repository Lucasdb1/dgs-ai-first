# SKILL: typescript-conventions

> **Nível:** Foundation
> **Path no repo:** `skills/foundation/typescript-conventions.md`
> **Ativação:** Use quando o agente gerar qualquer arquivo `.ts` ou `.tsx` no projeto NovaTech Assistant.
> **Depende de:** nenhuma (é a base de todas as outras skills)
> **Criada por:** Tech Lead | **Versão:** 1.0 | **Testada com:** GitHub Copilot

---

## Contexto

Este projeto usa TypeScript com `strict: true`. O compilador está configurado em `tsconfig.json` com `"strict": true, "noImplicitAny": true, "strictNullChecks": true`. Todo código gerado DEVE compilar sem erros nessa configuração.

O projeto usa ESM (`"type": "module"` no `package.json`). Imports `require()` estão proibidos.

O logger oficial é `pino`, importado de `../../shared/logger` (ou caminho relativo equivalente). `console.log`, `console.error`, `console.warn` estão **proibidos em produção**.

---

## Regras Obrigatórias

### R1 — Tipos explícitos em toda função exportada

DEVE declarar tipo de retorno em toda função exportada. Funções internas com tipo inferível pelo compilador são permitidas.

**DO:**
```typescript
export function buildPrompt(chunks: SearchChunk[], question: string): string {
  return chunks.map(c => c.text).join("\n\n") + "\n\nPergunta: " + question;
}
```

**DON'T:**
```typescript
// tipo de retorno implícito — Copilot gera isso com frequência
export function buildPrompt(chunks, question) {
  return chunks.map(c => c.text).join("\n\n") + "\n\nPergunta: " + question;
}
```

---

### R2 — Proibido `as any`

NUNCA use `as any` para contornar o sistema de tipos. Se o tipo é desconhecido, use `unknown` e faça narrowing explícito.

**DO:**
```typescript
function parseAzureResponse(raw: unknown): SearchResult {
  if (!isSearchResult(raw)) {
    throw new SearchError("Resposta inesperada do Azure AI Search");
  }
  return raw;
}

function isSearchResult(value: unknown): value is SearchResult {
  return (
    typeof value === "object" &&
    value !== null &&
    "value" in value &&
    Array.isArray((value as Record<string, unknown>).value)
  );
}
```

**DON'T:**
```typescript
// Copilot gera isso quando não conhece o tipo exato
function parseAzureResponse(raw: any): SearchResult {
  return raw as SearchResult;
}
```

---

### R3 — Logger pino, nunca console

DEVE usar o logger de `../../shared/logger`. DEVE criar um `child` com contexto da função/módulo.

**DO:**
```typescript
import { logger } from "../../shared/logger";

const log = logger.child({ module: "search-service" });

export async function searchChunks(embedding: number[]): Promise<SearchChunk[]> {
  log.info({ embeddingDim: embedding.length }, "iniciando busca no Azure AI Search");
  // ...
  log.info({ chunkCount: results.length }, "busca concluída");
  return results;
}
```

**DON'T:**
```typescript
// Proibido — vaza para stdout sem estrutura e sem contexto de request
export async function searchChunks(embedding: number[]): Promise<SearchChunk[]> {
  console.log("iniciando busca", embedding.length);
  // ...
  console.log("resultados:", results);
  return results;
}
```

---

### R4 — Imports ESM, proibido `require()`

DEVE usar `import`/`export` estático. Proibido `require()`, `import()` dinâmico, e `module.exports`.

**DO:**
```typescript
import { app, HttpRequest, HttpResponseInit } from "@azure/functions";
import { z } from "zod";
import { logger } from "../../shared/logger";
```

**DON'T:**
```typescript
// Copilot às vezes gera isso em projetos mistos CJS/ESM
const { app } = require("@azure/functions");
const pino = require("pino");
```

---

### R5 — Exports nomeados, proibido `export *`

DEVE exportar símbolos individualmente. Proibido `export *` (wildcard) — quebra tree shaking e torna dependências implícitas.

**DO:**
```typescript
// types.ts
export type { QueryInput, QueryOutput, SearchChunk };

// index.ts do módulo
export { queryHandler } from "./handler";
export { QueryInputSchema } from "./validator";
```

**DON'T:**
```typescript
// Copilot gera isso para "facilitar" imports de barrel
export * from "./handler";
export * from "./validator";
export * from "./response-builder";
```

---

### R6 — Strings de input DEVEM ser `.trim()`'d antes de validação

Todo campo de texto vindo do usuário ou de APIs externas DEVE ser normalizado com `.trim()` antes de entrar no schema Zod.

**DO:**
```typescript
export const QueryInputSchema = z.object({
  question: z.string()
    .trim()                               // ← remove espaços antes de validar
    .min(1, "question não pode ser vazio")
    .max(1000, "question excede 1000 caracteres"),
});
```

**DON'T:**
```typescript
// Aceita "   " (só espaços) como pergunta válida
export const QueryInputSchema = z.object({
  question: z.string().min(1, "question não pode ser vazio"),
});
```

---

### R7 — Variáveis de ambiente DEVEM ser acessadas via `config.ts`

NUNCA ler `process.env.AZURE_*` diretamente no código. DEVE usar as constantes exportadas de `../../shared/config`.

**DO:**
```typescript
import { AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY } from "../../shared/config";

const client = new OpenAIClient(AZURE_OPENAI_ENDPOINT, new AzureKeyCredential(AZURE_OPENAI_KEY));
```

**DON'T:**
```typescript
// Copilot gera isso por conveniência — impossibilita testes e vaza segredos em logs
const client = new OpenAIClient(
  process.env.AZURE_OPENAI_ENDPOINT!,
  new AzureKeyCredential(process.env.AZURE_OPENAI_KEY!)
);
```

---

## Anti-padrões que o Copilot gera com frequência

| Anti-padrão | Por que o Copilot gera | Por que é problema | Regra |
|---|---|---|---|
| `as any` | Não conhece o tipo exato da resposta Azure | Bypassa o compilador; erros silenciosos em produção | R2 |
| `console.log(...)` | É a forma mais simples de debug | Não é estruturado, não tem request ID, vaza para stdout sem contexto | R3 |
| `require("...")` | Treinado em código CJS legacy | Falha em runtime com `"type": "module"` no package.json | R4 |
| `export *` | Facilita barrel file | Impede tree shaking; importações implícitas difíceis de rastrear | R5 |
| `.min(1)` sem `.trim()` | Valida comprimento sem normalizar | Aceita strings de espaços como válidas; downstream recebe input sujo | R6 |
| `process.env.X!` direto | Acesso direto é mais simples | Impossibilita mock em testes; `!` silencia erros de env não configurado | R7 |
| Função sem tipo de retorno | TypeScript infere na maioria dos casos | Em funções complexas a inferência falha ou gera `any` implícito | R1 |

---

## Critérios de maturidade desta skill

Esta skill está madura para uso pelo time quando:
1. Testada com ≥ 3 gerações de código diferentes (endpoint, service, validator)
2. Todos os anti-padrões da tabela acima foram observados pelo menos uma vez no output do Copilot — e a skill os preveniu na segunda geração
3. Aprovada em review pelo Tech Lead
4. Qualquer membro do time consegue ler a skill e saber o que o Copilot vai gerar diferente com ela vs sem ela

**Status atual:** v1.0 — testada com TASK-001/002 do query endpoint. Anti-padrões 1 (as any), 3 (console.log), 6 (min sem trim) confirmados no output v1 do Copilot. Anti-padrões 2, 4, 5, 7 ainda não confirmados empiricamente — precisam de teste em tasks de service e barrel files.
