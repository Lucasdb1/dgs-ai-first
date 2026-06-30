# Histórico de Interação com o GitHub Copilot — Exercício 1.3

**Exercício:** 1.3 — Construção de pipeline de RAG com ferramentas open-source  
**Ferramenta:** GitHub Copilot CLI (powered by Claude Sonnet 4.6)  
**Data:** 30/06/2026  
**Evidências visuais:** pasta `prints/` (8 capturas de tela)

---

## Contexto da interação

O pipeline foi desenvolvido em iterações com o Copilot CLI. Para cada módulo,
o fluxo foi: escrever a implementação inicial → pedir revisão ao Copilot →
analisar criticamente os achados → incorporar ou rejeitar com justificativa.

---

## Módulo 1 — `ingestao.py`

### Prompt 1 — Revisão da lógica de chunking semântico

```
Revisar as funções _split_sections, _apply_overlap e build_chunks.
O objetivo é chunking semântico por heading H2/H3 com dois perfis:
standard (≤400 palavras) e table (tabela inteira, cap 1500 palavras).
Tabelas nunca devem ser cortadas. Overlap de 40 palavras entre chunks
standard consecutivos. Identificar qualquer bug ou inconsistência.
```

**Resposta do Copilot (resumo):**
- `_split_sections`: regex `(?=\n#{1,3} )` correto para split sem perder o heading
- `_apply_overlap`: lógica correta — skip no índice 0 e em chunks do tipo table
- `build_chunks`: sub-split por parágrafo para seções longas funcionando

**Achados do Copilot aceitos:**
- Confirmou que o `dict(sec)` em `_apply_overlap` é necessário para não mutar o original — comportamento que eu não havia documentado explicitamente

**Achados rejeitados:**
- Copilot sugeriu usar `re.split(r"\n## ", text)` em vez do lookahead. Rejeitado: o lookahead preserva o heading no início de cada chunk, o split simples o perde.

*Evidência visual: `prints/Evidência Copilot CLI - ingestao.py.png`*

---

### Prompt 2 — Validação da função `_table_to_prose`

```
Validar a função _table_to_prose. Ela deve converter tabelas Markdown
em prosa para melhorar a qualidade do embedding com all-MiniLM-L6-v2.
Verificar se o output tem o formato: "Métrica — Col1: Val1, Col2: Val2."
Testar mentalmente com a tabela de SLAs da NovaTech (Gold/Silver/Standard).
```

**Resposta do Copilot:**
- Confirmou formato correto: `"Tempo de resolução — Gold: Até 24h úteis, Silver: Até 48h úteis..."`
- Identificou edge case: se uma linha da tabela tiver número diferente de colunas do cabeçalho, o `continue` evita IndexError — comportamento correto já estava implementado

**Iteração:** nenhuma mudança necessária. Copilot confirmou a implementação.

*Evidência visual: `prints/Evidência Copilot CLI - ingestao respostas finais.py.png`*

---

## Módulo 2 — `busca.py`

### Prompt 3 — Revisão do re-ranking por metadados

```
Revisar a função buscar() em busca.py. Ela deve:
1. Gerar embedding da pergunta com SentenceTransformer
2. Recuperar top-20 do ChromaDB (espaço cosine: dist 0=idêntico, 2=oposto)
3. Converter distância para score: 1.0 - (dist / 2.0)
4. Aplicar penalidades: superseded -0.15, informal -0.10
5. Retornar top-8 ordenados por score ajustado

Verificar se a lógica de penalidade está correta para o caso NovaTech:
PROC-042-v1 (superseded) não deve aparecer acima de PROC-042-v2 (active)
para a mesma query de multiplicadores regionais.
```

**Resposta do Copilot:**
- Lógica de conversão correta: `1.0 - (dist / 2.0)` mapeia [0,2] → [1,0]
- Penalidades aplicadas corretamente como subtração do score ajustado
- Ordenação `reverse=True` correta para score descendente

**Achado crítico do Copilot — aceito com ressalva:**
> "A exibição em `imprimir_resultados` usa `raw["ids"][0][len(results)]` para obter o chunk_id, o que pode dar IndexError se `n_retrieve > collection.count()`. Adicionar `min(n_retrieve, collection.count())` na query resolve."

**Análise crítica:** o Copilot estava certo no diagnóstico mas a sugestão de fix era diferente da minha — ele sugeriu validar fora da query, eu já tinha adicionado `min()` dentro da chamada `collection.query()`. Mantive minha abordagem por ser mais limpa.

*Evidências visuais: `prints/Evidência - Copilot CLI - busca.py.png`, `prints/Evidência 2 - Copilot CLI - busca.py.png`, `prints/Evidência - Copilot CLI - busca resposta final.py.png`*

---

## Módulo 3 — `prompt.py`

### Prompt 4 — Revisão da mitigação lost-in-the-middle

```
Revisar montar_prompt() em prompt.py. A função deve:
1. Inverter a lista de chunks (chunk mais relevante por último — mitigação
   do efeito lost-in-the-middle, que mostra que LLMs atendem mais ao fim)
2. Adicionar labels de aviso para chunks informais e superseded
3. Montar: SYSTEM_PROMPT + blocos de documentos + pergunta

Verificar se a inversão está correta e se os labels de aviso estão
sendo aplicados apenas quando necessário.
```

**Resposta do Copilot:**
- Inversão com `list(reversed(chunks))` correta — não muta a lista original
- Labels condicionais corretos: `if chunk.source_type == "informal"` e `if chunk.status == "superseded"`

**Achado do Copilot — parcialmente aceito:**
> "O texto do aviso superseded está hardcoded com 'PROC-042' e '01/12/2023'. Se um segundo documento ficar superseded no futuro, o aviso vai citar dados errados. Recomendo tornar o aviso genérico."

**Análise crítica:** o Copilot identificou um problema real de manutenibilidade. No contexto do PoC com 5 documentos conhecidos, o aviso hardcoded é aceitável. Para produção com 1.250+ documentos, o Copilot está certo. Registrei como melhoria futura mas não alterei no PoC — a especificidade do aviso é útil para os atendentes no cenário NovaTech atual.

*Evidências visuais: `prints/Evidência - Copilot CLI - prompt.py.png`, `prints/Evidência 2 - Copilot CLI - prompt.py.png`, `prints/Evidência - Copilot CLI - prompt.py reposta final.png`*

---

## Síntese da iteração

| Módulo | Prompts | Achados Copilot | Aceitos | Rejeitados com justificativa |
|---|---|---|---|---|
| ingestao.py | 2 | 2 | 1 | 1 (regex do split) |
| busca.py | 1 | 1 | 1 (fix parcial) | — |
| prompt.py | 1 | 1 | 0 (registrado como melhoria futura) | 1 (hardcode aceitável no PoC) |

**Padrão de uso:** Copilot como revisor crítico, não como gerador. A lógica central
(`_table_to_prose`, re-ranking por metadados, inversão de chunks) foi desenvolvida
com entendimento próprio do problema — o Copilot validou e identificou edge cases,
mas não determinou as decisões arquiteturais.
