# Exercício 2.1 — Iteração v1 → v2 do `.mcp/mcp.json`

> **Papel:** Desenvolvedor | **Cenário 2**
> **Artefato:** `.mcp/mcp.json`

---

## v1 — Config inicial (problema identificado)

A primeira versão seguiu a abordagem mais óbvia: um único server `filesystem` apontando para a raiz do projeto. Simples, funcional, mas sem least privilege.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

### Problemas identificados na v1

1. **Escopo amplo demais no `filesystem`**: `"."` dá ao agente acesso a `.env`, `infra/`, `.git/objects/` — qualquer arquivo no repositório. Um `read_file "./.env"` retornaria credenciais Azure em texto claro.

2. **Docs de negócio com escrita habilitada**: `docs/novatech/` (POL-001, PROC-042, SLA-2024, FAQ) ficam dentro do escopo de escrita. O agente poderia modificar a fonte de verdade do domínio.

3. **`data/retrieval-corpus/` misturado com código**: O corpus de chunks ficava no mesmo escopo que `src/` — o agente poderia sobrescrever chunks durante uma task de implementação.

---

## v2 — Config refinada (least privilege aplicado)

Divisão em dois servers `filesystem` com responsabilidades distintas, mais o `everything` para exploração de primitivas MCP.

```json
{
  "mcpServers": {
    "filesystem-code": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem",
               "./src", "./specs", "./skills", "./docs/adr", "./prompts", "./tests"]
    },
    "filesystem-docs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem",
               "./docs/novatech", "./data/retrieval-corpus"]
    },
    "git": { ... },
    "memory": { ... },
    "everything": { ... }
  }
}
```

### O que mudou e por quê

| Mudança | Razão |
|---|---|
| `"."` → paths explícitos em `filesystem-code` | Remove acesso a `.env`, `infra/`, `.git/` |
| Novo `filesystem-docs` separado | Isolamento físico entre fontes de negócio (leitura) e código (escrita) |
| `everything` adicionado explicitamente | Server de referência do protocolo MCP — necessário para entender primitivas antes de criar servers customizados; ausente na v1 por descuido |

### O que a v2 ainda não resolve

O `@modelcontextprotocol/server-filesystem` v0.2.0 não aplica read-only por diretório nativamente — `write_file` ainda aparece no schema do `filesystem-docs`. A separação de servers é a mitigação disponível; a restrição definitiva exigiria um server customizado ou uma versão futura do pacote. Documentado em `analise-riscos.md` (Risco 3).
