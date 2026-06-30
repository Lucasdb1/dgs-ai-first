# Exercício 2.1 — Mapeamento de Necessidades MCP

> **Papel:** Desenvolvedor | **Cenário 2 — Fase de Estruturação**
> **Repositório:** `novatech-assistant` (local, sem remoto)

---

## 1. Necessidades do projeto

| # | Necessidade | Quem usa | Frequência |
|---|---|---|---|
| N1 | Ler e editar código-fonte, specs SDD, skills e ADRs | Dev, TL, QA (via agente) | Alta — toda geração de código |
| N2 | Ler documentação de negócio da NovaTech (`docs/novatech/`) | Dev, PS, QA (via agente) | Alta — toda resposta do assistente usa esses docs como fonte |
| N3 | Recuperar chunks do corpus RAG (`data/retrieval-corpus/`) | Dev, TL (via agente) | Média — testes de retrieval e validação de prompts |
| N4 | Ler histórico, branches e diffs do repositório | Dev, TL (via agente) | Média — context de mudanças, changelog, blame |
| N5 | Persistir linguagem ubíqua e decisões entre sessões | Todo o time (via agente) | Baixa — atualização quando novos termos ou decisões surgem |

---

## 2. Mapeamento Necessidade → MCP Server

| Necessidade | Server | Tipo | Escopo configurado |
|---|---|---|---|
| N1 — Código/specs/skills | `filesystem-code` | filesystem (local) | `./src` `./specs` `./skills` `./docs/adr` `./prompts` `./tests` |
| N2 — Docs de negócio | `filesystem-docs` | filesystem (local) | `./docs/novatech` — somente-leitura (política) |
| N3 — Corpus de chunks | `filesystem-docs` | filesystem (local) | `./data/retrieval-corpus` — somente-leitura (política) |
| N4 — Histórico git | `git` | mcp-server-git (local) | repositório raiz (`.`) |
| N5 — Memória persistente | `memory` | knowledge graph (local) | grafo local em memória |

**Nota de design:** N2 e N3 compartilham o server `filesystem-docs` porque ambas são fontes read-only da verdade do domínio. Mantê-las em um server separado do código (N1) é a principal garantia de least privilege: o agente nunca pode sobrescrever a documentação de negócio enquanto edita código.

---

## 3. Tools e Resources expostos por server

### `filesystem-code`
| Tool | Tipo (hint) | Uso esperado |
|---|---|---|
| `read_file` | readOnly | Ler handlers, specs, skills |
| `read_multiple_files` | readOnly | Ler vários arquivos de contexto |
| `write_file` | escrita | Gerar/editar código e specs |
| `create_directory` | escrita | Criar pastas de módulo |
| `list_directory` | readOnly | Navegar na estrutura do projeto |
| `search_files` | readOnly | Buscar padrão em código |
| `move_file` | escrita | Renomear/mover arquivo |

### `filesystem-docs`
| Tool | Tipo (hint) | Uso esperado | Política |
|---|---|---|---|
| `read_file` | readOnly | Ler POL-001, PROC-042, SLA-2024, FAQ, chunks | **Apenas leitura** |
| `list_directory` | readOnly | Listar documentos disponíveis | **Apenas leitura** |
| `search_files` | readOnly | Buscar termo no corpus | **Apenas leitura** |

> **Limitação conhecida:** O `@modelcontextprotocol/server-filesystem` não aplica restrição de escrita por diretório nativamente. A separação em dois servers é a mitigação: o agente que recebe tools do `filesystem-docs` não recebe `write_file` se o escopo estiver configurado corretamente. A política "nunca escreva em docs/novatech" deve estar também no AGENTS.md (seção a ser preenchida pelo Tech Lead).

### `git`
| Tool | Uso |
|---|---|
| `git_log` | Ver histórico de commits |
| `git_diff` | Ver diferenças entre branches/commits |
| `git_status` | Estado atual do working tree |
| `git_show` | Detalhes de um commit específico |
| `git_branch` | Listar branches locais |

### `memory`
| Tool | Uso |
|---|---|
| `create_entities` | Registrar termos do domínio (ex: "cliente Gold", "carga perigosa") |
| `add_observations` | Adicionar contexto a entidades existentes |
| `search_nodes` | Recuperar definições e decisões persistidas |
| `read_graph` | Visualizar toda a base de conhecimento acumulada |

---

## 4. Justificativa de least privilege por server

| Server | Por que este escopo é o mínimo suficiente |
|---|---|
| `filesystem-code` | Inclui apenas diretórios que o agente precisa editar durante o desenvolvimento. Exclui `.env`, `infra/`, `data/`, `docs/novatech/` — o agente não tem necessidade de escrever nesses caminhos. |
| `filesystem-docs` | Restrito a `docs/novatech/` e `data/retrieval-corpus/` — a fonte de verdade do domínio. Não inclui `src/` ou `specs/`, impedindo que o agente "resolva" dúvidas editando o código a partir de uma leitura de documento. |
| `git` | Aponta para `.` (repositório local). Não tem acesso a remoto (não há remoto configurado nesta fase). As tools de escrita (`git_commit`, `git_add`) estão disponíveis, mas devem ser usadas com supervisão humana — mitigação documentada em `analise-riscos.md`. |
| `memory` | Escopo natural do server: grafo em memória. Sem acesso ao filesystem — não pode vazar segredos. |

---

## 5. Quem consome cada server

| Server | Dev (agente) | TL (agente) | QA (agente) | PS (agente) | DM |
|---|---|---|---|---|---|
| `filesystem-code` | ✅ escreve código e tasks | ✅ escreve AGENTS.md e skills | ✅ lê specs para escrever testes | ✅ lê specs para validar requirements | — |
| `filesystem-docs` | ✅ referência de domínio | ✅ referência de domínio | ✅ dados de teste | ✅ fonte para guardrails | — |
| `git` | ✅ contexto de diff | ✅ contexto de branch/histórico | ✅ blame de mudanças | — | — |
| `memory` | ✅ consulta linguagem ubíqua | ✅ persiste decisões | ✅ recupera definições de domínio | ✅ persiste bounded contexts | — |
