# Exercício 2.1 — Evidência: Agente lendo histórico via MCP git server

> **Tipo de evidência:** Chamada real ao `mcp-server-git` via protocolo JSON-RPC/stdio
> **Server:** `uvx mcp-server-git` — instalado localmente via uv/uvx
> **Repositório:** `novatech-assistant/` (git local, sem remoto)
> **Data:** 2026-06-30

---

## Startup do server

```
$ uvx mcp-server-git --repository .

Downloading cryptography (4.5MiB)
Installed 33 packages in 61ms
(servidor iniciado em stdio, aguardando mensagens)
```

---

## Tools disponíveis (listagem real)

**Request:**
```json
{ "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {} }
```

**Resposta:**
```json
{
  "result": {
    "tools": [
      "git_status", "git_diff_unstaged", "git_diff_staged",
      "git_diff", "git_commit", "git_add", "git_reset",
      "git_log", "git_create_branch", "git_checkout",
      "git_show", "git_branch"
    ]
  }
}
```

**Observação:** O server expõe tools de escrita (`git_commit`, `git_add`) — isso é um risco documentado na análise de segurança.

---

## Chamada — git_log (histórico do repositório)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "git_log",
    "arguments": { "repo_path": ".", "max_count": 5 }
  }
}
```

**Resposta real do server:**
```
Commit history:
Commit: 'bbdd03aeecd7e349a2bfc93849e0552a0b766ac6'
Author: <git.Actor "Trilha AI First <trilha@db1.local>">
Date: 2026-06-09 18:13:30+00:00
Message: 'chore: starter repo (Anexo D) — estrutura + dados semeados dos Anexos A e B'
```

**Interpretação:** O agente consegue ver o histórico do repositório. Útil para que o Copilot entenda o estado atual do projeto — por exemplo, antes de implementar uma task, o agente verifica se há commits recentes no mesmo módulo.

---

## Utilidade no fluxo SDD

O acesso ao histórico via MCP git permite que o agente:
1. Verifique se uma feature branch existe antes de criar outra
2. Leia o `COMMIT_EDITMSG` do último commit para continuar de onde parou
3. Use `git_diff` para entender mudanças em andamento antes de gerar código

Isso substitui o server de GitHub (arquivado no upstream) sem depender de conta/token externos.
