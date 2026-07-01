# Exercício 2.1 — Evidência: Agente recuperando chunk do corpus RAG

> **Tipo de evidência:** Chamadas reais ao `filesystem-docs` MCP server (JSON-RPC/stdio)
> **Pergunta simulada:** *"Qual o prazo de devolução de carga perigosa?"*
> **Gabarito Anexo B:** chunks esperados = `POL-001-A` + `POL-001-B`
> **Data:** 2026-06-30

---

## Contexto

O `filesystem-docs` server expõe `./data/retrieval-corpus/` para que o agente simule o Azure AI Search localmente. O agente lê o corpus, identifica os chunks relevantes para a pergunta e os apresenta como contexto — sem custo de API.

A pergunta *"Qual o prazo de devolução de carga perigosa?"* é o caso de teste mais crítico do domínio NovaTech: o chunk `POL-001-A` diz "7 dias úteis" (regra geral), mas o chunk `POL-001-B` diz que **carga perigosa NÃO é elegível para devolução padrão**. Um assistente que retorna apenas `POL-001-A` está alucinando por omissão.

---

## Startup do server

```
$ npx -y @modelcontextprotocol/server-filesystem ./docs/novatech ./data/retrieval-corpus

Secure MCP Filesystem Server running on stdio
```

---

## Chamada 1 — Agente lê o corpus para identificar chunks relevantes

**Request (JSON-RPC via stdio):**
```json
{
  "jsonrpc": "2.0", "id": 10, "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": { "path": "./data/retrieval-corpus/chunks-novatech.md" }
  }
}
```

**Chunks retornados (seção POL-001 — relevante para a pergunta):**
```
Chunk POL-001-A — Seção 3.1: Prazo geral
> O cliente pode solicitar a devolução de mercadorias em até 7 (sete) dias úteis após a
> data de recebimento confirmada no sistema de tracking. A contagem de dias úteis exclui
> sábados, domingos e feriados nacionais.

Chunk POL-001-B — Seção 3.2: Exceções
> As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:
> Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes
> Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1),
> gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4),
> oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
> Para essas categorias, o cliente deve entrar em contato com o setor de Gestão de Riscos
> (ramal 4500) para tratamento individual.

Chunk POL-001-C — Seção 3.3: Procedimento
> O cliente abre chamado no Portal do Cliente (portal.novatech.com.br)...
```

**Análise de cobertura (gabarito Anexo B):**

| Chunk | Presente? | Relevância para a pergunta |
|---|---|---|
| `POL-001-A` | ✅ | Regra geral (7 dias) — necessário mas insuficiente |
| `POL-001-B` | ✅ | **Crítico** — exceção de carga perigosa; sem este chunk o assistente alucina |
| `POL-001-C` | presente | Procedimento — baixa relevância para esta pergunta |

---

## Chamada 2 — Validação cruzada no documento fonte (`docs/novatech/`)

O agente faz validação cruzada lendo o documento de origem para confirmar que o chunk `POL-001-B` reflete fielmente a seção 3.2 do POL-001.

**Request:**
```json
{
  "jsonrpc": "2.0", "id": 11, "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": { "path": "./docs/novatech/POL-001-politica-devolucao.md" }
  }
}
```

**Resposta (seção 3.2 do documento fonte):**
```
3.2. Exceções ao prazo geral

As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:

- Cargas perigosas classificadas nas classes 1 a 6 da ANTT (Agência Nacional de Transportes
  Terrestres), conforme Resolução ANTT nº 5.947/2021. Inclui: explosivos (classe 1),
  gases (classe 2), líquidos inflamáveis (classe 3), sólidos inflamáveis (classe 4),
  oxidantes e peróxidos (classe 5), substâncias tóxicas e infectantes (classe 6).
- Cargas refrigeradas que tenham rompido a cadeia de frio (temperatura fora da faixa
  especificada na nota fiscal por mais de 30 minutos contínuos).
```

**Resultado da validação:** chunk `POL-001-B` é fiel ao documento fonte ✅

---

## Resposta correta do assistente (baseada nos chunks)

> *"Cargas perigosas (classes 1-6 da ANTT) não são elegíveis para devolução pelo processo padrão — a regra geral de 7 dias úteis não se aplica. Para tratamento individual, entre em contato com o setor de Gestão de Riscos (ramal 4500). Fonte: POL-001, seção 3.2."*

Se o agente retornar apenas "7 dias úteis" sem mencionar a exceção, é uma alucinação por omissão — `POL-001-B` estava disponível no corpus e foi ignorado.
