---
name: functional-map
description: Mapa dos 5 domínios do novatech-assistant (ingestão, consulta/RAG, feedback, bot do Teams e painel web) recortados no Anexo C do Cenário 2, com o efeito das decisões herdadas já refletido em cada bloco — base para a implementação do Cenário 3.
metadata:
  author: clovis-cli
  responsibility: "Mapa de identificação dos domínios de negócio (bounded contexts), suas fronteiras, dependências e ordem de implementação sugerida. Índice de domínios para a geração de skills e o fluxo spec-driven; não detalha regras de negócio nem duplica as decisões transversais, que vivem no discovery-answers.md."
---

## Contexto

Os domínios abaixo descrevem o `novatech-assistant` — o assistente de IA de atendimento da NovaTech (empresa fictícia de logística) que o time está construindo desde o Cenário 1. O recorte segue exatamente os 5 módulos definidos no `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` (cada um com sua própria pasta `specs/<slug>/{requirements,plan,tasks}.md` e pasta própria em `src/`) — essa é a granularidade que o próprio time do exercício já validou, refletida na estrutura de diretórios do Anexo C. O Cenário 3 é a fase em que esses módulos passam de blueprint para implementação real por agentes de IA (ver `discovery-answers.md`).

Apenas o módulo `query-assistant` tem hoje evidência de código real esboçado (Exercício 2.2, TASK-001/002 geradas com Copilot). Os outros quatro existem apenas como blueprint no Anexo C — não há ainda `requirements.md`/`plan.md`/`tasks.md` escritos para eles no scaffold local.

---

## Domínio: Pipeline de Ingestão de Documentos

**Slug:** `ingestion-pipeline`

**Objetivo de negócio:** transformar a documentação de negócio da NovaTech (POL-001, PROC-042/v2, SLA-2024, FAQ-Atendimento e demais fontes futuras) em chunks indexados e pesquisáveis, mantendo metadado de vigência para lidar com versões contraditórias.

**Evidências no material fornecido:**
- `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` — pasta `specs/pipeline-ingestao/` e módulo `src/pipeline/` (`extractor.ts`, `chunker.ts`, `embedder.ts`, `indexer.ts`).
- `cenario-2/material-pratica/exercicio-2-fase-estruturacao.md` — decisões herdadas do Cenário 1 sobre a base documental (847 documentos válidos após deduplicação, 12 com contradições pendentes de resolução pelo Compliance da NovaTech, 63 obsoletos, ~340 duplicatas eliminadas).

**Dependências entre domínios:** nenhuma (é a base de dados para os demais domínios).

**Regras inferidas:**
- Chunking de tabelas exige tratamento especial — o protótipo open-source do Cenário 1 (ChromaDB) identificou que gera embeddings ruins (ADR-0004); a estratégia de chunking híbrido validada no protótipo deve ser portada para produção.
- Documentos com contradições pendentes (12 dos 847) precisam do metadado de vigência (ADR-0003) até que o Compliance da NovaTech resolva a divergência.

**Dependências externas relevantes:** Azure AI Search (indexação em produção, substitui o `ChromaDB` do protótipo), Azure OpenAI (`text-embedding-ada-002`, mesmo modelo usado no domínio `query-assistant`).

**Grau de confiança:** alto (evidência direta e inequívoca no Anexo C, reforçada pelas decisões já registradas no discovery do Cenário 1).

---

## Domínio: Consulta do Assistente (RAG Query)

**Slug:** `query-assistant`

**Objetivo de negócio:** responder, em linguagem natural, às perguntas dos atendentes da NovaTech sobre procedimentos, SLAs e regras de frete, citando sempre a fonte documental e respeitando o orçamento de contexto do modelo.

**Evidências no código:**
- `cenario-2/exercicio-2.2/tasks.md` — TASK-001 a TASK-010: endpoint HTTP (`POST /api/query`), validação Zod, cliente de embeddings, busca no Azure AI Search (top-5), enforcement de context budget, montagem de prompt com priorização de versão, chamada ao GPT-4o, response builder, testes unitários e de integração.
- `cenario-2/exercicio-2.2/revisao-critica.md` — revisão do código gerado por Copilot para TASK-001/TASK-002: contrato `source_document` nunca nulo, correção do guard de método HTTP, `.trim()` na validação de `question`.

**Evidências no material fornecido:**
- `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` — pasta `specs/query-endpoint/` e módulos `src/functions/query/` + `src/services/` (`search.ts`, `completion.ts`, `prompt-builder.ts`, `response-validator.ts`).

**Dependências entre domínios:** `ingestion-pipeline` (precisa dos documentos já indexados para buscar chunks).

**Regras inferidas:**
- `source_document` na resposta nunca pode ser `null`/`undefined` — contrato explícito validado na revisão crítica.
- Context budget de ~8K tokens em chunks é descartado por chunk excedente, nunca truncado (TASK-005 / ADR-0002).
- Quando dois chunks de versões conflitantes de PROC-042 aparecem juntos, o prompt deve instruir a priorizar a versão mais recente (TASK-006 / ADR-0003).
- `response-validator.ts` (harness de validação determinística da resposta) é a capacidade que sustenta o tópico "Harness Engineering" do Cenário 3 — ver `discovery-answers.md`.

**Dependências externas relevantes:** Azure AI Search, Azure OpenAI (`GPT-4o` para completion, `text-embedding-ada-002` para embeddings), Zod (validação de schema), pino (logging).

**Grau de confiança:** alto (único domínio com evidência de código já gerado e revisado).

---

## Domínio: Feedback de Respostas

**Slug:** `feedback`

**Objetivo de negócio:** capturar a avaliação do atendente sobre a qualidade de uma resposta do assistente (útil / não útil, comentário), para alimentar o painel de métricas e futuras iterações do prompt.

**Evidências no material fornecido:**
- `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` — pasta `specs/feedback-api/` e módulo `src/functions/feedback/` (`handler.ts`, `validator.ts`); consumido também por `src/bot/cards/feedback-card.ts` (Adaptive Card do Teams).

**Dependências entre domínios:** `query-assistant` (o feedback se refere a uma resposta específica já gerada por esse domínio).

**Regras inferidas:** nenhuma regra de negócio detalhada está evidenciada além da existência do endpoint e do card do Teams — o `requirements.md` deste módulo ainda não foi escrito no scaffold local.

**Dependências externas relevantes:** nenhuma além da stack já registrada (Azure Functions, TypeScript).

**Grau de confiança:** médio (o módulo existe e está recortado no Anexo C, mas sem `requirements.md`/critérios de aceite ainda escritos — mais raso que `query-assistant`).

---

## Domínio: Integração com Microsoft Teams

**Slug:** `teams-bot`

**Objetivo de negócio:** expor o assistente dentro do Microsoft Teams, onde os atendentes já trabalham, evitando que precisem sair da ferramenta para consultar documentação.

**Evidências no material fornecido:**
- `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` — pasta `specs/teams-bot/` e módulo `src/bot/` (`bot.ts`, `cards/response-card.ts`, `cards/feedback-card.ts`).
- `cenario-2/material-pratica/exercicio-2-fase-estruturacao.md` — "Integração: Microsoft Teams (bot) + painel web interno", decisão já validada no Cenário 1.

**Dependências entre domínios:** `query-assistant` (encaminha a pergunta do usuário e recebe a resposta formatada), `feedback` (usa o `feedback-card` para capturar avaliação inline no Teams).

**Regras inferidas:** nenhuma regra de negócio própria além de formatar a resposta como Adaptive Card — a lógica de negócio (busca, prompt, resposta) pertence a `query-assistant`.

**Dependências externas relevantes:** Bot Framework (Microsoft Teams).

**Grau de confiança:** médio (recorte de módulo claro no Anexo C, mas sem código ou `requirements.md` ainda escritos).

---

## Domínio: Painel Web de Métricas

**Slug:** `web-dashboard`

**Objetivo de negócio:** dar visibilidade interna (para Delivery Manager, Tech Lead e Product Specialist) sobre o uso do assistente — volume de consultas, histórico e indicadores de qualidade a partir do feedback capturado.

**Evidências no material fornecido:**
- `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` — pasta `specs/painel-web/` e módulo `src/web/` (React, `components/`, `pages/`, `App.tsx`).
- `cenario-2/material-pratica/exercicio-2-fase-estruturacao.md` — "(4) painel web interno (dashboard de métricas e histórico)" como um dos 4 componentes da arquitetura.

**Dependências entre domínios:** `query-assistant` (histórico de consultas), `feedback` (indicadores de qualidade agregados).

**Regras inferidas:** nenhuma regra de negócio própria evidenciada além de "métricas e histórico" — é majoritariamente uma camada de leitura/relatório sobre dados de outros domínios. Confiança rebaixada para médio por essa razão: se, na prática, o painel não desenvolver regra de agregação/SLA própria, ele pode terminar como uma capacidade fina do domínio `query-assistant` + `feedback` em vez de um domínio pleno — mas o Anexo C já o trata como módulo com `requirements.md` próprio (dono: Product Specialist), então mantém-se separado nesta rodada.

**Dependências externas relevantes:** React (stack já registrada em `discovery-answers.md`).

**Grau de confiança:** médio.

---

## Gaps em aberto

Nenhum gap bloqueante permanece aberto nesta rodada. Um ponto de atenção não bloqueante (não escalado como gap por não impedir o avanço para a Etapa 2): se `web-dashboard` deve permanecer domínio pleno ou ser tratado como capacidade de relatório dos domínios `query-assistant`/`feedback`, só ficará claro quando seu `requirements.md` for escrito — revisar a granularidade nesse momento.
