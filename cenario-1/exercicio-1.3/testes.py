"""
Testes do pipeline de RAG — 5 perguntas do mapa de cobertura do Anexo B.

Para cada pergunta:
  1. Executa a busca semântica
  2. Exibe os chunks recuperados com scores
  3. Compara com o gabarito do Anexo B
  4. Monta o prompt completo pronto para colar no LLM

Uso:
  python testes.py            # roda todos os testes
  python testes.py --ingerir  # reindexa os documentos antes de testar
"""

import sys
import argparse
from pipeline.ingestao import ingest
from pipeline.busca import buscar, imprimir_resultados
from pipeline.prompt import montar_prompt, estimar_tokens

# ---------------------------------------------------------------------------
# Gabarito do Anexo B (mapa de cobertura)
# chunk_id_hint é o doc_id que DEVE aparecer no top-3 para o teste passar
# ---------------------------------------------------------------------------
TESTES = [
    {
        "id": "T1",
        "pergunta": "Qual o prazo de devolução?",
        "gabarito_doc_ids": ["POL-001"],
        "gabarito_secoes_hint": ["3.1", "3.2", "Prazo", "Exceç"],
        "nota": "Deve recuperar prazo geral (3.1) E exceções (3.2). Se só recuperar 3.1, perde a armadilha das cargas perigosas.",
    },
    {
        "id": "T2",
        "pergunta": "Posso devolver carga perigosa?",
        "gabarito_doc_ids": ["POL-001"],
        "gabarito_secoes_hint": ["3.2", "Exceç", "perigosa"],
        "nota": "Deve recuperar a seção de exceções (3.2). Resposta correta: NÃO é elegível pelo processo padrão.",
    },
    {
        "id": "T3",
        "pergunta": "Qual o SLA de resolução do cliente Gold?",
        "gabarito_doc_ids": ["SLA-2024"],
        "gabarito_secoes_hint": ["SLA", "Tabela", "Gold"],
        "nota": "Deve recuperar a tabela de SLAs. Resposta: 24h resolução, 2h primeira resposta.",
    },
    {
        "id": "T4",
        "pergunta": "Quanto custa o frete especial para 600kg para Manaus?",
        "gabarito_doc_ids": ["PROC-042-v2"],
        "gabarito_secoes_hint": ["2", "Fórmula", "Multiplicador", "Norte"],
        "nota": "Deve recuperar PROC-042-v2 (não v1). Multiplicador Norte=1.8. Valor base ausente — não pode calcular total.",
    },
    {
        "id": "T5",
        "pergunta": "Qual o multiplicador regional para o Sudeste?",
        "gabarito_doc_ids": ["PROC-042-v2"],
        "gabarito_secoes_hint": ["Multiplicador", "Sudeste", "regional"],
        "nota": "Armadilha de contradição: PROC-042 v1 tem Sudeste=1.0, v2 tem Sudeste=1.1. Pipeline deve priorizar v2 (status=active).",
    },
]


def avaliar_resultado(teste: dict, resultados) -> dict:
    """Verifica se o gabarito aparece no top-3 dos resultados."""
    top3_doc_ids = [r.doc_id for r in resultados[:3]]
    top3_sections = " ".join(r.section for r in resultados[:3]).lower()

    doc_ok = any(gid in top3_doc_ids for gid in teste["gabarito_doc_ids"])
    sec_ok = any(hint.lower() in top3_sections for hint in teste["gabarito_secoes_hint"])

    # Verificar se versão superseded aparece no top-3 (problema de contradição)
    superseded_in_top3 = any(r.status == "superseded" for r in resultados[:3])

    return {
        "doc_correto": doc_ok,
        "secao_hint_ok": sec_ok,
        "superseded_no_top3": superseded_in_top3,
        "passou": doc_ok and sec_ok,
    }


def rodar_testes(montar_prompts: bool = False) -> None:
    print("\n" + "=" * 70)
    print("PIPELINE DE RAG — NOVATECH | 5 TESTES DO ANEXO B")
    print("=" * 70)

    resumo = []

    for teste in TESTES:
        resultados = buscar(teste["pergunta"], n_retrieve=20, n_return=8)
        imprimir_resultados(teste["pergunta"], resultados)

        avaliacao = avaliar_resultado(teste, resultados)

        status = "PASSOU ✓" if avaliacao["passou"] else "FALHOU ✗"
        warn = " ⚠️  versão superseded no top-3!" if avaliacao["superseded_no_top3"] else ""
        print(f"\n[{teste['id']}] {status}{warn}")
        print(f"     Nota do gabarito: {teste['nota']}")

        if montar_prompts:
            prompt = montar_prompt(teste["pergunta"], resultados[:5])
            tokens = estimar_tokens(prompt)
            print(f"\n--- PROMPT MONTADO (T{teste['id']}) ---")
            print(prompt)
            print(f"\n--- ESTIMATIVA DE TOKENS: {tokens} ---")

        resumo.append({
            "id": teste["id"],
            "pergunta": teste["pergunta"],
            "passou": avaliacao["passou"],
            "doc_correto": avaliacao["doc_correto"],
            "superseded_no_top3": avaliacao["superseded_no_top3"],
        })

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    passou = sum(1 for r in resumo if r["passou"])
    print(f"Resultado: {passou}/{len(resumo)} testes passaram\n")
    for r in resumo:
        icon = "✓" if r["passou"] else "✗"
        sup = " [superseded no top-3]" if r["superseded_no_top3"] else ""
        print(f"  [{icon}] {r['id']} — {r['pergunta']}{sup}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingerir", action="store_true", help="Reindexa os documentos antes de testar")
    parser.add_argument("--prompts", action="store_true", help="Exibe o prompt montado para cada teste")
    args = parser.parse_args()

    if args.ingerir:
        print("Iniciando ingestão dos documentos...\n")
        ingest()

    rodar_testes(montar_prompts=args.prompts)
