import { z } from "zod";

export const QueryInputSchema = z.object({
  question: z
    .string({
      required_error: "question é obrigatório",
      invalid_type_error: "question deve ser string",
    })
    .min(1, "question não pode ser vazio")
    .max(1000, "question excede 1000 caracteres"),
});

export type QueryInput = z.infer<typeof QueryInputSchema>;
