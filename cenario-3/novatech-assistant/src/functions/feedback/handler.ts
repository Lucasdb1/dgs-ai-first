/**
 * feedback/handler.ts — endpoint de feedback do atendente.
 *
 * Reescrito após revisão crítica do código gerado pelo Copilot (Ex. 3.2).
 * Corrige: as any, console.log, require dinâmico, attendantEmail logado.
 */

import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { CosmosClient } from "@azure/cosmos";       // import estático (corrige require dinâmico)
import { z } from "zod";
import { logger } from "../../shared/logger";
import { COSMOS_CONNECTION_STRING } from "../../shared/config";

// ─── schema Zod — substitui "as any" ─────────────────────────────────────────

const FeedbackSchema = z.object({
  queryId: z.string().min(1, "queryId é obrigatório"),
  rating: z.number().int().min(1).max(5, "rating deve ser entre 1 e 5"),
  comment: z.string().max(1000).optional(),
  attendantEmail: z.string().email("attendantEmail deve ser e-mail válido"),
});

type FeedbackInput = z.infer<typeof FeedbackSchema>;

// ─── cliente Cosmos (lazy singleton) ─────────────────────────────────────────

let _cosmosClient: CosmosClient | undefined;

function getContainer() {
  if (!_cosmosClient) {
    _cosmosClient = new CosmosClient(COSMOS_CONNECTION_STRING);
  }
  return _cosmosClient.database("novatech").container("feedbacks");
}

// ─── handler ──────────────────────────────────────────────────────────────────

export async function feedbackHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  const log = logger.child({ requestId: context.invocationId, module: "feedback-handler" });

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return { status: 400, jsonBody: { error: "Body inválido: JSON malformado" } };
  }

  const parsed = FeedbackSchema.safeParse(body);
  if (!parsed.success) {
    const firstError = parsed.error.errors[0];
    log.warn({ field: firstError.path.join("."), message: firstError.message }, "input inválido");
    return { status: 400, jsonBody: { error: firstError.message } };
  }

  const input: FeedbackInput = parsed.data;

  // Armazena apenas queryId/rating/comment — attendantEmail NÃO é logado nem persistido
  const record = {
    queryId: input.queryId,
    rating: input.rating,
    comment: input.comment ?? null,
    timestamp: new Date().toISOString(),
  };

  await getContainer().items.create(record);

  log.info({ queryId: input.queryId, rating: input.rating }, "feedback registrado");

  return { status: 201, jsonBody: { ok: true } };
}

app.http("feedback", {
  methods: ["POST"],
  handler: feedbackHandler,
});
