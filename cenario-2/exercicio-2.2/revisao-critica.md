# Exercício 2.2 — Revisão Crítica do Código Gerado com Copilot

> **Papel:** Desenvolvedor | **Cenário 2**
> **Código revisado:** `src/functions/query/handler.ts` + `validator.ts` (TASK-001 e TASK-002)
> **Avaliação:** Pré-merge, simulando Gate 3 (code review pelo Tech Lead)

---

## Contexto

O código foi gerado com o GitHub Copilot usando o `plan.md` como contexto (AGENTS.md ainda sem as seções de Coding Standards e Product Rules — Tech Lead e PS ainda não as preencheram). Os problemas abaixo são reais e teriam impacto em produção ou em etapas subsequentes do desenvolvimento.

---

## Problema 1 — `source_document: null` hardcoded no placeholder viola o contrato futuro

**Trecho:**
```typescript
return {
  status: 200,
  jsonBody: { answer: "not implemented", source_document: null },
};
```

**Por que é um problema real:**
O campo `source_document` foi definido no plan como **obrigatório e nunca nulo** (TASK-008: *"source_document NUNCA pode ser null ou undefined"*). O Copilot gerou o placeholder com `null` porque era a forma mais rápida de satisfazer a tipagem, mas isso cria um precedente perigoso: se os desenvolvedores que implementarem TASK-007 e TASK-008 copiarem este retorno como base, vão propagar o `null` sem perceber.

**Ajuste proposto:**
Substituir por um tipo temporário explícito que force o erro de compilação caso alguém esqueça de implementar:

```typescript
// Placeholder de compilação — NUNCA retorne source_document: null em produção
// TASK-007 e TASK-008 devem substituir este bloco antes do merge
return {
  status: 501,
  jsonBody: { error: "not implemented" },
} satisfies HttpResponseInit;
```

Ou, melhor ainda, criar um schema Zod de output já nesta task para que o TypeScript force a conformidade desde TASK-001:

```typescript
const QueryOutputSchema = z.object({
  answer: z.string(),
  source_document: z.string(), // nunca null — validado em runtime
});
```

---

## Problema 2 — `app.http` registra apenas `["POST"]` mas o método 405 nunca é alcançado

**Trecho:**
```typescript
app.http("queryEndpoint", {
  methods: ["POST"],
  authLevel: "function",
  handler: queryHandler,
});
```

**Por que é um problema real:**
Quando `methods: ["POST"]` é configurado no Azure Functions v4, o runtime **rejeita outros métodos antes de chamar o handler** — com comportamento padrão de runtime (geralmente 404, não 405). O check `if (req.method !== "POST")` dentro do handler nunca executa para requisições GET/PUT/DELETE: elas não chegam ao handler.

O critério de aceite da TASK-001 diz: *"GET /api/query retorna 405 Method Not Allowed"* — mas isso não acontece com esta configuração. O Copilot gerou código aparentemente correto, mas o guard interno é letra morta.

**Ajuste proposto — opção A (manter guard no handler):**
Mudar `methods` para aceitar qualquer método e mover a validação para o handler:
```typescript
app.http("queryEndpoint", {
  methods: ["GET", "POST", "PUT", "DELETE", "PATCH"],
  authLevel: "function",
  handler: queryHandler,
});
```

**Ajuste proposto — opção B (preferível — delegar ao runtime):**
Remover o guard do handler e confiar no runtime para retornar 405 automaticamente, adicionando `["GET"]` nos métodos aceitos só para disparar o 405 via runtime:
```
Registrar apenas POST. Documentar no AGENTS.md que o runtime retorna 404 (não 405)
para métodos não registrados — e alinhar o critério de aceite da TASK-001 com a realidade.
```

A decisão entre A e B deve ser tomada pelo Tech Lead e registrada como ADR.

---

## Problema 3 — Schema de validação aceita `question` com apenas espaços em branco

**Trecho:**
```typescript
.min(1, "question não pode ser vazio")
```

**Por que é um problema real:**
`z.string().min(1)` aceita `"   "` (três espaços) como válido. No domínio do assistente NovaTech, uma pergunta de espaços geraria uma chamada ao Azure OpenAI (custo real) que retornaria chunks irrelevantes ou nenhum resultado. O assistente responderia com aviso de baixa confiança para uma entrada inválida que deveria ter sido rejeitada antes.

**Ajuste proposto:**
```typescript
question: z
  .string({ ... })
  .trim()
  .min(1, "question não pode ser vazio")
  .max(1000, "question excede 1000 caracteres"),
```

O `.trim()` antes do `.min(1)` faz com que `"   "` seja normalizado para `""` e rejeitado com o erro correto. O campo `parsed.data.question` já chegará ao restante do fluxo sem espaços extras.

---

## Resumo dos ajustes

| # | Problema | Severidade | Impacto sem corrigir |
|---|---|---|---|
| 1 | `source_document: null` no placeholder | Alta | Propaga null em produção se TASK-008 copiar o padrão |
| 2 | `methods: ["POST"]` torna o guard 405 letra morta | Média | Critério de aceite da TASK-001 nunca é satisfeito na prática |
| 3 | `.min(1)` aceita strings de espaços | Baixa | Chamadas Azure desnecessárias; custo e latência reais |

---

## O que o Copilot acertou

- Estrutura Azure Functions v4 (`app.http`) correta — sem a sintaxe v3 legada
- `pino` usado em vez de `console.log` — segue o padrão do plano
- `safeParse` com retorno do primeiro erro — UX de validação adequada
- `context.invocationId` no logger child — rastreabilidade de requests
- Separação em `validator.ts` isolado — testável independentemente (TASK-009 mais fácil)
