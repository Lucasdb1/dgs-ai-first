# Resumo — Exercício 1.2

**Exercício:** 1.2 — Prototipação de prompt com engenharia de contexto  
**Papel:** Desenvolvedor  
**Autor:** Lucas Costa  
**Data:** 30/06/2026

---

## O que foi feito

Prototipação e teste do system prompt do assistente de atendimento da NovaTech, com foco em engenharia de contexto (mapeamento estático/dinâmico) e iteração baseada em falhas observadas nos testes.

---

## Artefatos gerados

| Arquivo | Conteúdo |
|---|---|
| `system-prompt-v1.md` | System prompt v1 + mapeamento estático/dinâmico + estimativa de tokens por componente |
| `testes-v1.md` | 3 perguntas testadas no Claude com chunks A/B/C + análise crítica de cada resposta + decisões de iteração |
| `system-prompt-v2.md` | System prompt v2 + changelog documentado (o que mudou e por quê) |
| `testes-v2.md` | Retest com v2 + comparação direta com v1 por critério |

---

## Resultado da iteração

### Falhas encontradas no v1

| Falha | Pergunta | Severidade |
|---|---|---|
| Exceção de carga perigosa apresentada depois da regra geral | Q1 — devolução de carga perigosa | Alta |
| Cálculo incompleto entregue sem alerta de incompletude | Q3 — frete Manaus 600kg | Alta |
| Incompletude de chunk não sinalizada ao atendente | Q1 | Média |

### Correções aplicadas no v2

| Regra adicionada | O que resolve |
|---|---|
| Regra 6 — Exceções críticas têm prioridade | Cargas perigosas, prazos vencidos, documentação irregular sempre aparecem antes da regra geral |
| Regra 7 — Cálculos incompletos declarados | Quando dado faltante impede o cálculo, o assistente declara e orienta onde buscar |
| Regra 8 — Incompletude sinalizada | Quando os chunks cobrem parcialmente a pergunta, o assistente sinaliza ativamente |

---

## Lição central de engenharia de contexto

A v1 tinha guardrails genéricos ("nunca invente", "cite a fonte") que funcionam para perguntas simples com cobertura total nos chunks. Ela falhou nos dois casos que exigem raciocínio sobre a estrutura da resposta — não sobre o conteúdo:

- **Q1:** Regra geral vs. exceção — o modelo sabe a exceção, mas não sabe que ela deve aparecer primeiro.
- **Q3:** Cálculo parcial — o modelo sabe a fórmula, mas não sabe que "valor base" ausente torna a resposta operacionalmente inútil.

Esses não são problemas de conhecimento — são problemas de **instrução de prioridade e formato**. A v2 resolve adicionando instruções explícitas sobre como estruturar a resposta quando há hierarquia entre regra e exceção, e quando há dado faltante para completar um cálculo.

**Implicação:** System prompts para assistentes de domínio crítico precisam codificar não apenas o que o modelo deve saber, mas como deve hierarquizar e qualificar a informação que já tem.

---

## Conexão com a análise técnica (1.1)

As falhas observadas aqui confirmam dois riscos identificados na analise-tecnica-v2.md:

- **§1.5.1 (Cargas perigosas):** A co-recuperação obrigatória de POL-001-B com POL-001-A é necessária em nível de pipeline — o system prompt sozinho não resolve a ausência do chunk de exceções. V2 sinaliza a incompletude, mas a solução estrutural está no retrieval.

- **§1.5.3 (Valor base do frete):** Confirmado que a tabela de valor base não pode ser chunk estático. A v2 orienta o atendente para o Comercial, mas a solução de produção requer function call conforme descrito no §1.5.3 da análise técnica.
