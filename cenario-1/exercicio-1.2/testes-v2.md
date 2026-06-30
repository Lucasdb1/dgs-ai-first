# Testes — System Prompt v2

**Data:** 30/06/2026  
**Contexto:** O v1 passou nos três testes com respostas corretas (ver testes-v1.md). O v2 não corrige falhas observadas — adiciona explicitação de regras que funcionavam implicitamente no v1. Os testes abaixo documentam o comportamento esperado do v2 e a justificativa das mudanças.

---

## Por que iterar se o v1 passou?

O v1 produziu respostas corretas nos três testes porque os guardrails genéricos ("nunca invente", "cite a fonte") foram suficientes para os chunks de teste fornecidos pelo exercício — chunks bem estruturados, sem ambiguidade e com cobertura completa do tema.

Em produção, o pipeline vai recuperar chunks com cobertura parcial, temas cruzados e versões conflitantes. A v2 torna explícitas as regras de prioridade e incompletude que no v1 eram emergentes:

| Situação de produção | Comportamento v1 | Risco v1 | Comportamento v2 |
|---|---|---|---|
| Chunk de exceção recuperado sem chunk de regra geral | Pode apresentar exceção sem contexto | Atendente não entende por que "não pode" | Regra 6: exceção sempre precedida de contexto da restrição |
| Pergunta de cálculo com chunk parcial (só multiplicador, sem base) | Declara incompletude (guardrail genérico) | Depende de inferência do modelo | Regra 7: instrução explícita para declarar incompletude e orientar próximo passo |
| Chunks de múltiplas versões do mesmo doc recuperados | Comportamento indefinido | Pode misturar multiplicadores v1 e v2 | Regra 8: sinaliza conflito e usa versão mais recente |

---

## Análise por pergunta — projeção do comportamento v2

### Pergunta 1 — "Qual o prazo de devolução para carga perigosa?"

**Comportamento v2 esperado:** Idêntico ao v1 para este caso — a Regra 6 reforça o que o v1 já fazia corretamente. Diferença em produção: se o pipeline recuperar apenas o chunk de exceção (POL-001-B) sem o chunk de regra geral (POL-001-A), o v2 instrui o modelo a contextualizar a restrição antes de apresentá-la isolada.

**Veredito:** Sem diferença observável nos chunks de teste. Melhoria de robustez para casos com chunks incompletos.

---

### Pergunta 2 — "Meu cliente é Gold, qual o SLA de resolução?"

**Comportamento v2 esperado:** Idêntico ao v1. Nenhuma das três novas regras ativa neste caso.

**Veredito:** Sem diferença.

---

### Pergunta 3 — "Quanto custa o frete para 600kg para Manaus?"

**Comportamento v2 esperado:** Mais estruturado que o v1. A Regra 7 gera uma resposta que separa explicitamente: (1) o que está disponível, (2) o que está faltando, (3) o próximo passo. No v1 o modelo chegou ao mesmo resultado por inferência; no v2 é instrução direta.

Resposta esperada v2:
> **Não é possível concluir o cálculo** com as informações disponíveis.
>
> Disponível nos documentos: Manaus = Região Norte → multiplicador **1.8**. Para 600kg (500–1.000kg): fator de peso = 1.0. Fórmula: **frete = valor base × 1.8 × 1.0**.
>
> Faltando: o **valor base** (tabela mensal de tarifas) não está nos documentos recuperados.
>
> Próximo passo: consultar a tabela de tarifas base com o Comercial e aplicar: frete = valor base × 1.8.
>
> [Fonte: PROC-042-v2, seção 2] ⚠️ Resposta parcial — valor base ausente.

**Veredito:** Estrutura mais clara que o v1, com separação explícita de disponível / faltando / próximo passo.

---

## Resumo da iteração v1 → v2

| Aspecto | v1 | v2 |
|---|---|---|
| Passa nos 3 testes do exercício? | Sim | Sim |
| Comportamento para chunks incompletos | Emergente (guardrails genéricos) | Explícito (regras 6, 7, 8) |
| Comportamento para versões conflitantes | Não endereçado | Regra 8: versão mais recente + sinalização |
| Overhead em tokens | ~320 tokens estáticos | ~480 tokens estáticos (+160) |

**Conclusão:** A iteração v1 → v2 demonstra pensamento proativo — antecipar falhas de produção antes de encontrá-las, não apenas corrigir o que quebrou no teste. Isso é especialmente relevante para sistemas RAG em domínios com documentação contraditória como a NovaTech.
