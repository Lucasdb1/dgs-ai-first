---
name: skill-authoring-hierarchy
description: Convenção de organização das skills reutilizáveis do novatech-assistant em 3 níveis — Foundation (convenções globais), Domain (padrões por camada/tecnologia) e Artifact (receitas de geração pontual) — sob `/skills/{foundation,domain,artifact}/`. Carregar ao criar, classificar ou revisar uma nova skill técnica ou de domínio do novatech-assistant, ao decidir em que nível/pasta uma skill deve viver, ou ao escrever o conteúdo de um SKILL.md para esse projeto.
metadata:
  author: clovis-cli
  type: technical-skill
---

## O padrão e o problema que resolve

Skills são artefatos `.md` estruturados que encapsulam como gerar um tipo específico de output — endpoint Azure Functions com padrão RAG, teste de integração, componente React — para que Claude e GitHub Copilot não recebam essa orientação repetida (e potencialmente inconsistente) a cada prompt. Sem essa camada, cada um dos 5 módulos do `novatech-assistant` (`ingestion-pipeline`, `query-assistant`, `feedback`, `teams-bot`, `web-dashboard`) tende a reinventar convenções de erro, de teste e de estrutura de forma divergente. As skills vivem em `cenario-2/novatech-assistant/skills/` (Anexo C do Cenário 2) e são um sistema de skills distinto do usado por este próprio fluxo de preparação — ver nota na seção "Estrutura de arquivo" abaixo.

## Os 3 níveis

### Foundation — convenções globais
Aplicam-se a todo o código do projeto, independente de camada ou tecnologia. Exemplos já recortados no Anexo C: `typescript-conventions.md`, `error-handling.md`, `project-structure.md`. Vivem em `skills/foundation/`.

### Domain — padrões por camada/tecnologia
Especificam como uma camada ou integração específica deve ser implementada, reutilizados por múltiplos artefatos daquela camada. Exemplos: `azure-functions-endpoint.md`, `azure-ai-search-integration.md`, `react-components.md`, `testing-patterns.md`. Vivem em `skills/domain/`.

### Artifact — receitas de geração pontual
Passo a passo ponta a ponta para produzir um tipo de artefato completo e repetido no projeto. Exemplos: `create-rag-endpoint.md`, `create-integration-test.md`, `create-react-card.md`. Vivem em `skills/artifact/`.

## Regra de decisão de nível

Ao criar uma skill nova, decida o nível perguntando, nesta ordem:

1. É uma convenção geral, sem amarração a uma tecnologia ou camada específica (ex.: como tratar erros, como nomear pastas)? → **Foundation**.
2. É um padrão específico de uma tecnologia/camada usada no projeto, reutilizado por mais de um artefato daquela camada (ex.: como todo endpoint Azure Functions deve validar input)? → **Domain**.
3. É uma receita completa, do início ao fim, para gerar um artefato específico e repetido (ex.: "criar um novo endpoint RAG")? → **Artifact**.

Uma skill Artifact normalmente referencia e compõe skills Domain e Foundation em vez de repetir as regras — não duplique conteúdo de um nível no outro.

## Estrutura de arquivo e frontmatter

Cada skill é um arquivo `.md` independente, nomeado com o slug da skill (kebab-case), direto sob `skills/<nivel>/` — não há uma subpasta por skill (ex.: `skills/foundation/error-handling.md`, não `skills/foundation/error-handling/SKILL.md`). Frontmatter mínimo, no mesmo formato já usado pelas skills nativas deste repositório em `.claude/skills/*/SKILL.md`:

```markdown
---
name: error-handling
description: <frase de ativação que um agente reconheceria — quando carregar esta skill>
---
```

**Não confundir com `.agents/skills/<slug>/SKILL.md`:** esse é o formato usado pelo fluxo de preparação Clovis para as skills técnicas e de domínio deste próprio processo de descoberta (com `metadata.type` e `metadata.author`), consumido por este agente durante a Etapa 2. A hierarquia Foundation → Domain → Artifact descrita aqui é um sistema separado, consumido por Copilot/Claude durante a implementação do `novatech-assistant` em `cenario-2/novatech-assistant/skills/`. Os dois convivem no mesmo repositório sem conflito porque atendem consumidores e fases diferentes.

## Conteúdo obrigatório de uma skill Foundation

Uma skill Foundation precisa ser prescritiva e concreta, não abstrata: contexto, regras prescritivas, exemplos de código reais em DO/DON'T, e anti-padrões específicos — os erros que o GitHub Copilot realmente geraria sem essa orientação (ex.: `as any`, `console.log` em vez do logger `pino`, `require` dinâmico em código TypeScript estrito), não anti-padrões genéricos de manual. Skills Domain e Artifact seguem a mesma exigência de concretude, adaptada ao seu nível — uma skill Artifact deve ser executável como receita, não uma descrição de alto nível do que o artefato faz.

## Criação e consumo multi-papel

A árvore de skills não é uma responsabilidade só do time de desenvolvimento. Para cada skill, registre nome, descrição, quem cria (o papel responsável pela convenção) e quem consome (papel + agente):

| Exemplo de skill | Quem cria | Quem consome |
|---|---|---|
| `error-handling.md` (Foundation) | Tech Lead | Dev (via Copilot), QA (via Claude) |
| `testing-patterns.md` (Domain) | QA | Dev (via Copilot) |
| `create-rag-endpoint.md` (Artifact) | Dev Sênior | Dev (via Copilot) |
| skill de template de spec (Domain, ainda não recortada no Anexo C) | Product Specialist | Product Specialist e Tech Lead (via Claude, ao redigir `requirements.md`) |

Uma árvore em que toda skill é criada e consumida só por devs é um sinal de que o exercício não considerou o time inteiro (Product Specialist, QA, Delivery Manager também criam e consomem skills).

## Ferramentas e artefatos envolvidos

- `cenario-2/novatech-assistant/skills/{foundation,domain,artifact}/` — a árvore real de skills do projeto, hoje com 10 arquivos placeholder (3 Foundation, 4 Domain, 3 Artifact) ainda vazios, a preencher pelos exercícios do Cenário 2/3.
- `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` — origem da árvore e da convenção de nomenclatura (seção "Convenções de organização").
- `.mcp/mcp.json` (server `filesystem-code`) — o agente só tem permissão de escrita em `./skills` através desse server; ver [[mcp-server-configuration]].

## Armadilhas conhecidas

- **Skills teóricas que ninguém consumiria.** Cada skill precisa corresponder a um artefato que o projeto realmente gera mais de uma vez — não crie uma skill "para completude" da árvore.
- **Anti-padrões genéricos em vez de específicos de LLM/Copilot.** "Não escreva código ruim" não é um anti-padrão útil; "Copilot tende a usar `as any` para silenciar erro de tipo em vez de tipar corretamente" é.
- **Confundir esta hierarquia com o formato `.agents/skills/<slug>/SKILL.md` do fluxo Clovis** — são convenções de nomenclatura e consumidor diferentes (ver "Estrutura de arquivo" acima).
- **Pular Foundation e escrever direto uma skill Artifact.** Sem as convenções de base (error handling, estrutura de projeto), a receita de geração pontual não tem o que referenciar e acaba reimplementando regras gerais dentro de um escopo que devia ser só a receita.

## Manutenção (anti-drift)

Atualize esta skill sempre que `cenario-2/material-pratica/anexo-c-estrutura-repositorio.md` mudar a árvore de skills, sempre que os arquivos placeholder em `cenario-2/novatech-assistant/skills/` forem preenchidos e revelarem uma convenção de frontmatter ou de conteúdo diferente da descrita aqui, ou sempre que uma nova skill for adicionada a um dos 3 níveis e mudar o exemplo canônico citado.
