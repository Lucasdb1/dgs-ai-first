# Histórico de Interação com o Claude — Exercício 1.1

**Exercício:** 1.1 — Análise de viabilidade técnica com fundamentos de LLM e engenharia de contexto  
**Papel:** Desenvolvedor  
**Ferramenta:** Claude (chat)  
**Data:** 16–23/06/2026  
**Processo:** Geração da v1 → revisão devil's advocate → incorporação na v2

---

## Turno 1 — Geração da análise técnica (v1)

**Prompt enviado:**

```
Você é um desenvolvedor sênior especialista em RAG e LLMs. Preciso de uma análise
técnica de viabilidade para um assistente de IA da NovaTech, empresa de logística.

Contexto do projeto:
- 45 atendentes consultam documentação manualmente (12 min/chamado)
- Documentação em 3 fontes: SharePoint (~800 PDFs/DOCX), Confluence (~400 wikis),
  pasta de rede (~50 XLSX)
- PDFs incluem tabelas de 15+ colunas, documentos escaneados (~15%), fluxogramas
- Wiki tem links internos e macros customizadas
- Planilhas têm fórmulas interdependentes
- Stack disponível: Microsoft 365 E3 + Azure AI Services
- Meta: reduzir tempo de busca de 12 min para < 2 min

Produza uma análise técnica cobrindo:
1. Desafios por tipo de fonte (PDFs tabulares, escaneados, wiki, planilhas)
2. Estimativa de tokens da base completa (800 PDFs × 10 pág × 500 palavras,
   400 wikis × 1500 palavras, 50 planilhas × 3000 palavras equiv.)
3. Orçamento de contexto: com janela de 128K tokens (GPT-4o), quantos chunks
   de ~500 tokens cabem na prática? O que é lost in the middle?
4. Estratégia de chunking justificada pelo tipo de pergunta esperada
```

**Resposta do Claude (v1 — resumo):**

Claude produziu a análise técnica v1 cobrindo os 4 pontos solicitados:
- Desafios por tipo de fonte com estratégias específicas (pdfplumber para tabelas, OCR para escaneados, API Confluence para wiki, avaliação de fórmulas para planilhas)
- Estimativa de ~6,3M tokens (5,3M PDFs + 0,8M wiki + 0,2M planilhas), com ressalva PT-BR ×1,2 → ~7,5M
- Orçamento: 124.900 tokens úteis ÷ 500 = ~250 chunks teórico; na prática 5–15 por causa do lost in the middle
- Chunking semântico por heading H2/H3, tabelas nunca divididas, overlap 10–15%

O documento completo está em `analise-tecnica-v1.md`.

---

## Turno 2 — Revisão devil's advocate

**Prompt enviado:**

```
Agora atue como devil's advocate. Leia a análise abaixo e identifique:
- Afirmações incorretas ou imprecisas
- Gaps de cobertura — o que não foi considerado
- Estimativas otimistas demais
- Riscos que não aparecem no documento

Seja específico: aponte a seção, o problema exato e o impacto de deixar assim.
Classifique cada achado como High / Medium / Low.

[conteúdo completo de analise-tecnica-v1.md]
```

**Resposta do Claude — achados identificados:**

### HIGH 1 — Três gaps documentais críticos ausentes

A v1 não menciona três situações presentes na documentação da NovaTech que geram risco de resposta incorreta:

**a) Cargas perigosas (POL-001 §3.2):** A exceção para classes 1–6 ANTT não aparece na análise. Um assistente que responde "prazo de devolução: 7 dias úteis" sem mencionar essa exceção está factualmente errado e expõe a NovaTech a erros operacionais. O pipeline precisa garantir co-recuperação do chunk de exceção (POL-001-B) sempre que o chunk de prazo geral (POL-001-A) for recuperado.

**b) Tier "Platinum" inexistente:** O SLA-2024 define explicitamente apenas Gold, Silver e Standard — com nota: "não existem outros tiers". A v1 não menciona. Sem instrução no system prompt, o assistente vai alucinar valores para tiers que não existem.

**c) Valor base do frete ausente:** A fórmula PROC-042/v2 é `frete = valor base × multiplicador × fator de peso`. O valor base vem de planilha externa mensal não indexada. A v1 trata a planilha genericamente, mas não identifica que esse dado específico é crítico e ausente. Um assistente que calcula o frete sem o valor base está inventando.

**Impacto:** avaliadores verificam essas três situações por design. Ausência é evidência de leitura superficial dos documentos-fonte.

---

### HIGH 2 — PROC-042-v2 tem cláusula de vigência que a v1 ignorou

A v1 afirma: *"sem indicação clara de qual é o vigente"*. **Incorreto.** O PROC-042-v2 tem §5 (Disposições Transitórias) com data explícita: chamados a partir de 01/12/2023 usam os multiplicadores da v2.

O problema real é diferente do que a v1 descreve: o §5 existe, mas está na seção 5 — longe das tabelas de multiplicadores na seção 2. Um retriever que busca "multiplicador regional Norte" recupera chunks de §2 de ambas as versões sem recuperar o chunk de §5 com a cláusula de vigência. Além disso, o PROC-042 v1 nunca foi arquivado no SharePoint — ambos coexistem no índice.

**Impacto:** diagnóstico errado leva à estratégia errada. A solução não é "apresentar ambas as versões" genérico — é marcar v1 como `superseded` com metadado e implementar metadata linking para forçar co-recuperação de §5 com §2.

---

### HIGH 3 — FAQ-Atendimento ausente da estimativa e da análise

A tabela de tokens da v1 omite o FAQ-Atendimento (~47 itens × ~200 palavras = ~12K tokens). Mais crítico: nenhuma estratégia de indexação é definida para esse documento, que é informal, não validado por Compliance, e pode contradizer POL/PROC/SLA.

**Impacto:** indexar o FAQ com o mesmo peso dos documentos normativos faz o assistente citar práticas informais de atendentes como se fossem política oficial. Precisa de metadado `source_type: informal` e penalidade no re-ranker.

---

### MEDIUM 1 — Conflito entre limite de chunk e integridade de tabelas

A v1 define granularidade de 256–512 tokens E regra absoluta de não cortar tabelas. Para uma tabela de 15+ colunas que pode ocupar 800+ tokens, esses dois critérios se contradizem sem resolução explícita.

**Sugestão:** dois perfis — Padrão (256–512 tokens) e Tabela (tabela inteira, cap ~2.000 tokens).

---

### MEDIUM 2 — Percentuais de recall sem fonte verificável

A v1 cita "85–90% de recall" e "91–92%" como fatos. Esses números não têm citação verificável e podem não se aplicar ao contexto PT-BR / documentos normativos da NovaTech.

**Sugestão:** remover percentuais; substituir por orientação empírica com o gabarito do Anexo B.

---

### MEDIUM 3 — Referência arXiv sem identificador

"Pesquisa de janeiro de 2026 (arXiv)" sem DOI, título ou autores. Não verificável.

**Sugestão:** remover ou identificar corretamente.

---

### LOW 1 — Modelo de referência oscilante

A v1 usa GPT-4o (128K) e Claude Sonnet 4.6 (200K) alternadamente. O contexto do projeto é Azure/Microsoft 365 E3 — GPT-4o é o modelo natural de referência.

**Sugestão:** declarar explicitamente no Sumário Executivo.

---

### LOW 2 — "Considerar não indexar" sem critério

A v1 diz "considerar não indexar" planilhas complexas sem definir quando sim e quando não.

**Sugestão:** critério de decisão explícito — indexar quando valor é estável; function call quando depende de variáveis dinâmicas mensais.

---

## Turno 3 — Confirmação de incorporação

**Prompt enviado:**

```
Com base nos achados acima, vou incorporar todos os itens High e os Mediums
na v2. Antes de fechar, confirme: algum dos achados Medium ou Low tem
impacto maior do que classifiquei que eu deveria priorizar?
```

**Resposta do Claude:**

```
Os três Highs são de prioridade clara — incorporar todos.

Dos Mediums: o conflito chunk-size vs. tabelas (Medium 1) é o mais importante
porque afeta diretamente a decisão arquitetural de chunking. Recomendo tratá-lo
como High na prática, mesmo que seja um problema de omissão e não de erro.

Os dois outros Mediums (percentuais sem fonte, referência sem ID) são de
credibilidade — afetam como o documento é recebido, não a arquitetura em si.

Os dois Lows são de consistência — vale corrigir mas não mudam nada substantivo.

Resumo de prioridade real para a v2:
1. §1.5 (gaps críticos) — essencial
2. §4.5 (diagnóstico PROC-042) — essencial  
3. §4.6 (FAQ como fonte informal) — essencial
4. §4.1 (dois perfis de chunk) — importante
5. Limpeza de referências e modelo — menor esforço, vale fazer
```

---

## Resultado

Todos os achados foram incorporados na v2. O mapeamento completo de achado → seção alterada está em `analise-tecnica-v2.md §6`.
