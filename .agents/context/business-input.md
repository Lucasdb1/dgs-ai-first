---
name: business-input
description: Entrada bruta do usuário para a descoberta do Cenário 3 do dgs-ai-first e índice de proveniência das fontes consultadas (README, materiais do Cenário 2, scaffold do novatech-assistant, memória de sessões anteriores).
metadata:
  author: clovis-cli
  responsibility: Registro fiel do material de negócio fornecido pelo usuário e índice de proveniência e reacesso desse material, organizado por fonte. A Etapa 2 reabre as fontes originais a partir daqui; não classifica domínios, fronteiras, dependências nem grau de confiança.
---

## Entrada do usuário (preservada)

**Campo de regras de negócio (texto digitado pelo usuário):**
> as regras estao em .md dentro do projeto ... para diferentes cenarios

**Campo de restrições declaradas (texto digitado pelo usuário):**
> analisar o que foi feito e trazer insights e fazer o cenario 3 aqui no clovis , o 2 e 1 foi atra´ves do claude code, então pegue na memoria tamb´me , o 2.1 foi finalizado agora tamo fazendo o 2.2 , pegue contexto..

**Resposta humana ao gap `cenario-3-business-rules-source` (rodada de incorporação):**
> faça um ls -l na pasta e identifique os arquivos

O usuário não indicou um caminho específico para um enunciado do Cenário 3 — orientou a localizar a fonte diretamente na estrutura do projeto. Nenhum arquivo ou pasta dedicada ao Cenário 3 foi encontrado (ver índice abaixo); a informação usada para caracterizar o Cenário 3 veio por inferência a partir de outras fontes já existentes no projeto, indexadas abaixo.

---

## Índice de fontes consultadas

### 1. `README.md` (raiz do repositório)

- **Proveniência:** arquivo local, tabela de cenários (linhas 13–17) e seção "Estrutura" (linhas 23–38).
- **Reacesso:** `cat README.md` na raiz do repositório.
- **Informação relevante:** tabela lista os 3 cenários por branch; Cenário 1 = "Fundamentos · Prompt · Contexto · RAG/MCP" (entregue 06/06/2026); Cenário 2 = tópicos "a definir" no texto mas detalhados no material do próprio cenário (ver item 3); Cenário 3 = tópicos explicitamente marcados como **"a definir"**, entrega 27/06/2026.

### 2. Listagem de diretórios (`ls -l`) — raiz e subpastas

- **Proveniência:** comando executado diretamente no diretório de trabalho `/home/lucascosta/ProjetosDB1/dgs-ai-first` (raiz, `cenario-1/`, `cenario-2/`, `material-pratica-1/`, `.claude/`, `.clovis/`), a pedido explícito do usuário na resposta ao gap.
- **Reacesso:** `ls -la` em cada uma dessas pastas.
- **Informação relevante:** confirma que **não existe** pasta `cenario-3/`, `material-pratica-3/` nem qualquer arquivo com enunciado do Cenário 3 no projeto. Também não há `.docx`, `.zip` ou outro documento oculto correspondente (busca por extensão em todo o repositório).

### 3. `cenario-2/material-pratica/exercicio-2-fase-estruturacao.md`

- **Proveniência:** arquivo local, cabeçalho "Tópicos cobertos" (linhas 1–7) e seção "O que foi definido na fase anterior (cenário 1)" (linhas 26–37).
- **Reacesso:** `cat cenario-2/material-pratica/exercicio-2-fase-estruturacao.md`.
- **Informação relevante:** tópicos do Cenário 2 = MCP, Recorte de Domínio e SDD, AGENTS.md, Skills. Resumo das decisões já tomadas no Cenário 1 (modelo LLM, pipeline RAG, context budget, tratamento de documentos contraditórios, arquitetura de 4 componentes, stack, equipe).

### 4. `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md`

- **Proveniência:** arquivo local, blocos "Estrutura de diretórios" (linhas 9–138) e "Estado atual do repositório" (linhas 169–182).
- **Reacesso:** `cat cenario-2/material-pratica/anexo-c-estrutura-repositorio.md`.
- **Informação relevante:** blueprint da árvore do `novatech-assistant`, com 5 módulos de spec (`pipeline-ingestao`, `query-endpoint`, `feedback-api`, `teams-bot`, `painel-web`), estrutura de `src/`, skills em 3 níveis (foundation/domain/artifact), convenção de ADRs, exemplo de `.mcp/mcp.json`.

### 5. `cenario-2/novatech-assistant/` (scaffold local do projeto simulado)

- **Proveniência:** pasta versionada como scaffold de código do exercício — `AGENTS.md` (constitution ainda com seções `<!-- TODO -->`), `README.md`, `docs/onboarding.md` (vazio), `prompts/system-prompt.md` (v1 herdado do Cenário 1), `prompts/prompt-changelog.md`.
- **Reacesso:** `ls -la cenario-2/novatech-assistant/` e leitura direta de cada arquivo.
- **Informação relevante:** confirma que specs/, src/, skills/, tests/ e infra/ ainda **não foram criados** neste scaffold local — apenas o blueprint (item 4) e os artefatos dos exercícios 2.1/2.2 (itens 6–8) existem hoje.

### 6. `cenario-2/exercicio-2.1/mapeamento-mcp.md`

- **Proveniência:** arquivo local, seções 1–5 (necessidades → servers, tools/resources, least privilege, matriz de consumo por papel).
- **Reacesso:** `cat cenario-2/exercicio-2.1/mapeamento-mcp.md`.
- **Informação relevante:** decisão de MCP servers do projeto: `filesystem-code`, `filesystem-docs` (somente leitura), `git`, `memory`; justificativa de least privilege.

### 7. `cenario-2/exercicio-2.1/analise-riscos.md`

- **Proveniência:** arquivo local, 3 riscos descritos (linhas 7–68) e tabela-resumo (linhas 70–76).
- **Reacesso:** `cat cenario-2/exercicio-2.1/analise-riscos.md`.
- **Informação relevante:** regras de segurança já decididas — nunca `git_commit`/`git_add` via MCP sem aprovação humana; nunca `write_file` em `docs/novatech/` ou `data/retrieval-corpus/`; destino declarado no próprio documento: seção "Coding Standards" do `AGENTS.md`.

### 8. `cenario-2/exercicio-2.2/tasks.md` e `cenario-2/exercicio-2.2/revisao-critica.md`

- **Proveniência:** arquivos locais — `tasks.md` (TASK-001 a TASK-010 do módulo `query-endpoint`) e `revisao-critica.md` (3 problemas encontrados no código gerado por Copilot para TASK-001/TASK-002).
- **Reacesso:** `cat cenario-2/exercicio-2.2/tasks.md` / `cat cenario-2/exercicio-2.2/revisao-critica.md`.
- **Informação relevante:** único módulo dos 5 do Anexo C com evidência de código real já esboçado (mesmo que ainda não mergeado); confirma contrato do endpoint de consulta (`source_document` nunca nulo, budget de contexto, priorização de versão de documento).

### 9. Memória de sessões anteriores (auto-memory, fora do repositório)

- **Proveniência:** arquivos de memória persistente do agente em `/home/lucascosta/.claude/projects/-home-lucascosta-ProjetosDB1-dgs-ai-first/memory/`: `project_ai_first_training.md`, `feedback_cenario1_patterns.md`, `user_role.md`, `reference_pratica1_materials.md`.
- **Reacesso:** memória automática do agente, carregada a cada sessão neste diretório de trabalho; não é um arquivo do repositório Git.
- **Informação relevante:** confirma que a Trilha de Formação cobre 10 tópicos (Gen AI, Prompt Eng, Context Eng, RAG/MCP, AI Agents, Spec Driven Development, Agents.md, Skills, Harness Engineering, Critical Review); Cenário 1 está 100% concluído (exercícios 1.1, 1.2, 1.3); Cenário 2 tem o exercício 2.1 concluído e o 2.2 em andamento nesta sessão.

### 10. `Trilha de Formação - DGS AI First.pdf` (raiz do repositório)

- **Proveniência:** arquivo binário PDF na raiz do repositório.
- **Reacesso:** tentativa de leitura direta nesta sessão falhou por ausência de `poppler-utils`/`pdftoppm` no ambiente de execução; uma varredura textual bruta (`strings`) não encontrou menções a "Cenário 3" no conteúdo bruto do PDF (o texto pode estar comprimido/não indexável dessa forma). Sessões anteriores (ver item 9) já haviam caracterizado este arquivo como material de referência geral da trilha (links de estudo dos 10 tópicos), não como o enunciado de um cenário-âncora específico.
- **Informação relevante:** não contribuiu com conteúdo específico do Cenário 3 nesta rodada; mantido aqui apenas como fonte já registrada, caso um reacesso futuro (com `poppler-utils` instalado) traga informação nova.
