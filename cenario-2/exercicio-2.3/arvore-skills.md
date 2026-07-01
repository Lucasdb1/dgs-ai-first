# Exercício 2.3 — Árvore de Skills do Projeto NovaTech Assistant

> **Papel:** Desenvolvedor | **Cenário 2**
> **Referência:** Estrutura de diretórios conforme Anexo C (`/skills/foundation/`, `/skills/domain/`, `/skills/artifact/`)

---

## Hierarquia Foundation → Domain → Artifact

```
skills/
├── foundation/                        ← convenções globais (base de todas as skills)
│   ├── typescript-conventions.md      ★ mais importante — usada por todas as outras
│   ├── error-handling.md
│   └── project-structure.md
│
├── domain/                            ← padrões por camada técnica ou de produto
│   ├── azure-functions-endpoint.md
│   ├── azure-ai-search-integration.md
│   ├── react-components.md
│   ├── testing-patterns.md            ← criada pelo QA
│   └── sdd-spec-template.md           ← criada pelo Product Specialist
│
└── artifact/                          ← receitas de geração (combinam skills de domain)
    ├── create-rag-endpoint.md
    ├── create-integration-test.md
    └── create-react-card.md
```

---

## Foundation

### `typescript-conventions` ★
**Descrição / frase-ativação:** *"Gere código TypeScript seguindo os padrões de convenção do projeto NovaTech Assistant"*
**Quem cria:** Tech Lead
**Quem consome:** Dev Pleno, Dev Sênior, QA (ao revisar código), Copilot, Claude Code
**Frequência:** Alta — toda geração de código passa por esta skill
**Razão de ser:** Contém as regras que o Copilot mais frequentemente viola: `as any`, `console.log`, imports dinâmicos, tipos implícitos. É a base que todas as outras skills pressupõem.

---

### `error-handling`
**Descrição / frase-ativação:** *"Implemente tratamento de erros seguindo os padrões do projeto NovaTech Assistant"*
**Quem cria:** Tech Lead
**Quem consome:** Dev Pleno, Dev Sênior, Copilot
**Frequência:** Alta — toda função que chama Azure deve ter retry e error handling
**Razão de ser:** O Copilot gera `try/catch` com `console.error` e erros genéricos. Esta skill define `AppError`, `EmbeddingError`, `SearchError` com pino estruturado e retry com exponential backoff.

---

### `project-structure`
**Descrição / frase-ativação:** *"Crie um novo módulo seguindo a estrutura de diretórios do NovaTech Assistant"*
**Quem cria:** Tech Lead
**Quem consome:** Dev Pleno, Dev Sênior, Copilot
**Frequência:** Média — usada quando novos módulos/endpoints são criados
**Razão de ser:** O Copilot frequentemente cria arquivos no path errado (ex: `src/query.ts` em vez de `src/functions/query/handler.ts`). Esta skill mapeia a estrutura do Anexo C.

---

## Domain

### `azure-functions-endpoint`
**Descrição / frase-ativação:** *"Crie um Azure Function HTTP endpoint seguindo o padrão do projeto"*
**Quem cria:** Dev Sênior
**Quem consome:** Dev Pleno, Dev Sênior, Copilot
**Frequência:** Alta — todos os endpoints do projeto seguem este padrão (query, feedback, health)
**Depende de:** `typescript-conventions`, `error-handling`

---

### `azure-ai-search-integration`
**Descrição / frase-ativação:** *"Integre com Azure AI Search para busca de chunks RAG"*
**Quem cria:** Dev Sênior
**Quem consome:** Dev Pleno, Copilot
**Frequência:** Média — usada nas tasks de retrieval e indexação
**Depende de:** `typescript-conventions`, `error-handling`

---

### `react-components`
**Descrição / frase-ativação:** *"Crie um componente React para o painel web do NovaTech Assistant"*
**Quem cria:** Dev Sênior
**Quem consome:** Dev Pleno, Copilot
**Frequência:** Média — painel web tem número limitado de componentes únicos
**Depende de:** `typescript-conventions`

---

### `testing-patterns` ← criada pelo QA
**Descrição / frase-ativação:** *"Escreva testes seguindo os padrões de teste do projeto NovaTech Assistant"*
**Quem cria:** **QA** — é o papel com autoridade sobre estratégia de teste
**Quem consome:** Dev Pleno, Dev Sênior, QA (ao revisar), Copilot
**Frequência:** Alta — toda task de implementação tem task de teste correspondente
**Razão de ser:** O QA define o padrão de mocks (MSW), fixtures, e o que deve e não deve ser testado. Copilot gera testes sem fixtures compartilhadas e com mocks inconsistentes.
**Depende de:** `typescript-conventions`

---

### `sdd-spec-template` ← criada pelo Product Specialist
**Descrição / frase-ativação:** *"Escreva um requirements.md seguindo o template SDD do projeto NovaTech Assistant"*
**Quem cria:** **Product Specialist** — é o papel que escreve specs de produto
**Quem consome:** Product Specialist, Tech Lead (ao revisar), Delivery Manager, Claude (chat/Cowork)
**Frequência:** Média — 5 módulos com specs a escrever; evoluções frequentes
**Razão de ser:** Padroniza outcomes, scope boundaries, verification criteria e prior decisions. Sem esta skill, PS e TL geram specs com formatos incompatíveis que não são consumíveis por agentes.
**Depende de:** (nenhuma skill técnica — é de domínio de produto)

---

## Artifact

### `create-rag-endpoint`
**Descrição / frase-ativação:** *"Crie um endpoint RAG completo seguindo o padrão do projeto NovaTech Assistant"*
**Quem cria:** Dev Sênior
**Quem consome:** Dev Pleno, Copilot
**Frequência:** Média — usado para query, feedback e futuras expansões
**Depende de:** `azure-functions-endpoint`, `azure-ai-search-integration`, `error-handling`, `typescript-conventions`
**Razão de ser:** Receita completa que combina todas as skills de domain. Copilot sem esta skill gera endpoints RAG sem context budget enforcement, sem retry, sem `source_document`.

---

### `create-integration-test`
**Descrição / frase-ativação:** *"Crie um teste de integração para um endpoint do NovaTech Assistant"*
**Quem cria:** QA (com apoio do Dev Sênior)
**Quem consome:** Dev Pleno, Dev Sênior, QA, Copilot
**Frequência:** Alta — cada endpoint tem pelo menos 3 cenários de integração
**Depende de:** `testing-patterns`, `azure-functions-endpoint`

---

### `create-react-card`
**Descrição / frase-ativação:** *"Crie um componente de card para o painel web do NovaTech Assistant"*
**Quem cria:** Dev Sênior
**Quem consome:** Dev Pleno, Copilot
**Frequência:** Baixa — número limitado de cards únicos (resposta, feedback, histórico)
**Depende de:** `react-components`, `typescript-conventions`

---

## Resumo de criação/consumo por papel

| Skill | Cria | Consome (humanos) | Consome (agentes) |
|---|---|---|---|
| `typescript-conventions` | TL | Dev, QA | Copilot, Claude Code |
| `error-handling` | TL | Dev | Copilot |
| `project-structure` | TL | Dev | Copilot |
| `azure-functions-endpoint` | Dev Sênior | Dev Pleno | Copilot |
| `azure-ai-search-integration` | Dev Sênior | Dev Pleno | Copilot |
| `react-components` | Dev Sênior | Dev Pleno | Copilot |
| `testing-patterns` | **QA** | Dev, QA | Copilot |
| `sdd-spec-template` | **PS** | PS, TL, DM | Claude (chat/Cowork) |
| `create-rag-endpoint` | Dev Sênior | Dev Pleno | Copilot |
| `create-integration-test` | QA + Dev Sênior | Dev, QA | Copilot |
| `create-react-card` | Dev Sênior | Dev Pleno | Copilot |

**Skills criadas por papel não-dev:** `testing-patterns` (QA) e `sdd-spec-template` (PS) — demonstrando que skills são um artefato de time, não só de desenvolvedores.
