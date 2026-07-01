# AGENTS.md

## Visão geral

`dgs-ai-first` é o repositório pessoal de Lucas Costa (DB1) para a Trilha de Formação AI First (DGS/DB1). Os entregáveis são organizados por cenário, um por branch/pasta (`cenario-1/`, `cenario-2/`, `cenario-3/` quando criado); a `main` funciona como vitrine de documentação.

O caso-âncora é a NovaTech, uma empresa fictícia de logística: a DB1 constrói um assistente de IA (`novatech-assistant`) que responde em linguagem natural a perguntas de atendimento, citando sempre a fonte documental. O Cenário 3 é a fase de implementação real desse assistente por agentes de IA — cinco domínios de negócio (`ingestion-pipeline`, `query-assistant`, `feedback`, `teams-bot`, `web-dashboard`), detalhados em `.agents/maps/functional-map.md`. As decisões e restrições que fundamentam este arquivo estão registradas em `.agents/context/discovery-answers.md` e `.agents/context/business-input.md`.

Ferramentas de agente usadas no projeto: Claude, Claude Code, GitHub Copilot. Nenhum dado real de cliente entra em qualquer entregável — apenas o material fictício da NovaTech.

## Stack principal

Decisões herdadas do Cenário 2, válidas para a implementação do Cenário 3 (evidência: `.agents/context/discovery-answers.md`):

- **LLM:** Azure OpenAI GPT-4o (janela de 128K tokens).
- **RAG em produção:** Azure AI Search + Azure OpenAI (`text-embedding-ada-002`). O protótipo do Cenário 1 (ChromaDB + sentence-transformers) foi descontinuado.
- **Backend e bot:** TypeScript estrito.
- **Painel web:** React.
- **Infraestrutura:** Bicep — nesta fase de treinamento é tratada como estado narrativo; nenhum recurso Azure real é provisionado.

## Estrutura do repositório

- `cenario-1/`, `cenario-2/`: entregáveis dos cenários já concluídos/em andamento, cada um com subpastas `exercicio-X.Y/`.
- `material-pratica-1/`: enunciados e documentos-fonte do caso NovaTech (POL-001, PROC-042, PROC-042-v2, SLA-2024, FAQ-Atendimento).
- `.claude/skills/`: skills nativas do Claude Code usadas nos Cenários 1 e 2 (`novatech-context`, `rag-viability-analysis`, `devils-advocate-review`) — continuam versionadas e ativas.
- `cenario-2/novatech-assistant/`: código-fonte do assistente — repositório Git aninhado e independente (tem seu próprio `.git`), iniciado a partir do starter repo do Anexo C do Cenário 2. Contém `specs/`, `src/`, `skills/`, `tests/`, `infra/`, `.mcp/`, `docs/adr/` e sua própria constitution (`AGENTS.md`), com seções preenchidas pelos papéis dos exercícios do Cenário 2.
- `.agents/`: artefatos do fluxo de preparação orientado por agente para este projeto (ver seção dedicada abaixo).

## Convenções arquiteturais

- Cada domínio de negócio do `novatech-assistant` segue SDD: `specs/<slug>/{requirements,plan,tasks}.md` antes de qualquer implementação em `src/` (ver os 5 domínios e suas dependências em `.agents/maps/functional-map.md`).
- Decisões arquiteturais relevantes são registradas como ADR, nomenclatura `NNNN-titulo-da-decisao.md`, formato Contexto/Decisão/Consequências/Alternativas Consideradas (evidência: `cenario-2/novatech-assistant/docs/adr/template.md`).
- Commits seguem Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`) com descrição breve referenciando o exercício/cenário quando aplicável (evidência: histórico de commits do repositório).

## Restrições globais

- Nenhum dado real de cliente em qualquer entregável — apenas o material fictício da NovaTech.

## Comandos essenciais

A raiz do repositório não tem tooling de build próprio — é um contêiner de documentação e exercícios. O único código com scripts de desenvolvimento evidenciados hoje é o `novatech-assistant`:

```bash
cd cenario-2/novatech-assistant
npm run build   # tsc -p .
npm run lint    # eslint .
npm run test    # vitest run
```

## `.agents/`

- `.agents/context/`: artefatos da descoberta funcional (`discovery-answers.md`, `business-input.md`) — objetivo, escopo, restrições e decisões validadas com o usuário. Releia antes de qualquer decisão que dependa de contexto de negócio.
- `.agents/maps/`: `functional-map.md` — mapa dos domínios de negócio, fronteiras e dependências.
- `.agents/skills/`: concentra tanto as skills de negócio (domínio NovaTech) quanto as skills técnicas (transversais) deste projeto, geradas nas rodadas seguintes desta etapa de preparação. Todas são carregadas sob demanda pelo agente a partir do frontmatter `description` de cada skill — não há necessidade de um índice manual aqui.

## Fonte de documentação autoritativa do domínio

As **skills locais em `.agents/skills/`** são a fonte de verdade do domínio NovaTech. Consulte-as e mantenha-as atualizadas antes de implementar qualquer regra de negócio.
