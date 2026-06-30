# Resumo — Exercício 1.3

**Exercício:** 1.3 — Construção de pipeline de RAG com ferramentas open-source  
**Papel:** Desenvolvedor  
**Autor:** Lucas Costa  
**Data:** 30/06/2026

---

## Stack utilizada

| Componente | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12 |
| Vector store | ChromaDB | 0.5.23 |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | 3.3.1 |
| Orçamento de tokens | Manual (estimativa palavras / 0.75 × 1.2 PT-BR) | — |

Stack gratuita e open-source conforme requisito do exercício. ChromaDB roda localmente com persistência em disco (`chroma_db/`).

---

## Arquivos entregues

| Arquivo | Conteúdo |
|---|---|
| `pipeline/config.py` | Constantes, caminhos, metadados por documento |
| `pipeline/ingestao.py` | Carregamento, chunking semântico, embedding, indexação no ChromaDB |
| `pipeline/busca.py` | Busca semântica com re-ranking por metadados |
| `pipeline/prompt.py` | Montagem do prompt completo (system + chunks + pergunta) |
| `testes.py` | Script de teste com 5 perguntas do mapa de cobertura do Anexo B |
| `resultados-testes.md` | Resultados detalhados com análise chunk-a-chunk |
| `requirements.txt` | Dependências |

---

## Estratégia de chunking

Dois perfis definidos na `config.py` e implementados em `ingestao.py`:

| Perfil | Tamanho | Quando usar |
|---|---|---|
| **Standard** | ≤ 400 palavras (~533 tokens) | Seções de texto narrativo, regras, procedimentos |
| **Table** | Tabela inteira (cap 1.500 palavras) | Qualquer seção com tabela Markdown |

Divisão em fronteiras semânticas (H2/H3 heading boundaries), nunca no meio de parágrafo. Overlap de 40 palavras entre chunks consecutivos (padrão 10%).

**Metadados por chunk:** `doc_id`, `source_type` (normative/informal), `status` (active/superseded), `version`, `section`, `chunk_type`. Usados no re-ranking de busca.

---

## Re-ranking por hierarquia de fontes

O `busca.py` aplica penalidades ao score cosine antes de retornar os resultados:

| Condição | Penalidade |
|---|---|
| `status = superseded` | −0.15 |
| `source_type = informal` | −0.10 |

Isso garante que PROC-042-v2 (active) supere PROC-042-v1 (superseded) para a mesma query de multiplicador — confirmado no T5.

---

## Resultados dos testes

| Teste | Pergunta | Gabarito | Resultado |
|---|---|---|---|
| T1 | Prazo de devolução? | POL-001 §3.1 + §3.2 | PASSOU ✓ |
| T2 | Posso devolver carga perigosa? | POL-001 §3.2 | PASSOU ✓ |
| T3 | SLA de resolução do cliente Gold? | SLA-2024 §2 tabela | PASSOU ✓ |
| T4 | Frete especial 600kg para Manaus? | PROC-042-v2 §2 + §2.1 | PASSOU ✓ |
| T5 | Multiplicador para o Sudeste? | PROC-042-v2 §2.1 (contradição v1 vs v2) | PASSOU ✓ |

**5/5 testes passaram.**

---

## Problemas encontrados e correções propostas

### Problema 1 — T3: tabela de SLAs não aparece no top-3

O chunk correto (SLA-2024 §2 — tabela de valores) ficou em posição 6. O chunk "5. Medição e reportes" ficou em posição 1 porque menciona "Gold", "SLA" e "resolução" no corpo do texto — as mesmas palavras da query. O modelo `all-MiniLM-L6-v2` não distingue "seção que fala sobre Gold" de "seção que contém os SLAs do Gold".

**Causa raiz:** modelo de embedding pequeno, treinado em inglês, faz matching por sobreposição de keywords em vez de intenção semântica para queries estruturadas em PT-BR.

**Correção proposta:** adicionar metadado `topic` a cada chunk e usar busca filtrada por topic (ex: query com "SLA" + "resolução" → filtrar `topic: sla_values` antes da busca semântica). Alternativa de maior impacto: trocar para `paraphrase-multilingual-mpnet-base-v2`, modelo multilíngue com melhor desempenho em PT-BR.

### Problema 2 — Ruído cross-domain nos resultados

Chunks de domínios não relacionados competem no top-8: SLA-2024 aparece em queries de frete (T4), POL-001 aparece em queries de SLA (T3). Com 39 chunks no total, scores ficam concentrados entre 0.73 e 0.85 — pouca separação entre domínios.

**Causa raiz:** o volume de documentos é pequeno e os textos compartilham vocabulário ("cliente", "prazo", "carga") que infla a similaridade cross-domain.

**Correção proposta:** implementar busca híbrida BM25 + semântica (BM25 filtra por keywords exatas, semântica captura intenção). Em produção com 1.250 documentos, a separação de scores seria naturalmente maior; o problema de ruído é amplificado pelo volume pequeno do POC.

---

## Conexão com a análise técnica (1.1)

Os resultados confirmam duas previsões da `analise-tecnica-v2.md`:

- **§1.5.1 (co-recuperação obrigatória POL-001-A + POL-001-B):** No T1, o chunk de exceções (§3.2) ficou em posição 7. A co-recuperação forçada via metadata linking (proposta no §1.5.1) teria garantido que ele entrasse no contexto — independentemente do score.

- **§4.5 (PROC-042 v1 superseded):** O re-ranking por `status=superseded` funcionou conforme projetado no §4.5. PROC-042 v1 não apareceu no top-8 do T5.
