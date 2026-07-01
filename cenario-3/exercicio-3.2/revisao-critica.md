# Exercício 3.2 — Revisão Crítica de Código Gerado por IA

> **Papel:** Desenvolvedor | **Cenário 3**
> **Tópico:** Revisão Crítica de Outputs de IA
> **Código revisado:** `feedback-handler.ts` gerado pelo Copilot
> **Código corrigido:** `novatech-assistant/src/functions/feedback/handler.ts`
> **AGENTS.md:** construído no Cenário 2 pelo time — fonte de verdade das regras de código

---

## Código original (gerado pelo Copilot)

```typescript
// feedback-handler.ts — gerado pelo Copilot
import { app, HttpRequest, HttpResponseInit } from '@azure/functions';

export async function feedbackHandler(
  request: HttpRequest
): Promise<HttpResponseInit> {
  const body = await request.json() as any;

  const feedback = {
    queryId: body.queryId,
    rating: body.rating,
    comment: body.comment,
    attendantEmail: body.attendantEmail,
    timestamp: new Date().toISOString()
  };

  console.log('Feedback recebido:', JSON.stringify(feedback));

  const { CosmosClient } = require('@azure/cosmos');
  const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
  const database = client.database('novatech');
  const container = database.container('feedbacks');

  await container.items.create(feedback);

  return { status: 200, body: 'OK' };
}

app.http('feedback', {
  methods: ['POST'],
  handler: feedbackHandler
});
```

---

## Minha revisão (ANTES do Claude)

### Problema 1 — `as any` sem validação Zod
**Tipo:** Violação do AGENTS.md (proibido `as any`)
**Linha:** `const body = await request.json() as any;`
**Por que é problema:** Bypassa o sistema de tipos. Qualquer campo de qualquer tipo passa. Um request com `rating: "cinco"` ou `queryId: null` não gera erro de validação — vai direto para o Cosmos com tipos errados. AGENTS.md define: "Zod para validação de input. Nunca `as any`."

### Problema 2 — `console.log` em vez de pino
**Tipo:** Violação do AGENTS.md (proibido `console.log`)
**Linha:** `console.log('Feedback recebido:', JSON.stringify(feedback));`
**Por que é problema:** Não é estruturado, não carrega `requestId`, não tem nível configurável. Em produção vaza para stdout sem contexto de rastreabilidade.

### Problema 3 — `require` dinâmico dentro da função
**Tipo:** Violação do AGENTS.md (proibido `require`, imports devem ser estáticos)
**Linha:** `const { CosmosClient } = require('@azure/cosmos');`
**Por que é problema:** Projeto usa `"type": "module"` — `require` falha em runtime com ESM. Além disso, executa o `require` em cada invocação da função (toda chamada de request recria o cliente), o que é ineficiente.

### Problema 4 — `attendantEmail` logado (dado pessoal — PII)
**Tipo:** Problema de segurança
**Linha:** `console.log('Feedback recebido:', JSON.stringify(feedback));` — onde `feedback` contém `attendantEmail`
**Por que é problema:** AGENTS.md define explicitamente: "Nunca logar dados pessoais (e-mail, nome)." E-mail do atendente é PII. Vai para logs, que podem ser acessados por mais pessoas do que o necessário e retidos por tempo indefinido.

> **Nota:** O `attendantEmail` também é **persistido no Cosmos** (`container.items.create(feedback)`), o que levanta questão adicional sobre necessidade de armazenar PII. Na reescrita, removi do objeto persistido — apenas `queryId`, `rating`, `comment` e `timestamp` são salvos.

---

## Revisão do Claude

O Claude identificou os mesmos 4 problemas com descrições equivalentes. Divergências:

| Ponto | Minha revisão | Claude |
|---|---|---|
| `as any` | Mencionei impacto nos tipos e Cosmos | Claude também mencionou risco de injection se `body.queryId` vier como objeto |
| `require` | Mencionei falha de runtime ESM + ineficiência | Claude focou apenas na falha ESM, não mencionou re-criação do cliente |
| `attendantEmail` | Identifiquei também a persistência no Cosmos como problema | Claude só mencionou o log |
| `process.env` direto | Não identifiquei como violação (focado nos 4 principais) | Claude adicionou: `process.env.COSMOS_CONNECTION_STRING` direto viola R7 — deveria usar `shared/config` |

**Conclusão da comparação:** Os 4 problemas obrigatórios foram identificados na revisão própria antes do Claude. O Claude adicionou 1 problema válido (`process.env` direto) que eu não priorizei por estar focado nas violações mais críticas. Ambas as revisões são complementares.

---

## Código reescrito

Arquivo: `novatech-assistant/src/functions/feedback/handler.ts`

Correções aplicadas:
- ✅ `as any` → `FeedbackSchema.safeParse(body)` com Zod
- ✅ `console.log` → `logger.child({ requestId, module })` com pino
- ✅ `require('@azure/cosmos')` → `import { CosmosClient }` estático no topo + lazy singleton
- ✅ `attendantEmail` removido dos logs E do objeto persistido no Cosmos
- ✅ `process.env.COSMOS_CONNECTION_STRING` → `COSMOS_CONNECTION_STRING` de `shared/config`
- ✅ Status 200 → 201 (Created) para POST que persiste recurso
