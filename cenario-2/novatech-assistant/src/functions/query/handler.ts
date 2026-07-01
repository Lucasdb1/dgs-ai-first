import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { logger } from "../../shared/logger";
import { QueryInputSchema } from "./validator";

export async function queryHandler(
  req: HttpRequest,
  context: InvocationContext
): Promise<HttpResponseInit> {
  const log = logger.child({ requestId: context.invocationId });

  if (req.method !== "POST") {
    return { status: 405, body: JSON.stringify({ error: "Method Not Allowed" }) };
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return {
      status: 400,
      jsonBody: { error: "Body inválido: JSON malformado" },
    };
  }

  const parsed = QueryInputSchema.safeParse(body);
  if (!parsed.success) {
    const firstError = parsed.error.errors[0];
    log.warn({ validationError: firstError.message }, "input inválido");
    return {
      status: 400,
      jsonBody: { error: firstError.message },
    };
  }

  const { question } = parsed.data;
  log.info({ questionLength: question.length }, "query recebida");

  // TODO: TASK-003 — gerar embedding
  // TODO: TASK-004 — buscar chunks no Azure AI Search
  // TODO: TASK-005 — enforçar context budget (ADR-0002: ~8K tokens para chunks)
  // TODO: TASK-006 — montar prompt com system prompt + chunks + pergunta
  // TODO: TASK-007 — chamar GPT-4o com retry e exponential backoff
  // TODO: TASK-008 — formatar resposta com source_document obrigatório

  return {
    status: 200,
    jsonBody: { answer: "not implemented", source_document: null },
  };
}

app.http("queryEndpoint", {
  methods: ["POST"],
  authLevel: "function",
  handler: queryHandler,
});
