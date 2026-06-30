# Exercício 2.1 — Evidência: Agente lendo documentação de negócio

> **Tipo de evidência:** Chamada real ao `filesystem-docs` MCP server via protocolo JSON-RPC/stdio
> **Server:** `@modelcontextprotocol/server-filesystem` v0.2.0
> **Data:** 2026-06-30

---

## Contexto

O server `filesystem-docs` foi iniciado com escopo restrito a `./docs/novatech` e `./data/retrieval-corpus`.
A chamada abaixo demonstra que o agente consegue listar e ler documentos dessa pasta sem acesso ao restante do repositório.

---

## Startup do server

```
$ npx -y @modelcontextprotocol/server-filesystem ./docs/novatech ./data/retrieval-corpus

Secure MCP Filesystem Server running on stdio
```

---

## Chamada 1 — Listar documentos disponíveis em `docs/novatech/`

**Request enviado (JSON-RPC via stdio):**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "list_directory",
    "arguments": { "path": "./docs/novatech" }
  }
}
```

**Resposta do server:**
```json
{
  "result": {
    "content": [{
      "type": "text",
      "text": "[FILE] FAQ-atendimento.md\n[FILE] POL-001-politica-devolucao.md\n[FILE] PROC-042-frete-especial-v1.md\n[FILE] PROC-042-v2-frete-especial-revisado.md\n[FILE] README.md\n[FILE] SLA-2024-tabela-sla-clientes.md"
    }]
  },
  "jsonrpc": "2.0",
  "id": 2
}
```

**Interpretação:** O agente enxerga os 5 documentos da NovaTech (POL-001, PROC-042 v1, PROC-042 v2, SLA-2024, FAQ-Atendimento) + README da pasta.

---

## Chamada 2 — Ler conteúdo de `SLA-2024-tabela-sla-clientes.md`

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": { "path": "./docs/novatech/SLA-2024-tabela-sla-clientes.md" }
  }
}
```

**Resposta (trecho):**
```
# SLA-2024 — Tabela de SLA por Tipo de Cliente

**Versão:** 2024.1
**Última atualização:** 02/01/2024
**Responsável:** Diretoria Comercial + Diretoria de Operações
**Classificação:** Documento contratual — os SLAs listados aqui são compromissos formais com o cliente

## 1. Classificação de clientes

A NovaTech classifica seus clientes em 3 (três) tiers com base no volume mensal de operações e no valor do contrato:

| Tier | Critério de elegibilidade | Revisão |
|------|--------------------------|---------|
| Gold | Contrato anual acima de R$ 500.000 OU mais de 200 operações/mês | Semestral |
```

**Relevância para o assistente:** Confirma que existem apenas 3 tiers (Gold, Silver, Standard) — sem "Platinum". Uma pergunta sobre SLA Platinum deve retornar "tier não existe", não valores inventados.

---

## Verificação de isolamento

O server foi iniciado **sem** acesso a `./src` ou `./specs`. Uma tentativa de leitura fora do escopo retorna erro de permissão negada — o agente não consegue ler código-fonte ou modificar arquivos através deste server.
