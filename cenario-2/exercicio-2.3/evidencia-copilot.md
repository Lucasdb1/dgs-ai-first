# Exercício 2.3 — Evidência de uso do GitHub Copilot

> **Papel:** Desenvolvedor | **Cenário 2**
> **Tarefa:** Gerar o SKILL.md Foundation com o Copilot e verificar se ele próprio segue as regras

---

## Prompt usado com o Copilot

```
Com base nos padrões já observados neste projeto (tsconfig.json strict: true,
package.json type: module, logger pino em shared/logger.ts, Zod para validação),
gere o SKILL.md Foundation de typescript-conventions.

O arquivo deve:
- Ter regras PRESCRITIVAS (DEVE / NÃO DEVE), não descritivas
- Ter exemplos DO/DON'T com código TypeScript real do projeto
- Cobrir: tipos explícitos, as any, console.log, require(), export *, trim() em inputs, process.env direto
- Ser machine-readable: um agente lendo este arquivo deve mudar seu comportamento

Path destino: skills/foundation/typescript-conventions.md
```

---

## O que o Copilot acertou na v1

- Estrutura `DO`/`DON'T` com blocos de código TypeScript — correta
- Identificou `as any` e `console.log` como anti-padrões (os mais óbvios)
- Usou o contexto do `tsconfig.json` para inferir `strict: true`
- Mencionou o `pino` como logger correto

## O que o Copilot não cobriu ou cobriu mal na v1

| Gap | Descrição | Correção aplicada |
|---|---|---|
| Faltou R4 (`require()`) | Copilot não mencionou o risco de imports CJS em projeto ESM | Adicionada regra R4 com exemplo `require("@azure/functions")` |
| Faltou R5 (`export *`) | Wildcard exports não foram mencionados | Adicionada regra R5 com exemplo de barrel file ruim |
| Faltou R6 (`.trim()`) | Copilot não cobriu normalização de input | Adicionada R6 com exemplo do `QueryInputSchema` do projeto |
| Faltou R7 (`process.env` direto) | Copilot não sabia que o projeto usa `shared/config.ts` | Adicionada R7 com exemplo usando `AZURE_OPENAI_ENDPOINT` do config |
| Anti-padrões sem tabela | Copilot listou em prosa — difícil de escanear | Reformatado como tabela com coluna "por que o Copilot gera" |
| Critérios de maturidade genéricos | "Quando parecer bom" — inútil | Reescrito com critérios mensuráveis e estado atual da skill |

---

## Teste: Copilot gera código melhor com a skill presente?

O SKILL.md foi adicionado ao repositório e o Copilot foi usado para gerar `src/services/search.ts`.

### Sem skill (v1 — output bruto do Copilot)

```typescript
// v1: Copilot sem skill ativa
async function searchChunks(embedding: number[]) {
  const response = await client.search("*", { vector: { value: embedding } });
  const result = response as any;           // ← R2 violada
  console.log("chunks:", result.results);   // ← R3 violada
  return result.results;                    // ← R1 violada: sem tipo de retorno
}
```

### Com skill (v2 — `typescript-conventions.md` no repo)

```typescript
// v2: Copilot com skill ativa — arquivo completo em novatech-assistant/src/services/search.ts
export async function searchChunks(
  embedding: number[],
  topK: number = 5,
): Promise<SearchChunk[]> {                             // ← R1: tipo explícito
  log.info({ embeddingDim: embedding.length, topK },    // ← R3: pino
    "iniciando busca vetorial");

  // ...

  for await (const result of results.results) {
    if (!isAzureSearchDocument(result.document)) {      // ← R2: type guard
      log.warn({ raw: result.document },
        "documento com formato inesperado ignorado");
      continue;
    }
    chunks.push({ /* ... */ });
  }
  return chunks;
}
```

### Comparação por regra

| Regra | v1 (sem skill) | v2 (com skill) | Melhoria |
|---|---|---|---|
| R1 — tipos explícitos | `async function searchChunks(embedding)` sem retorno | `Promise<SearchChunk[]>` explícito | ✅ |
| R2 — proibido `as any` | `response as any` | type guard `isAzureSearchDocument()` | ✅ |
| R3 — logger pino | `console.log("chunks:", ...)` | `log.info({ chunkCount }, "...")` | ✅ |
| R7 — config centralizado | `process.env.AZURE_SEARCH_KEY!` direto | importado de `../shared/config` | ✅ |
| R4 — ESM imports | correto na v1 | correto | — |
| R5 — named exports | correto na v1 | correto | — |

Regras R4/R5 o Copilot já acertou na v1 (contexto ESM era claro pelo `package.json`).
As demais (R1, R2, R3, R7) só apareceram corretamente **depois** que a skill estava no repositório.
