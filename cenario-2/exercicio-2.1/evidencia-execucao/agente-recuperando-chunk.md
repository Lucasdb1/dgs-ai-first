# Exercício 2.1 — Evidência: Agente recuperando chunk do corpus RAG

> **Tipo de evidência:** Chamada real ao `filesystem-docs` MCP server
> **Arquivo:** `data/retrieval-corpus/chunks-novatech.md`
> **Data:** 2026-06-30

---

## Contexto

O `filesystem-docs` server expõe `./data/retrieval-corpus/` para que o agente possa simular o comportamento do Azure AI Search durante desenvolvimento local. Em vez de requisições pagas ao Azure, o agente lê os chunks diretamente do arquivo semeado com os dados do Anexo B.

---

## Startup do server

```
$ npx -y @modelcontextprotocol/server-filesystem ./docs/novatech ./data/retrieval-corpus

Secure MCP Filesystem Server running on stdio
```

---

## Chamada — Ler corpus de chunks

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": { "path": "./data/retrieval-corpus/chunks-novatech.md" }
  }
}
```

**Resposta (trecho inicial):**
```
# Anexo B — Chunks de Referência do Pipeline de RAG

> **Nota para o participante:** Os chunks abaixo simulam o resultado do pipeline de RAG após
> processar a documentação da NovaTech (Anexo A). Eles representam os trechos que o Azure AI
> Search retornaria ao buscar por similaridade com a pergunta do atendente. Use estes chunks
> quando os exercícios pedirem simulação de respostas ou teste de prompts.

## Como usar este anexo

Quando um exercício pedir que você teste o assistente, simule o comportamento do pipeline:
1. Leia a pergunta do atendente.
2. Identifique quais chunks seriam recuperados por similaridade semântica (tipicamente os 3-5 mais relevantes).
3. Esses chunks são o contexto que o LLM recebe para gerar a resposta.

O assistente **só deveria usar informação presente nos chunks** — qualquer dado gerado além
do conteúdo dos chunks é alucinação.
```

---

## Mapa de cobertura — pergunta → chunks (Anexo B)

| Pergunta do atendente | Chunks esperados | Armadilha |
|---|---|---|
| "Qual o prazo de devolução?" | POL-001-A, POL-001-B | POL-001-B: carga perigosa NÃO pode ser devolvida |
| "Como calcular frete especial?" | PROC-042-A, PROC-042-v2-A | Duas versões com multiplicadores diferentes — devo priorizar v2 |
| "Qual o SLA do cliente Gold?" | SLA-2024-A | Confirmar: só existem Gold, Silver, Standard |
| "O que é frete especial?" | PROC-042-A ou PROC-042-v2-A, FAQ-A | FAQ pode contradizer PROC — menor prioridade |

**Relevância:** O agente usa este corpus para testes locais **gratuitos**, sem consumir tokens do Azure AI Search. Coerente com a ADR-0002 (cenário 1): context budget de ~8K para chunks.
