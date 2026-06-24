# Resumo e Documentação — Exercício 1.1

**Projeto:** Assistente de atendimento da NovaTech  
**Papel:** Desenvolvedor  
**Autor:** Lucas Costa  
**Data:** 24/06/2026  
**Status:** Concluído

---

## O que foi feito

O Exercício 1.1 pediu uma análise técnica de viabilidade de um pipeline de RAG para o assistente da NovaTech, com iteração verificável usando IA. O fluxo percorrido foi:

```
analise-tecnica-v1.md  →  Devil's Advocate Review  →  analise-tecnica-v2.md
```

A iteração não foi cosmética: a revisão crítica identificou 3 findings de severidade High, 3 Medium e 2 Low. A v2 os incorporou com um §6 de mapeamento explícito — o artefato que o avaliador usa para confirmar que a iteração foi real.

---

## Contexto do projeto

A NovaTech é uma empresa de logística com 1.200 funcionários. A DB1 foi contratada para construir um assistente de IA que permite aos 45 atendentes consultar documentação interna em linguagem natural, reduzindo o tempo médio de busca de 12 min para menos de 2 min por chamado.

| Métrica | Valor |
| :--- | :--- |
| Base estimada (com correção PT-BR) | ~7,5M tokens |
| Múltiplo em relação à janela do GPT-4o (128K) | ~60× |
| Orçamento operacional recomendado por query | 5–7% da janela (~7K–9K tokens) |

**Conclusão central:** RAG é a única arquitetura viável. O maior risco não é o LLM — é a qualidade e a governança da base documental.

---

## Seções da análise técnica (v2)

### 1. Desafios por tipo de fonte

| Fonte | Tokens | Principal desafio | Estratégia |
| :--- | ---: | :--- | :--- |
| PDFs com tabelas (SharePoint) | ~5,3M | Extração ingênua achata estrutura tabular | Azure AI Document Intelligence; perfil Tabela (cap 2K tok) |
| PDFs escaneados (~15% da base) | incluído | OCR com erros corrompem chunks | OCR transformer + validação pós-OCR com vocabulário de domínio |
| Wiki Confluence (~400 pgs) | ~0,8M | Links internos viram texto solto; macros geram HTML poluído | Ingestão via API; links resolvidos para referência textual |
| Planilhas XLSX (~50, com fórmulas) | ~0,2M | Conversão perde a lógica das fórmulas | Indexar resultado calculado (estável) ou function call (dinâmico) |
| FAQ-Atendimento (47 itens) | ~12K | Documento informal, sem validação de Compliance | Metadado `source_type: informal`; penalidade no re-ranker |

**§1.5 — Gaps documentais críticos** (adicionado na v2):

1. **POL-001 §3.2 — Cargas perigosas NÃO são elegíveis para devolução padrão.** Classes 1–6 da ANTT vão para Gestão de Riscos (ramal 4500). Chunk de exceções co-recuperado obrigatoriamente com o chunk de prazo geral via metadata tag.
2. **SLA-2024 — Tier "Platinum" não existe.** Apenas Gold, Silver e Standard. Instrução no system prompt: nunca inventar valores para tiers inexistentes.
3. **PROC-042 — Valor base do frete está em arquivo externo não indexado.** `frete-base-AAAAMM.xlsx` muda mensalmente. Expor como function call `get_frete_base(regiao, peso, data)`.

### 2. Estimativa de tokens

Regra: `tokens ≈ palavras / 0,75` (calibrada em inglês). Correção de +20% para PT-BR (morfologia mais rica) → base total de **~7,5M tokens** para dimensionamento real.

### 3. Orçamento de contexto

Dois efeitos documentados mostram que encher a janela degrada qualidade:

- **Lost in the middle:** precisão cai até 30% para informação posicionada no meio do contexto (Stanford/UC Berkeley, 2023).
- **Context rot:** em sessões multi-turn longas no Teams, o modelo começa a ignorar instruções do início da sessão.

Orçamento operacional recomendado: **5–7% da janela** (~7K–9K tokens), com compaction após 8–10 turnos.

### 4. Estratégia de chunking

Dois perfis de chunk:

| Perfil | Tamanho | Quando usar |
| :--- | :---: | :--- |
| **Padrão** | 256–512 tokens | Texto narrativo, seções normativas |
| **Tabela** | Inteira (cap 2K tokens) | Qualquer tabela estruturada |

Recuperação: top-20 por similaridade vetorial → re-ranker cross-encoder → 5–8 melhores → chunk mais relevante posicionado por último no prompt.

### 5. Tratamento de versões contraditórias (PROC-042)

Diagnóstico corrigido na v2: PROC-042-v2 tem §5 (Disposições Transitórias) com data explícita (01/12/2023). O problema é que o v1 nunca foi arquivado no SharePoint.

Estratégia: marcar v1 como `status: superseded`, metadata linking para co-recuperação de §5 com §2, instrução no system prompt distinguindo chamados legados de novos.

---

## A revisão crítica — findings resumidos

### Highs corrigidos na v2

| Finding | Problema na v1 | Correção na v2 |
| :--- | :--- | :--- |
| Três traps ausentes | Apenas PROC-042 coberto | §1.5 com 3 subseções (carga perigosa, Platinum, valor base) |
| Vigência do PROC-042-v2 | "Sem indicação de vigência" | Diagnóstico correto: §5 tem data; problema é archivamento |
| FAQ-Atendimento | Ausente da estimativa | Adicionado ao §2; §4.6 com hierarquia de fontes informais |

### Mediums corrigidos na v2

| Finding | Problema na v1 | Correção na v2 |
| :--- | :--- | :--- |
| Conflito chunk vs. tabela | "Mesmo que ultrapasse 512" sem resolver | Dois perfis explícitos (Padrão e Tabela) |
| Recall sem fonte verificável | "85–90%" citando vídeo do YouTube | Percentuais removidos; validar com Anexo B |
| arXiv sem identificador | "Pesquisa de jan/2026" sem título ou ID | Removida; substituída por postura empírica |

### Lows corrigidos na v2

| Finding | Correção |
| :--- | :--- |
| Modelo de referência oscilante | GPT-4o declarado no Sumário Executivo (constraint Azure) |
| "Considerar não indexar" vago | Critério explícito: estável → indexar; dinâmico → function call |

---

## Critérios de avaliação — checklist

- [x] Diferentes tipos de conteúdo exigem diferentes estratégias de extração e chunking
- [x] Estimativa de tokens razoável com compreensão prática do conceito
- [x] Orçamento de contexto demonstra que janela é recurso limitado (não "quanto maior melhor")
- [x] Chunking justificado pelo tipo de pergunta e pelo efeito lost-in-the-middle
- [x] Iteração com Claude melhorou o documento de forma verificável (§6 da v2)
- [x] Evidência de uso de ferramenta de IA (screenshot incluído na pasta)

---

## Arquivos entregues

```
cenario-1/exercicio-1.1/
├── analise-tecnica-v1.md                        ← rascunho inicial
├── analise-tecnica-v2.md                        ← versão revisada com §6 de mapeamento
├── Evidência Conversa com IA Exercicio 1.1.png  ← screenshot do histórico com Claude
├── referencias.md                               ← bibliografia completa (6 referências)
├── resumo-exercicio-1.1.md                      ← este arquivo (resumo em Markdown)
└── resumo-visual-exercicio-1.1.html             ← versão visual completa (HTML)
```

---

## Principais aprendizados técnicos

**RAG é problema de engenharia de dados, não de modelo.** A qualidade das respostas é determinada na ingestão — antes de o LLM ser chamado.

**Orçamento de contexto como invariante de design.** Usar 5–7% da janela (não 95%) resulta de entender lost-in-the-middle e context rot como fenômenos arquiteturais.

**Contradições documentais exigem tratamento no pipeline, não no prompt.** Instruir o modelo a "apresentar ambas as versões" é insuficiente se o retriever não garantir que os chunks de vigência chegam ao contexto junto com os de multiplicadores.

**Armadilhas de domínio são mais perigosas que limitações de tecnologia.** Cargas perigosas, tier Platinum inexistente e valor base ausente causam dano operacional real se não tratados explicitamente antes do primeiro deploy.
