# Exercício 2.1 — Análise de Riscos de Segurança (MCP local)

> **Papel:** Desenvolvedor | **Cenário 2 — Fase de Estruturação**

---

## Risco 1 — Escopo amplo no `filesystem` expõe segredos

### Descrição
Se o `filesystem-code` server for configurado com `"."` (raiz do repositório) em vez de paths específicos, o agente ganha acesso a arquivos sensíveis:
- `.env` com credenciais do Azure (AZURE_OPENAI_KEY, AZURE_SEARCH_KEY)
- `infra/parameters/dev.bicepparam` com configurações de ambiente
- Qualquer arquivo de segredo versionado acidentalmente

### Cenário de exploração
Um agente que recebe uma task de "ler o contexto do projeto" pode usar `read_file` para ler `.env` e, em seguida, incluir os valores em código gerado (ex: hardcoded em `config.ts`) ou em um log que vaza para o histórico do repositório.

### Mitigação implementada
O `filesystem-code` no `.mcp/mcp.json` lista explicitamente apenas os diretórios necessários:
```
./src ./specs ./skills ./docs/adr ./prompts ./tests
```
Isso **exclui** `.env`, `infra/`, `data/`, `.git/` e `docs/novatech/`. Um `read_file "./.env"` retorna erro de permissão negada.

### Mitigação adicional
Adicionar `.env` ao `.gitignore` (já presente no starter repo) e nunca versionar segredos. Usar Azure Key Vault em produção — não variáveis de ambiente hardcoded.

---

## Risco 2 — MCP git server com tools de escrita permite commits sem revisão

### Descrição
O `mcp-server-git` expõe as tools `git_add`, `git_commit` e `git_create_branch`. Se um agente for instruído a "implementar e commitar", ele pode criar commits sem passar pelo gate de code review definido pelo time (Gate 3: TL faz code review antes do merge).

### Cenário de exploração
O Copilot recebe uma task de implementar um endpoint. Após gerar o código, interpretando instruções ambíguas como "termine a tarefa", executa:
1. `git_add ./src/functions/query/handler.ts`
2. `git_commit` com mensagem automática

O código chega ao branch sem revisão humana, violando o Gate 3 do workflow AI First.

### Mitigação implementada
Regra explícita no AGENTS.md (seção de Coding Standards — a ser preenchida pelo Tech Lead):

> **NUNCA use `git_commit` ou `git_add` via MCP sem aprovação explícita do desenvolvedor. Commits são sempre iniciados pelo humano.**

### Mitigação adicional
Monitorar o histórico de commits (`git_log`) ao início de cada sessão para verificar se o agente criou commits não autorizados. Em caso positivo, reverter com `git reset --soft HEAD~1` antes de continuar.

---

## Risco 3 — `filesystem-docs` sem proteção nativa de escrita

### Descrição
O server `@modelcontextprotocol/server-filesystem` v0.2.0 não aplica restrição de escrita por diretório de forma nativa. Embora `filesystem-docs` tenha escopo restrito a `./docs/novatech` e `./data/retrieval-corpus`, o tool `write_file` ainda está disponível no server — um agente poderia sobrescrever documentos da NovaTech.

### Cenário de exploração
Agente interpretando "atualize o documento para refletir a resposta" tenta usar `write_file` no `filesystem-docs` para modificar `POL-001-politica-devolucao.md` — corrompendo a fonte de verdade do domínio.

### Mitigação implementada
A separação em dois servers (`filesystem-code` e `filesystem-docs`) limita o blast radius: o agente que edita código não tem acesso a `docs/novatech/`, e vice-versa. A regra de não-escrita em docs de negócio deve estar no AGENTS.md:

> **NUNCA use `write_file` em `./docs/novatech/` ou `./data/retrieval-corpus/`. Esses diretórios são somente-leitura por política.**

### Mitigação adicional
Versionar os documentos de negócio em um branch separado ou submodule. Monitorar `git_diff_unstaged` ao início de cada sessão para detectar modificações não autorizadas nesses diretórios.

---

## Resumo

| Risco | Impacto | Probabilidade | Mitigação |
|---|---|---|---|
| Escopo amplo expõe `.env` | Alto — vazamento de credenciais Azure | Baixa (se config correta) | Paths explícitos no mcp.json + `.gitignore` |
| `git_commit` sem revisão | Médio — burla Gate 3 do workflow | Média (instrução ambígua) | Regra no AGENTS.md + revisão do log |
| Escrita não intencional em docs | Alto — corrompe fonte de verdade | Baixa (erro de instrução) | Separação de servers + regra no AGENTS.md |
