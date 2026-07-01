/**
 * search.ts — integração com Azure AI Search para recuperação de chunks RAG.
 *
 * Gerado com GitHub Copilot + skill `typescript-conventions` ativa.
 * Demonstra: R1 (tipos explícitos), R2 (type guard), R3 (pino), R4 (ESM),
 *            R5 (named exports), R7 (config centralizado).
 */

import { SearchClient, AzureKeyCredential } from "@azure/search-documents";
import { logger } from "../shared/logger";
import {
  AZURE_SEARCH_ENDPOINT,
  AZURE_SEARCH_KEY,
  AZURE_SEARCH_INDEX,
} from "../shared/config";

// ─── tipos locais ──────────────────────────────────────────────────────────────

export interface SearchChunk {
  id: string;
  text: string;
  sourceDocument: string;
  score: number;
}

interface AzureSearchDocument {
  id: string;
  text: string;
  source_document: string;
  "@search.score": number;
}

// ─── logger com contexto do módulo (R3) ───────────────────────────────────────

const log = logger.child({ module: "search-service" });

// ─── type guard em vez de "as any" (R2) ──────────────────────────────────────

function isAzureSearchDocument(value: unknown): value is AzureSearchDocument {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).id === "string" &&
    typeof (value as Record<string, unknown>).text === "string" &&
    typeof (value as Record<string, unknown>).source_document === "string"
  );
}

// ─── cliente lazy singleton ───────────────────────────────────────────────────

let _client: SearchClient<AzureSearchDocument> | undefined;

function getClient(): SearchClient<AzureSearchDocument> {
  if (!_client) {
    _client = new SearchClient<AzureSearchDocument>(
      AZURE_SEARCH_ENDPOINT,
      AZURE_SEARCH_INDEX,
      new AzureKeyCredential(AZURE_SEARCH_KEY),
    );
  }
  return _client;
}

// ─── função principal — named export (R5), tipo de retorno explícito (R1) ─────

export async function searchChunks(
  embedding: number[],
  topK: number = 5,
): Promise<SearchChunk[]> {
  log.info({ embeddingDim: embedding.length, topK }, "iniciando busca vetorial");

  const client = getClient();

  const results = await client.search("*", {
    vector: {
      value: embedding,
      kNearestNeighborsCount: topK,
      fields: ["text_vector"],
    },
    select: ["id", "text", "source_document"],
    top: topK,
  });

  const chunks: SearchChunk[] = [];

  for await (const result of results.results) {
    if (!isAzureSearchDocument(result.document)) {
      log.warn({ raw: result.document }, "documento com formato inesperado ignorado");
      continue;
    }

    chunks.push({
      id: result.document.id,
      text: result.document.text,
      sourceDocument: result.document.source_document,
      score: result.score ?? 0,
    });
  }

  log.info({ chunkCount: chunks.length }, "busca concluída");
  return chunks;
}
