# AGENTS.md — NovaTech Assistant

> Constitution do projeto. Todo agente de IA (Copilot, Claude Code) lê este arquivo antes de gerar qualquer artefato.
> As seções abaixo são preenchidas por papéis diferentes nos exercícios do Cenário 2.

## Project Overview
<!-- TODO (Tech Lead — Ex. 2.1) -->

## Tech Stack & Architecture
<!-- TODO (Tech Lead — Ex. 2.1): inclui regras de gerenciamento de contexto da ADR-0002 -->

## Coding Standards (Tech Lead)

> Preenchido pelo Tech Lead no Exercício 2.3 — Estratégia de Skills.

Todo código gerado por agentes DEVE seguir as skills Foundation antes de aplicar qualquer padrão de camada.
Carregue as skills na ordem abaixo — cada uma é pré-requisito da próxima:

1. **`skills/foundation/typescript-conventions.md`** ← **OBRIGATÓRIA para qualquer arquivo `.ts`/`.tsx`**
   - `strict: true`, `noImplicitAny: true` — todo código deve compilar sem erros nessa configuração
   - Proibido: `as any`, `console.log/error/warn`, `require()`, `export *`, `process.env.X` direto
   - Obrigatório: tipos de retorno explícitos em funções exportadas, `.trim()` antes de `.min(1)` no Zod, imports via `shared/config`

2. **`skills/foundation/error-handling.md`** ← obrigatória em qualquer função que chame Azure
   - Use `AppError`, `EmbeddingError`, `SearchError` com pino estruturado
   - Retry com exponential backoff para chamadas ao Azure OpenAI e Azure AI Search

3. **`skills/foundation/project-structure.md`** ← obrigatória ao criar novos módulos/arquivos
   - Endpoints: `src/functions/<nome>/handler.ts` + `validator.ts` + `response-builder.ts`
   - Services: `src/services/<nome>.ts`
   - Pipeline: `src/pipeline/<stage>.ts`

### Regras rápidas (sem carregar skill completa)

| Situação | Regra |
|----------|-------|
| Resposta da Azure retorna `unknown` | Use type guard (`isX(v): v is X`), nunca `as any` |
| Precisa logar | `logger.child({ module: "..." })` de `../shared/logger` |
| Precisa de variável de ambiente | Importe de `../shared/config`, nunca `process.env.X!` |
| Criando barrel file | `export { X } from "./x"` — nunca `export * from "./x"` |
| Validando input do usuário | `.trim().min(1)` no Zod — nunca só `.min(1)` |

## Product Rules & Guardrails (Product Specialist)
<!-- TODO (Product Specialist — Ex. 2.3) -->

## Testing Standards (QA)
<!-- TODO (QA — Ex. 2.1) -->

## Project Management Rules (Delivery Manager)
<!-- TODO (Delivery Manager — Ex. 2.3) -->

## Build & Deploy
<!-- TODO (Tech Lead — Ex. 2.1) -->
