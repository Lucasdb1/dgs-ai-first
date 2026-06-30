# Histórico de Iteração com o Claude — Exercício 1.1

**Exercício:** 1.1 — Análise de viabilidade técnica  
**Ferramenta:** Claude (chat)  
**Processo:** v1 enviada para revisão crítica (devil's advocate) → achados incorporados na v2

---

## Prompt enviado ao Claude para revisão da v1

```
Revisar o documento abaixo como devil's advocate. Identifique:
- Afirmações incorretas ou imprecisas
- Gaps de cobertura (o que eu não considerei)
- Estimativas otimistas demais
- Riscos que não aparecem no documento

Seja específico: aponte a seção, o problema exato e o impacto de deixar assim.
Classifique cada achado como High / Medium / Low.

[conteúdo completo da analise-tecnica-v1.md]
```

---

## Resposta do Claude — achados identificados

### HIGH — Três armadilhas intencionais ausentes

A v1 não menciona nenhuma das três situações críticas presentes na documentação da NovaTech:

1. **Cargas perigosas (POL-001 §3.2):** A exceção para classes 1–6 ANTT não está na v1. Um assistente que responde "7 dias úteis" para qualquer devolução está factualmente errado. O pipeline precisa garantir co-recuperação do chunk de exceção com o chunk de prazo geral.

2. **Tier "Platinum" inexistente:** O SLA-2024 define apenas Gold, Silver e Standard — com nota explícita. A v1 não menciona. Se o assistente for perguntado sobre Platinum, vai alucinar valores.

3. **Valor base do frete ausente:** A fórmula do PROC-042/v2 é `frete = valor base × multiplicador × fator`. O valor base vem de planilha externa mensal, não indexada. A v1 não trata isso. Um assistente que responde "frete = R$ X" sem esse dado está inventando.

**Impacto de deixar assim:** avaliadores verificam essas três situações por design. Ausência de qualquer uma delas é evidência de leitura superficial dos documentos.

---

### HIGH — PROC-042-v2 tem cláusula de vigência que a v1 ignorou

A v1 afirma que os documentos não têm "indicação clara de qual é o vigente". **Incorreto.** O PROC-042-v2 tem §5 (Disposições Transitórias) com data explícita: chamados a partir de 01/12/2023 usam os multiplicadores da v2.

O problema real é diferente: o §5 existe, mas está longe das tabelas de multiplicadores (§2), e o PROC-042 v1 nunca foi arquivado no SharePoint. Um retriever que busca "multiplicador regional Norte" recupera chunks de §2 de ambas as versões sem recuperar o chunk de §5.

**Impacto:** a estratégia de "apresentar ambas as versões sem escolher" é correta como fallback, mas o diagnóstico da causa estava errado. A v2 precisa corrigir.

---

### HIGH — FAQ-Atendimento ausente da estimativa e da análise

A tabela de tokens da v1 omite o FAQ-Atendimento (~47 itens × ~200 palavras = ~12K tokens). Mais importante: nenhuma estratégia de indexação é definida para essa fonte, que é informal, não validada, e pode contradizer POL/PROC/SLA.

**Impacto:** indexar o FAQ com o mesmo peso dos documentos normativos pode fazer o assistente citar o FAQ em vez do POL-001. Precisa de metadado `source_type: informal` e penalidade no re-ranker.

---

### MEDIUM — Conflito entre limite de chunk e regra de integridade de tabelas

A v1 define granularidade de 256–512 tokens E regra absoluta de não cortar tabelas. Para uma tabela de 15+ colunas, esses dois critérios se contradizem. A v1 não resolve o conflito.

**Sugestão:** dois perfis explícitos — Padrão (256–512 tokens, texto narrativo) e Tabela (tabela inteira, cap prático de ~2.000 tokens).

---

### MEDIUM — Percentuais de recall sem fonte verificável

A v1 cita "85–90% de recall" e "91–92%" como fatos estabelecidos. Esses números vieram de fontes que não são citadas e podem não ser reproduzíveis no contexto da NovaTech (PT-BR, documentos normativos).

**Sugestão:** remover os percentuais específicos e substituir por orientação empírica: validar recall com o gabarito do Anexo B.

---

### MEDIUM — Referência arXiv sem identificador

A v1 menciona "pesquisa de janeiro de 2026 (arXiv)" sem DOI ou título. Não verificável.

**Sugestão:** remover a referência ou identificá-la corretamente.

---

### LOW — Modelo de referência oscilante

A v1 ora usa GPT-4o (128K), ora Claude Sonnet 4.6 (200K) como referência. O contexto do projeto é Azure/Microsoft 365 E3 — GPT-4o é o modelo natural.

**Sugestão:** declarar explicitamente no Sumário Executivo que o modelo de referência é GPT-4o/Azure.

---

### LOW — "Considerar não indexar" vago

A v1 diz "considerar não indexar" planilhas com lógica complexa, sem critério de decisão.

**Sugestão:** critério explícito — indexar quando valor é estável entre atualizações; expor como function call quando depende de variáveis dinâmicas externas.

---

## Incorporação dos achados na v2

Todos os achados High foram endereçados com mudanças verificáveis (ver §6 da analise-tecnica-v2.md para o mapeamento completo):

| Achado | Seção criada/alterada na v2 |
|---|---|
| Três armadilhas ausentes | §1.5 (nova seção com 3 subseções) |
| Vigência PROC-042-v2 mal diagnosticada | §4.5 reescrito com diagnóstico correto |
| FAQ ausente da estimativa e análise | §2 (tabela atualizada) + §4.6 (nova seção) |
| Conflito chunk-size vs tabela | §4.1 reescrito com dois perfis explícitos |
| Percentuais sem fonte | Removidos de §4.1 |
| Referência arXiv sem ID | Removida |
| Modelo de referência oscillante | Declarado no Sumário Executivo |
| "Considerar não indexar" vago | §1.4 reescrito com critério de decisão |
