---
name: mcp-server-configuration
description: Como mapear necessidades do time (código/specs/skills, documentação de negócio, corpus RAG, histórico git, memória) para servidores MCP locais com escopo de least privilege, e como estruturar o `.mcp/mcp.json` do novatech-assistant. Carregar ao configurar, revisar ou estender `.mcp/mcp.json`, ao adicionar um novo MCP server, ou ao preencher a seção Coding Standards do AGENTS.md com regras de segurança de agentes.
metadata:
  author: clovis-cli
  type: technical-skill
---

## O padrão

O `novatech-assistant` dá a agentes de IA (Claude, GitHub Copilot) acesso a filesystem, git e memória via MCP. O problema que este padrão resolve é overprivilege: um único server de filesystem apontando para a raiz do repositório exporia `.env`, `infra/parameters/*.bicepparam` e a documentação de negócio a `write_file` acidental. A solução adotada é **least privilege por necessidade**: cada necessidade do time vira um server (ou um escopo dedicado dentro de um server), nunca um server genérico de escopo amplo.

## Passo 1 — Mapear necessidade → server

Antes de configurar qualquer server, liste a necessidade concreta e o papel que a usa. O projeto já resolveu isso assim (`cenario-2/exercicio-2.1/mapeamento-mcp.md`):

| Necessidade | Server | Escopo configurado |
|---|---|---|
| Ler/editar código, specs, skills, ADRs, prompts, testes | `filesystem-code` | `./src ./specs ./skills ./docs/adr ./prompts ./tests` |
| Ler documentação de negócio da NovaTech | `filesystem-docs` | `./docs/novatech` — somente-leitura (política) |
| Recuperar chunks do corpus RAG | `filesystem-docs` | `./data/retrieval-corpus` — somente-leitura (política) |
| Histórico, diffs e branches do repositório | `git` | repositório raiz (`.`) |
| Persistir linguagem ubíqua e decisões entre sessões | `memory` | grafo de conhecimento local, sem acesso a filesystem |

Uma nova necessidade sempre entra nesta tabela antes de qualquer edição do `mcp.json` — se ela cabe no escopo de um server existente, reuse-o; só crie um server novo quando a necessidade exigir um tipo de acesso ou uma política diferente da dos servers já mapeados.

## Passo 2 — Por que a separação código vs. docs é o núcleo do least privilege

`filesystem-code` e `filesystem-docs` existem como dois servers, não um, porque isso é a única garantia real de que o agente não sobrescreve a fonte de verdade do domínio enquanto edita código:

- **`filesystem-code`**: inclui só os diretórios que o agente precisa *editar* durante o desenvolvimento. Exclui deliberadamente `.env`, `infra/`, `data/`, `docs/novatech/` — o agente nunca tem necessidade de escrever nesses caminhos.
- **`filesystem-docs`**: restrito a `docs/novatech/` e `data/retrieval-corpus/`, a fonte de verdade do domínio. Não inclui `src/` nem `specs/` — isso impede que o agente "resolva" uma dúvida de negócio editando código a partir da leitura de um documento, em vez de tratá-lo como leitura de referência.
- **`git`**: aponta para `.` porque histórico/diff/branch são inerentemente de repositório inteiro; não há remoto configurado nesta fase, então não há risco de push acidental.
- **`memory`**: sem acesso a filesystem — por construção, não pode vazar segredos nem sobrescrever arquivos.

Nunca configure um server de filesystem apontando para `.` (raiz) ou para qualquer diretório-pai de `docs/novatech/` — isso reintroduz o escopo amplo que a separação em dois servers existe para evitar.

## Passo 3 — Escrever o `.mcp/mcp.json`

O arquivo vive em `cenario-2/novatech-assistant/.mcp/mcp.json`. Formato adotado no projeto — chave raiz `mcpServers`; cada server tem `command`, `args` (array, paths de escopo passados como argumentos diretos ao pacote) e `description` (frase que documenta o escopo e a política de uso):

```json
{
  "mcpServers": {
    "filesystem-code": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./src",
        "./specs",
        "./skills",
        "./docs/adr",
        "./prompts",
        "./tests"
      ],
      "description": "Leitura e escrita de código-fonte, specs SDD, skills do projeto, ADRs e prompts. Escopo mínimo: exclui docs de negócio (somente-leitura) e infra."
    },
    "filesystem-docs": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./docs/novatech",
        "./data/retrieval-corpus"
      ],
      "description": "SOMENTE-LEITURA (política): documentação de negócio da NovaTech e corpus de chunks RAG. Agentes NUNCA devem escrever nestas pastas."
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."],
      "description": "Histórico, branches, diffs e status do repositório local."
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "description": "Grafo de conhecimento persistente. Armazena linguagem ubíqua do domínio NovaTech e decisões de projeto."
    }
  }
}
```

Executores: pacotes npm (`@modelcontextprotocol/server-*`) sobem via `npx -y`; ferramentas standalone distribuídas fora do npm (`mcp-server-git`) sobem via `uvx` (gerenciador de pacotes `uv`). Todos os servers deste projeto são *reference servers* locais e gratuitos — não há dependência de conta ou serviço pago/externo (Azure, Confluence, GitHub remoto) nesta fase de treinamento.

## Passo 4 — Tools expostos por server

| Server | Tools | Uso esperado |
|---|---|---|
| `filesystem-code` | `read_file`, `read_multiple_files`, `list_directory`, `search_files` (leitura); `write_file`, `create_directory`, `move_file` (escrita) | Gerar/editar código, specs, skills, ADRs |
| `filesystem-docs` | `read_file`, `list_directory`, `search_files` (todas somente-leitura por política) | Ler POL-001, PROC-042, SLA-2024, FAQ, chunks — nunca escrever |
| `git` | `git_log`, `git_diff`, `git_status`, `git_show`, `git_branch` (leitura); `git_add`, `git_commit` (escrita, restrita — ver regras abaixo) | Contexto de mudanças, blame, changelog |
| `memory` | `create_entities`, `add_observations`, `search_nodes`, `read_graph` | Registrar e recuperar linguagem ubíqua e decisões do domínio |

## Regras de segurança obrigatórias

Estas regras nascem da análise de risco do server (`cenario-2/exercicio-2.1/analise-riscos.md`) e devem estar registradas na seção **Coding Standards** do `AGENTS.md` do `novatech-assistant` — não bastam estar aqui, porque são a política que rege o uso diário dos servers já configurados:

- **Nunca** executar `git_commit` ou `git_add` via MCP sem aprovação explícita do desenvolvedor. Commits são sempre iniciados por um humano.
- **Nunca** executar `write_file` em `./docs/novatech/` ou `./data/retrieval-corpus/`. Esses diretórios são somente-leitura por política, não apenas por configuração — o `@modelcontextprotocol/server-filesystem` não impõe essa restrição nativamente (ver armadilha abaixo), então a regra escrita é a segunda camada de defesa, não a única.

## Armadilhas conhecidas

- **`@modelcontextprotocol/server-filesystem` não restringe escrita por diretório nativamente.** A separação em dois servers (`filesystem-code` vs. `filesystem-docs`) é a mitigação real — não confie apenas em uma política escrita se o agente recebe as tools de escrita do mesmo server que enxerga `docs/novatech/`.
- **Nomes de pacote e comandos evoluem.** Confirme no README oficial do repositório `modelcontextprotocol/servers` antes de ligar ou atualizar um server — não copie a versão deste documento sem revalidar.
- **Nunca aponte um escopo de filesystem para `.` (raiz) ou para qualquer pasta que contenha `.env`/`infra/`/segredos.** Liste sempre subpastas explícitas.
- **Não introduza servers pagos/externos (Azure, Confluence, GitHub remoto) quando um reference server local resolve a mesma necessidade** — este projeto não tem remoto configurado nesta fase, e o objetivo é aprendizado sem custo.

## Quando adicionar um novo server ou necessidade

Repita o Passo 1: registre a necessidade, o papel que a usa e a frequência antes de tocar no `mcp.json`. Só crie um server novo (em vez de estender o escopo de um existente) quando a necessidade exigir uma política de acesso diferente (ex.: leitura vs. escrita) da dos servers já mapeados — nunca amplie o escopo de `filesystem-code` ou `filesystem-docs` para "resolver rápido" uma necessidade que na verdade pede um terceiro server.

## Manutenção (anti-drift)

Atualize esta skill sempre que `cenario-2/exercicio-2.1/mapeamento-mcp.md` ou `analise-riscos.md` mudar, sempre que um server for adicionado/removido do `.mcp/mcp.json` real, ou sempre que os nomes/comandos dos MCP servers de referência mudarem no upstream `modelcontextprotocol/servers`.
