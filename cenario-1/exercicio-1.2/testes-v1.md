# Testes — System Prompt v1

**Data do teste:** 30/06/2026  
**Ferramenta:** Claude (chat — nova conversa, via Claude Code com @referência ao arquivo)  
**Setup:** System prompt v1 referenciado via `@cenario-1/exercicio-1.2/system-prompt-v1.md`, chunks A, B e C colados em seguida. Perguntas enviadas como mensagens do atendente.  
**Evidências:** `prints/Question One.png`, `prints/Question Two.png`, `prints/Question three.png`

---

## Setup completo colado no Claude

```
@cenario-1/exercicio-1.2/system-prompt-v1.md

Chunk A — POL-001, seção 3.2:
Política de Devolução POL-001, seção 3.2: Mercadorias podem ser devolvidas em até 7
dias úteis após o recebimento, exceto cargas classificadas como perigosas (classes 1
a 6 da ANTT). O cliente deve abrir chamado no portal e anexar fotos da mercadoria.

Chunk B — SLA-2024:
Tabela SLA-2024: Cliente Gold — resposta em até 2h, resolução em até 24h. Cliente
Silver — resposta em até 4h, resolução em até 48h. Cliente Standard — resposta em
até 8h, resolução em até 72h.

Chunk C — PROC-042-v2, seção 2:
PROC-042-v2, seção 2: Frete especial para cargas acima de 500kg: valor base ×
multiplicador regional. Região Sul: 1.3. Região Sudeste: 1.1. Região Norte: 1.8.
Região Nordeste: 1.5. Região Centro-Oeste: 1.4.
```

---

## Pergunta 1 — "Qual o prazo de devolução para carga perigosa?"

### Resposta obtida do Claude (v1) — ver `prints/Question One.png`

> Cargas perigosas (classes 1 a 6 da ANTT) são **exceção** à política de devolução padrão — elas **não se enquadram** no prazo de 7 dias úteis previsto para mercadorias comuns.
>
> A documentação disponível não estabelece um prazo alternativo para devolução desse tipo de carga. Recomendo escalar para o supervisor para orientação específica sobre esse caso.
>
> [Fonte: POL-001, seção 3.2]

### Análise crítica

| Critério | Resultado | Observação |
|---|---|---|
| Resposta factualmente correta? | Sim | Exceção identificada e comunicada corretamente |
| Exceção apresentada antes da regra geral? | Sim | Liderou com "não se enquadram no prazo" ✓ |
| Citou a fonte? | Sim | POL-001, seção 3.2 ✓ |
| Respeitou os guardrails? | Sim | Não inventou informação |
| Comportamento adequado para o domínio? | Sim | |

**Avaliação:** ATENÇÃO PARCIAL — A resposta liderou com a exceção e não inventou informação, mas a frase "não estabelece prazo alternativo para devolução desse tipo de carga" é ambígua. Ela implica que pode existir um processo de devolução não documentado, quando o correto é que cargas perigosas **NÃO são elegíveis para devolução** pelo processo padrão. Um atendente pode entender que talvez exista um caminho alternativo — o que é incorreto.

A resposta correta deveria afirmar diretamente: *"Cargas perigosas (classes 1–6 ANTT) não são elegíveis para devolução, conforme POL-001 seção 3.2."*

Esta ambiguidade foi identificada como melhoria para o v2: a Regra 6 ("exceções críticas têm prioridade") combinada com o novo formato ("Restrição crítica SEMPRE PRIMEIRO") produziria uma resposta v2 inequívoca: *"Cargas perigosas NÃO são elegíveis para devolução pelo processo padrão — encaminhe para o supervisor para tratamento específico. [Fonte: POL-001, seção 3.2]"*

**Gap remanescente (pipeline, não prompt):** O Chunk A do exercício não inclui a orientação de encaminhar para Gestão de Riscos (ramal 4500) — essa informação está no POL-001-B completo do Anexo B. O assistente sinaliza escalada genérica ao supervisor, mas não informa o ramal específico. Isso não é falha do prompt — é limitação do pipeline de recuperação: POL-001-B precisa ser co-recuperado com POL-001-A (ver analise-tecnica-v2.md §1.5.1).

---

## Pergunta 2 — "Meu cliente é Gold, qual o SLA de resolução?"

### Resposta obtida do Claude (v1) — ver `prints/Question Two.png`

> Clientes Gold têm resolução em até **24 horas**.
>
> Não há exceções ou condições adicionais mencionadas na documentação para esse tier.
>
> [Fonte: SLA-2024]

### Análise crítica

| Critério | Resultado | Observação |
|---|---|---|
| Resposta factualmente correta? | Sim | 24h para resolução ✓ |
| Citou a fonte? | Sim | SLA-2024 ✓ |
| Respeitou os guardrails? | Sim | |
| Comportamento adequado? | Sim | |

**Avaliação:** Correta e concisa. Sem falha.

---

## Pergunta 3 — "Quanto custa o frete para 600kg para Manaus?"

### Resposta obtida do Claude (v1) — ver `prints/Question three.png`

> A carga de 600kg enquadra no frete especial (acima de 500kg). Manaus fica na **Região Norte**, cujo multiplicador é **1.8**. Portanto, o valor final seria: **valor base × 1.8**.
>
> No entanto, **o valor base do frete não consta nos documentos disponíveis**. Sem esse dado, não é possível calcular o custo final. Recomendo escalar para o supervisor ou consultar a tabela de tarifas base na área de precificação.
>
> [Fonte: PROC-042-v2, seção 2]

### Análise crítica

| Critério | Resultado | Observação |
|---|---|---|
| Resposta factualmente correta? | Sim | Região Norte, multiplicador 1.8 ✓ |
| Alertou sobre cálculo incompleto? | Sim | "valor base não consta nos documentos" ✓ |
| Orientou o atendente sobre próximo passo? | Sim | Escalar / consultar precificação ✓ |
| Citou a fonte? | Sim | PROC-042-v2, seção 2 ✓ |
| Respeitou os guardrails? | Sim | Não inventou valor base |
| Comportamento adequado? | Sim | |

**Avaliação:** Correta. O prompt v1 já contém guardrail suficiente ("nunca invente valores") para que o modelo declare a incompletude sem fabricar um número.

**Nota sobre o teste:** A resposta no Claude Code incluiu um bloco adicional "O que esse teste revela sobre o sistema prompt" com meta-análise. Esse bloco é artefato do ambiente Claude Code (contexto expandido), não comportamento do sistema prompt em produção. O núcleo da resposta — multiplicador correto, ausência de valor base declarada, escalada sugerida — é o que importa avaliar.

---

## Resumo dos testes v1

| Pergunta | Resultado | Observação |
|---|---|---|
| Q1 — Carga perigosa | Passou | Exceção liderou a resposta; guardrails respeitados |
| Q2 — SLA Gold | Passou | Resposta correta e limpa |
| Q3 — Frete Manaus | Passou | Incompletude de cálculo declarada; valor base não inventado |

**Conclusão sobre o v1:** Os três guardrails centrais do exercício foram respeitados. O v1 já funciona corretamente para os casos de teste fornecidos.

**Decisão de iteração para o v2:** Mesmo com v1 passando nos três testes, a iteração para v2 é justificada por dois motivos:
1. **Robustez explícita:** O comportamento correto no v1 depende dos guardrails genéricos ("nunca invente"). O v2 torna explícitas as regras de prioridade de exceção e incompletude de cálculo — comportamentos que devem ser determinísticos, não emergentes.
2. **Cobertura de casos não testados:** Os três testes usam chunks que cobrem completamente o tema. Em produção, perguntas ambíguas ou com chunks parciais precisam de instrução mais robusta.
