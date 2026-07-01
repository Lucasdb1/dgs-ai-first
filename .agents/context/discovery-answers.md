---
name: discovery-answers
description: Objetivo e escopo do Cenário 3 (dgs-ai-first), restrições declaradas, decisões transversais herdadas do Cenário 2 com destino, e o log da decisão humana que resolveu o gap da fonte de regras de negócio do Cenário 3.
metadata:
  author: clovis-cli
  responsibility: "Memória durável do contexto e das decisões da descoberta funcional: objetivo, escopo, restrições declaradas, decisões transversais validadas (com destino), formas de documentação a manter e o log das decisões humanas resolvidas no loop de gaps. Fonte relida pelas etapas seguintes; suas restrições têm precedência sobre inferências posteriores."
---

## Objetivo e escopo

Descoberta funcional greenfield do projeto `dgs-ai-first`, especificamente para o **Cenário 3** da Trilha de Formação AI First (DGS/DB1). Tipo de sistema declarado: `treinamento`. Escopo: projeto inteiro.

Os Cenários 1 e 2 já foram executados manualmente (via Claude Code, fora do fluxo Clovis) e estão registrados em `cenario-1/` e `cenario-2/` do repositório — ver `business-input.md` para o índice de fontes. O Cenário 1 está 100% concluído (exercícios 1.1, 1.2 e 1.3 — análise de viabilidade RAG, prototipação de system prompt, pipeline RAG open-source). No Cenário 2, o exercício 2.1 (mapeamento de MCP servers e análise de riscos) está concluído e o exercício 2.2 (tasks.md + revisão crítica de código do módulo `query-endpoint`) está em andamento no momento desta descoberta.

O objetivo desta rodada é usar o fluxo Clovis para estruturar o **Cenário 3**, cujo enunciado formal ainda não existe no projeto (ver log de gap abaixo).

## Restrições declaradas pelo usuário

- Analisar o que já foi feito nos Cenários 1 e 2 e trazer insights antes de avançar.
- Executar o Cenário 3 usando o fluxo Clovis (diferente de 1 e 2, feitos via Claude Code direto).
- Considerar o contexto de que o Exercício 2.1 foi finalizado e o 2.2 está em andamento.
- Nenhuma restrição de stack, contrato ou schema fixo foi declarada além do que já está registrado como decisão herdada do Cenário 2 (ver seção seguinte).

## Log de gaps resolvidos

### Gap `cenario-3-business-rules-source`

- **O que era:** não foi localizada, em nenhuma fonte do projeto, a fonte com o enunciado/regras de negócio do Cenário 3 (equivalente a `material-pratica-1/exercicio-fase-1-entendimento.md` do Cenário 1 ou `cenario-2/material-pratica/exercicio-2-fase-estruturacao.md` do Cenário 2). O `README.md` lista os tópicos do Cenário 3 como "a definir".
- **O que foi decidido:** o usuário respondeu orientando a fazer `ls -l` na pasta e identificar os arquivos existentes, em vez de fornecer um novo documento. A listagem exaustiva (raiz, `cenario-1/`, `cenario-2/`, `material-pratica-1/`, `.claude/`, `.clovis/`, busca por `.docx`/`.pdf`/`.zip`) confirmou que **não existe** fonte dedicada ao Cenário 3 no projeto.
  - Diante da ausência confirmada, o Cenário 3 foi **inferido por evidência indireta**, não assumido arbitrariamente: a memória de sessões anteriores registra que a Trilha de Formação cobre 10 tópicos (Gen AI, Prompt Eng, Context Eng, RAG/MCP, AI Agents, Spec Driven Development, Agents.md, Skills, Harness Engineering, Critical Review de Outputs de IA). O Cenário 1 já consumiu 4 desses tópicos (Fundamentos · Prompt · Contexto · RAG/MCP — conforme a própria tabela do `README.md`) e o Cenário 2 consumiu outros 4 (MCP · Recorte de Domínio/SDD · AGENTS.md · Skills — conforme `cenario-2/material-pratica/exercicio-2-fase-estruturacao.md`). Restam exatamente 3 tópicos não cobertos: **AI Agents, Harness Engineering e Critical Review de Outputs de IA**.
  - **Decisão registrada:** o Cenário 3 é a fase de **implementação** do `novatech-assistant` (os 5 módulos já recortados no Anexo C do Cenário 2 — ver `functional-map.md`) efetivamente escrita por agentes de IA (tópico "AI Agents"), com harness de validação determinística das respostas do assistente (tópico "Harness Engineering" — capacidade já esboçada em `services/response-validator.ts` no blueprint do Anexo C) e com revisão crítica formal dos artefatos gerados (tópico "Critical Review" — o exercício 2.2 já iniciou esse padrão com `revisao-critica.md` e deve se aprofundar no Cenário 3).
  - Esta decisão tem confiança **média**: é uma inferência por subtração de um conjunto fechado de tópicos já documentado, não uma confirmação direta de um enunciado oficial do Cenário 3. Caso um enunciado oficial apareça depois (ex.: o usuário encontrar o documento ou a trilha for atualizada), esta seção deve ser revista.

## Decisões transversais herdadas do Cenário 2 (com efeito no Cenário 3)

Estas decisões já estavam validadas antes desta rodada (evidência em `cenario-2/material-pratica/exercicio-2-fase-estruturacao.md`, `cenario-2/exercicio-2.1/mapeamento-mcp.md` e `cenario-2/exercicio-2.1/analise-riscos.md`) e continuam valendo para o Cenário 3. O efeito de cada uma está refletido no bloco do domínio correspondente em `functional-map.md`.

- **Modelo LLM:** Azure OpenAI GPT-4o (ADR-0001, janela de 128K tokens). Destino: convenção no `AGENTS.md` (seção Tech Stack & Architecture).
- **Pipeline de RAG em produção:** Azure AI Search + Azure OpenAI, substituindo o protótipo open-source (ChromaDB + sentence-transformers) do Cenário 1. Problema de chunking de tabelas identificado no protótipo (ADR-0004) deve ser tratado no domínio `ingestion-pipeline`.
- **Context budget:** ~4K tokens para system prompt + ~8K tokens para até 5 chunks (~1.500 tokens cada) + pergunta + histórico limitado a 3 turnos (ADR-0002). Já existe enforcement especificado no domínio `query-assistant` (TASK-005 do `tasks.md`).
- **Documentos contraditórios:** metadado de vigência no pipeline; prompt instrui priorizar a versão mais recente; documentos obsoletos marcados, não excluídos (ADR-0003). Efeito direto no domínio `query-assistant` (TASK-006).
- **Stack:** TypeScript estrito (backend e bot), React (painel web), Bicep (infraestrutura como código, tratada como estado narrativo nesta fase de treinamento — nenhum recurso Azure real é provisionado).
- **MCP servers do projeto:** `filesystem-code` (escreve `./src ./specs ./skills ./docs/adr ./prompts ./tests`), `filesystem-docs` (somente leitura, `./docs/novatech` e `./data/retrieval-corpus`), `git` (repositório local, sem remoto), `memory` (grafo local). Racional de least privilege documentado em `mapeamento-mcp.md`. Destino: **technical-skill** `mcp-server-configuration` (how-to substancial e reutilizável — ver `technicalSkills`).
- **Regras de segurança de agentes (governança, não regra de negócio de domínio):**
  - Nunca usar `git_commit`/`git_add` via MCP sem aprovação explícita do desenvolvedor (mitigação do Risco 2, `analise-riscos.md`).
  - Nunca usar `write_file` em `./docs/novatech/` ou `./data/retrieval-corpus/` (mitigação do Risco 3, `analise-riscos.md`).
  - Ambas são regras curtas e estáveis — destino: convenção na seção "Coding Standards" do `AGENTS.md` do `novatech-assistant`, não uma `technical-skill` dedicada.
- **Skills reutilizáveis do projeto:** hierarquia em 3 níveis — Foundation → Domain → Artifact (Anexo C, pasta `skills/`). Destino: **technical-skill** `skill-authoring-hierarchy` (padrão reutilizável para criar novas skills técnicas/de domínio).
- **Formas de documentação a manter além das skills de negócio:** ADRs já adotados no projeto (`docs/adr/`, template com Contexto/Decisão/Consequências/Alternativas, nomenclatura `NNNN-titulo-da-decisao.md`) — evidência direta no Anexo C, sem necessidade de gap. Nenhuma outra forma (Swagger/OpenAPI, Postman, Storybook) foi evidenciada ou declarada até o momento; se algum módulo do Cenário 3 expuser uma API HTTP externa de forma mais ampla, reavaliar a necessidade de Swagger/OpenAPI como gap em etapa futura.

## Framework de spec-driven concorrente

Nenhum framework de terceiros concorrente (Spec Kit, OpenSpec ou similar) foi detectado — não há diretórios `.specify/` ou `openspec/` em nenhuma branch. O próprio `novatech-assistant` já usa uma convenção de três artefatos por módulo (`requirements.md`, `plan.md`, `tasks.md` sob `specs/<slug>/`, Anexo C) — é a metodologia SDD ensinada na própria trilha, não uma ferramenta de terceiros, e vive em um caminho (`cenario-2/novatech-assistant/specs/`) distinto de onde os artefatos Clovis desta descoberta são gravados (`.agents/` na raiz do `dgs-ai-first`). Não há conflito de fonte de verdade; nenhuma decisão de remoção foi necessária.
