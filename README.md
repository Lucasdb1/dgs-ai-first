# dgs-ai-first

Repositório de **Lucas Costa** para a **Trilha de Formação AI First — DGS / DB1**.

> Um caderno de campo. Anotações, exercícios e protótipos enquanto atravesso a trilha que prepara os times da DGS para o novo SDLC AI First.

---

## Sobre

A trilha cobre dez tópicos — de fundamentos de IA generativa a engenharia de harness — e fecha com prova de certificação. Os entregáveis estão organizados em três cenários, um por branch:

| Cenário | Branch | Tópicos | Entrega |
| :--- | :--- | :--- | :--- |
| 1 | `cenario-1` | Fundamentos · Prompt · Contexto · RAG/MCP | 06/06/2026 |
| 2 | `cenario-2` | MCP · SDD · AGENTS.md · Skills | 01/07/2026 |
| 3 | `cenario-3` | _a definir_ | 27/06/2026 |

A `main` permanece como vitrine: documentação, skills e índice dos cenários.

---

## Estrutura

```
.
├── README.md                     — este documento
├── AGENTS.md                     — constitution do repositório (lido por agentes de IA)
├── material-pratica-1/           — enunciados e anexos da Prática 1 (NovaTech)
├── cenario-1/                    — entregáveis do Cenário 1
│   ├── exercicio-1.1/            — análise técnica de viabilidade
│   ├── exercicio-1.2/            — protótipo de system prompt
│   └── exercicio-1.3/            — pipeline de RAG em Python
├── cenario-2/                    — entregáveis do Cenário 2
│   ├── material-pratica/         — enunciados e anexos da Prática 2
│   ├── correcao-pratica/         — gabaritos de avaliação por papel
│   ├── novatech-assistant/       — starter repo com modificações aplicadas
│   ├── exercicio-2.1/            — MCP servers (mapeamento, config, evidências, riscos)
│   ├── exercicio-2.2/            — SDD: tasks.md + código + revisão crítica
│   └── exercicio-2.3/            — estratégia de skills + SKILL.md Foundation
└── .claude/
    └── skills/                   — skills locais que apoiam o trabalho
        ├── novatech-context/
        ├── rag-viability-analysis/
        └── devils-advocate-review/
```

---

## O caso-âncora — NovaTech

Empresa fictícia de logística, 1.200 funcionários, documentação fragmentada em SharePoint, Confluence e planilhas. Equipe de atendimento gasta doze minutos por chamado procurando informação; a meta é dois.

A DB1 foi contratada para construir um assistente de IA que responda em linguagem natural, citando a fonte. Os exercícios giram em torno desse cenário e dos cinco documentos seminais — POL-001, PROC-042, PROC-042-v2, SLA-2024 e o FAQ-Atendimento — que carregam, propositadamente, contradições e armadilhas que precisam ser identificadas no caminho.

---

## Skills

Três skills foram escritas para acompanhar o trabalho. Vivem em `.claude/skills/` e seguem com o repositório.

- **`novatech-context`** — carrega o cenário, a localização dos arquivos e o catálogo das armadilhas plantadas nos documentos.
- **`rag-viability-analysis`** — estrutura a análise de viabilidade técnica de um projeto de RAG; usada no Exercício 1.1.
- **`devils-advocate-review`** — crítica adversarial para fechar o ciclo v1 → v2 que todo exercício exige.

Convivem com o repositório porque a trilha também ensina a tratá-las como artefato — não como ornamento.

---

## Ferramentas

Claude · Claude Code · GitHub Copilot. Sem dados de cliente em qualquer entregável.

---

## Notas

Este repositório é pessoal e tem objetivo formativo. Cada commit é menos uma demonstração e mais um movimento de leitura: tentativa, crítica, revisão.

> _"Trabalho honesto não pede aplauso — pede atenção."_

— Lucas Costa · DB1 · 2026
