/**
 * response-validator.ts — structured output + guardrails determinísticos.
 *
 * Gerado com GitHub Copilot + revisão via Claude.
 * Path: /src/services/response-validator.ts (Anexo C)
 */

import { z } from "zod";
import { logger } from "../shared/logger";

// ─── schema de structured output ─────────────────────────────────────────────

export const AssistantResponseSchema = z.object({
  answer: z.string().min(1, "answer não pode ser vazio"),
  source_document: z
    .string()
    .min(1, "source_document é obrigatório — resposta sem fonte não é publicada"),
  confidence_score: z
    .number()
    .min(0)
    .max(1, "confidence_score deve estar entre 0 e 1"),
}).strict(); // rejeita campos extras — v2 após code review

export type AssistantResponse = z.infer<typeof AssistantResponseSchema>;

// ─── resposta padrão segura ───────────────────────────────────────────────────

const SAFE_DEFAULT: AssistantResponse = {
  answer:
    "Não foi possível processar esta resposta com segurança. " +
    "Por favor, consulte um atendente.",
  source_document: "SISTEMA",
  confidence_score: 0,
};

// ─── logger com contexto do módulo ───────────────────────────────────────────

const log = logger.child({ module: "response-validator" });

// ─── guardrail 2: padrão de detecção ─────────────────────────────────────────
// v2 após code review: cobre variações ortográficas (acento, plural, conjugações)

const DANGEROUS_CARGO_PATTERN =
  /carga[s]?\s*perigosa[s]?|perigosa[s]?\s*carga[s]?|classe[s]?\s+[1-6]\s+da\s+antt|antt\s+classe[s]?\s+[1-6]/i;

const RETURN_PATTERN =
  /devolu[cç][aã]o|devolver|devolv[ae]|retorno\s+de\s+produto|retornar\s+produto/i;

const NEGATION_PATTERN =
  /não\s+(é\s+)?poss[ií]vel|não\s+pode[m]?|não\s+é\s+permitid[ao]|impossível|vetad[ao]|proibid[ao]|bloqueado|não\s+se\s+aplica|escalad[ao]/i;

// ─── validação principal ──────────────────────────────────────────────────────

export interface ValidationResult {
  valid: boolean;
  response: AssistantResponse;
  blockedBy?: "schema" | "guardrail_1_no_source" | "guardrail_2_dangerous_return";
}

export function validateResponse(raw: unknown): ValidationResult {
  // 1. Valida contra o schema Zod (structured output)
  const parsed = AssistantResponseSchema.safeParse(raw);

  if (!parsed.success) {
    const reason = parsed.error.errors.map((e) => e.message).join("; ");
    log.warn({ reason, raw }, "resposta rejeitada — falha no schema");
    return { valid: false, response: SAFE_DEFAULT, blockedBy: "schema" };
  }

  const response = parsed.data;

  // 2. Guardrail 1 — source_document obrigatório e não-vazio
  // (Zod min(1) já garante, mas verificação explícita reforça a intenção)
  if (!response.source_document || response.source_document.trim().length === 0) {
    log.warn({ answer: response.answer }, "guardrail 1: resposta sem source_document bloqueada");
    return { valid: false, response: SAFE_DEFAULT, blockedBy: "guardrail_1_no_source" };
  }

  // 3. Guardrail 2 — carga perigosa + devolução SEM negativa → bloqueio
  const mentionsDangerousCargo = DANGEROUS_CARGO_PATTERN.test(response.answer);
  const mentionsReturn = RETURN_PATTERN.test(response.answer);
  const containsNegation = NEGATION_PATTERN.test(response.answer);

  if (mentionsDangerousCargo && mentionsReturn && !containsNegation) {
    log.warn(
      { answer: response.answer },
      "guardrail 2: resposta sobre carga perigosa + devolução sem negativa — bloqueada",
    );
    return {
      valid: false,
      response: SAFE_DEFAULT,
      blockedBy: "guardrail_2_dangerous_return",
    };
  }

  log.info(
    {
      source_document: response.source_document,
      confidence_score: response.confidence_score,
    },
    "resposta validada com sucesso",
  );

  return { valid: true, response };
}
