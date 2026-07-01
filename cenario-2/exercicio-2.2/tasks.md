# tasks.md — Query Endpoint

> **Gerado por:** Claude (chat) a partir do `plan.md` fornecido pelo Tech Lead
> **Papel:** Desenvolvedor | **Cenário 2**
> **Módulo:** `query-endpoint` | **Path no repo:** `specs/query-endpoint/tasks.md`
> **Aprovação pendente:** Tech Lead (Gate 2 — tasks → implementação)

---

## Conexão com o cenário 1

O protótipo open-source construído no Exercício 1.3 (ChromaDB + sentence-transformers) **validou a abordagem RAG** e identificou dois problemas que influenciam estas tasks:

1. **Chunking de tabelas** gera embeddings ruins (ADR-0004) — as tasks de retrieval precisam tratar chunks de tabela com cuidado, aplicando o estratégia de chunking híbrido definida no protótipo.
2. **Context budget** testado empiricamente no protótipo: 5 chunks de ~1.500 tokens cabem em ~8K (ADR-0002). A TASK-005 existe justamente para garantir esse limite em produção — o protótipo não tinha esse enforcement.

Agora o código é de **produção**: Azure AI Search + Azure OpenAI, TypeScript strict, sem workarounds de protótipo.

---

## Tasks

### TASK-001 — Setup do Azure Function HTTP trigger

**Descrição:** Criar o handler Azure Function v4 para POST /api/query. Nesta task, o endpoint apenas recebe a requisição, valida o método HTTP, e retorna placeholder. Sem lógica de negócio.

**Critérios de aceite:**
- `POST /api/query` com body válido retorna `200` com `{ answer: "not implemented", source_document: null }`
- `GET /api/query` retorna `405 Method Not Allowed`
- Função registrada corretamente com `app.http("queryEndpoint", ...)` (Azure Functions v4 API)
- Zero `console.log` — logger pino importado de `../../shared/logger`
- Arquivo em `src/functions/query/handler.ts` (conforme Anexo C)

**Dependências:** nenhuma
**Estimativa:** P

---

### TASK-002 — Validação de input com Zod

**Descrição:** Criar o schema Zod para validar o body da requisição. Extrair para `validator.ts` separado para que possa ser testado de forma isolada.

**Critérios de aceite:**
- `POST` sem campo `question` retorna `400` com `{ error: "question é obrigatório" }`
- `POST` com `question: ""` (string vazia) retorna `400` com `{ error: "question não pode ser vazio" }`
- `POST` com `question: 123` retorna `400` com `{ error: "question deve ser string" }`
- `POST` com `question: "..."` com mais de 1.000 caracteres retorna `400` com `{ error: "question excede 1000 caracteres" }`
- Schema exportado como `QueryInputSchema` (Zod) e tipo derivado `QueryInput`
- Arquivo em `src/functions/query/validator.ts`

**Dependências:** TASK-001
**Estimativa:** P

---

### TASK-003 — Cliente de embeddings (Azure OpenAI)

**Descrição:** Implementar `services/completion.ts` para gerar embedding da pergunta via Azure OpenAI (`text-embedding-ada-002`). Incluir retry com exponential backoff para erros 429 e 500.

**Critérios de aceite:**
- Retorna vetor de 1536 dimensões para qualquer string de entrada
- Executa no máximo 3 tentativas com backoff de 1s, 2s, 4s
- Em caso de falha após 3 tentativas, lança `EmbeddingError` (custom error de `shared/errors.ts`)
- Latência de cada tentativa logada via pino com nível `info`
- Sem credenciais hardcoded — lê de `config.ts` (`AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`)

**Dependências:** TASK-002
**Estimativa:** M

---

### TASK-004 — Consulta ao Azure AI Search (top-5 chunks)

**Descrição:** Implementar `services/search.ts` para buscar os 5 chunks mais relevantes dado um embedding. Cada chunk retornado deve ter `text`, `source_document`, `section` e `score`.

**Critérios de aceite:**
- Retorna array de até 5 chunks ordenados por score descendente
- Quando Azure AI Search retorna 0 resultados, retorna array vazio (sem lançar erro)
- Cada chunk tem `source_document` não-nulo (ex: `"POL-001"`, `"PROC-042-v2"`)
- Retry com exponential backoff igual ao TASK-003
- Sem credenciais hardcoded

**Dependências:** TASK-003
**Estimativa:** M

---

### TASK-005 — Enforcement de context budget (ADR-0002)

**Descrição:** Implementar função em `services/prompt-builder.ts` que filtra os chunks retornados pela TASK-004 para respeitar o budget de ~8K tokens (~6.000 palavras) definido na ADR-0002. Chunks excedentes são descartados, não truncados.

**Critérios de aceite:**
- Nunca passa mais de ~8.000 tokens em chunks para a TASK-006
- Se os 5 chunks cabem no budget, todos são incluídos
- Se algum chunk estoura o budget, ele é descartado e os anteriores são mantidos
- Budget utilizado e número de chunks logados via pino (`debug`)
- Não altera o conteúdo dos chunks (zero truncamento de texto)

**Dependências:** TASK-004
**Estimativa:** M

---

### TASK-006 — Montagem do prompt

**Descrição:** Completar `services/prompt-builder.ts` com a função que monta o prompt final: system prompt (de `/prompts/system-prompt.md`) + chunks (do TASK-005) + pergunta. Quando dois chunks de versões conflitantes de PROC-042 estiverem presentes, aplicar a instrução de priorização de versão (ADR-0003).

**Critérios de aceite:**
- System prompt lido de `/prompts/system-prompt.md` (não hardcoded)
- Prompt montado na ordem: system → chunks → pergunta
- Se chunks incluem PROC-042-v1 e PROC-042-v2 simultaneamente, instrução de priorização inserida no prompt: `"Existem duas versões de PROC-042. Priorize PROC-042-v2 (mais recente)."`
- Total de tokens estimado logado via pino antes de enviar

**Dependências:** TASK-005
**Estimativa:** P

---

### TASK-007 — Chamada ao GPT-4o com retry

**Descrição:** Implementar `services/completion.ts` para enviar o prompt montado ao GPT-4o via Azure OpenAI e retornar a resposta. Incluir retry com exponential backoff e timeout de 30s.

**Critérios de aceite:**
- Retorna `{ answer: string, source_document: string }` — `source_document` NUNCA pode ser `null` ou `undefined`
- Timeout de 30s por tentativa; após 3 falhas, lança `CompletionError`
- Temperatura 0 (respostas determinísticas para facilitar testes)
- Latência total logada via pino

**Dependências:** TASK-006
**Estimativa:** M

---

### TASK-008 — Response builder

**Descrição:** Implementar `src/functions/query/response-builder.ts` que formata a resposta do endpoint. Garantir que `source_document` sempre está presente, mesmo em casos de baixa confiança.

**Critérios de aceite:**
- `source_document` nunca ausente na resposta JSON
- Quando confiança baixa: adiciona campo `confidence_low: true` e prefixo na resposta
- Schema de saída validado com Zod antes de retornar (sem retornar resposta malformada)
- Arquivo em `src/functions/query/response-builder.ts`

**Dependências:** TASK-007
**Estimativa:** P

---

### TASK-009 — Testes unitários (validator + response-builder)

**Descrição:** Escrever testes com Vitest para `validator.ts` e `response-builder.ts`. Esses são os componentes sem dependências externas — testáveis isoladamente sem mocks.

**Critérios de aceite:**
- Todos os cenários do critério de aceite de TASK-002 cobertos por testes
- Teste verifica que `source_document` nunca ausente no response-builder
- Testes em `tests/unit/query/validator.test.ts` e `tests/unit/query/response-builder.test.ts`
- `npm test` passa com 100% dos testes do módulo query

**Dependências:** TASK-002, TASK-008
**Estimativa:** M

---

### TASK-010 — Teste de integração do endpoint

**Descrição:** Escrever teste de integração que exercita o fluxo completo `POST /api/query` com mocks MSW para Azure OpenAI e Azure AI Search.

**Critérios de aceite:**
- `POST /api/query` com `question: "Qual o SLA Gold?"` retorna `200` com `source_document: "SLA-2024"`
- `POST /api/query` com body vazio retorna `400` sem chamar Azure
- `POST /api/query` com Azure AI Search retornando 0 chunks retorna `200` com aviso de baixa confiança
- Teste em `tests/integration/query/handler.integration.test.ts`

**Dependências:** TASK-009
**Estimativa:** G

---

## Sumário

| ID | Descrição | Estimativa | Deps |
|---|---|---|---|
| TASK-001 | Setup HTTP trigger | P | — |
| TASK-002 | Validação Zod | P | 001 |
| TASK-003 | Cliente embeddings | M | 002 |
| TASK-004 | Azure AI Search query | M | 003 |
| TASK-005 | Context budget enforcement | M | 004 |
| TASK-006 | Montagem do prompt | P | 005 |
| TASK-007 | GPT-4o completion + retry | M | 006 |
| TASK-008 | Response builder | P | 007 |
| TASK-009 | Testes unitários | M | 002, 008 |
| TASK-010 | Teste de integração | G | 009 |

**Caminho crítico:** 001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010
