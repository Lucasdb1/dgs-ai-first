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

O SKILL.md foi adicionado ao repositório e o Copilot foi usado para gerar um service de exemplo (`src/services/search.ts`). Comparação:

**Sem skill:** Copilot gerou `const result = response as any` e `console.log("chunks:", chunks)`

**Com skill:** Copilot gerou type guard `isSearchResult(value: unknown): value is SearchResult` e `log.info({ chunkCount }, "busca concluída")` usando o logger de `shared/logger`

Melhoria confirmada nas regras R2 (as any → type guard) e R3 (console.log → pino). Regras R4/R5/R6/R7 precisam de mais testes em tasks futuras.
