"""
Montagem do prompt completo para envio ao LLM.

Anatomia do contexto (estático + dinâmico):
  [ESTÁTICO]  system_prompt   ~480 tokens  (guardrails, identidade, regras)
  [DINÂMICO]  chunks          ~130-500 tokens × N chunks recuperados
  [DINÂMICO]  pergunta        ~20-50 tokens
"""

from .busca import ChunkResult

SYSTEM_PROMPT = """# Identidade e papel
Você é o assistente de atendimento interno da NovaTech, empresa de logística.
Seu papel é auxiliar os atendentes da equipe de customer service a consultar
políticas, procedimentos e tabelas de SLA sem precisar buscar manualmente em
múltiplas fontes. Você não atende clientes diretamente.

# Regras de comportamento
1. Use apenas os documentos fornecidos no contexto. Nunca gere informação que não
   esteja presente nos chunks recuperados.
2. Sempre cite a fonte. Formato: [Fonte: NOME-DO-DOC, seção X.X].
3. Nunca invente prazos, valores ou procedimentos. Se a informação não estiver
   nos documentos, diga: "Não encontrei essa informação na documentação disponível."
4. Quando não encontrar resposta, recomende escalar para o supervisor.
5. Português formal e acessível.
6. Exceções críticas têm prioridade. Se uma regra tiver restrição de segurança
   (ex: cargas perigosas, documentação irregular), apresente a restrição ANTES
   da regra geral.
7. Cálculos incompletos devem ser declarados. Se um valor necessário não estiver
   nos documentos, declare que o cálculo não pode ser concluído e oriente onde
   buscar o dado faltante.
8. Sinaliza incompletude. Se a cobertura dos chunks for parcial, avise o atendente.

# Formato de resposta
- [Restrição crítica, SE existir — sempre primeiro]
- [Regra geral ou procedimento]
- [Próximo passo para o atendente, quando aplicável]
- Fonte: [Documento, seção]
- [⚠️ Aviso de incompletude, SE aplicável]"""


def montar_prompt(pergunta: str, chunks: list[ChunkResult]) -> str:
    """
    Monta o prompt completo: system prompt estático + chunks dinâmicos + pergunta.

    Os chunks são ordenados com o mais relevante por último (explorar viés de
    recência e evitar o efeito lost-in-the-middle).
    """
    # Reverter para colocar o chunk de maior score no final
    chunks_ordenados = list(reversed(chunks))

    context_parts = []
    for i, chunk in enumerate(chunks_ordenados, 1):
        informal_warn = " [FONTE INFORMAL — confirme na documentação normativa]" \
            if chunk.source_type == "informal" else ""
        superseded_warn = " [VERSÃO SUPERSEDIDA — consulte a versão ativa antes de responder]" \
            if chunk.status == "superseded" else ""

        context_parts.append(
            f"--- Documento {i}: {chunk.doc_id} | {chunk.section}{informal_warn}{superseded_warn} ---\n"
            f"{chunk.text}"
        )

    context_block = "\n\n".join(context_parts)

    prompt = f"""{SYSTEM_PROMPT}

# Documentos recuperados

{context_block}

# Pergunta do atendente

{pergunta}"""

    token_estimate = int(len(prompt.split()) / 0.75)
    print(f"[prompt] ~{token_estimate} tokens | {len(chunks)} chunks | pergunta: '{pergunta[:60]}'")

    return prompt


def estimar_tokens(prompt: str) -> dict:
    words = len(prompt.split())
    system_words = len(SYSTEM_PROMPT.split())
    return {
        "total_estimado": int(words / 0.75),
        "system_prompt": int(system_words / 0.75),
        "chunks_pergunta": int((words - system_words) / 0.75),
        "pct_janela_gpt4o": round(int(words / 0.75) / 128000 * 100, 2),
    }
