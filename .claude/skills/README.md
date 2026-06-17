# Skills do Projeto — DGS AI First

Skills versionadas no repositório. Acompanham o código, são lidas por quem clonar, e fazem parte do entregável da trilha.

| Skill | Para que serve |
| :--- | :--- |
| [novatech-context](novatech-context/SKILL.md) | Carrega o caso NovaTech: cenário, localização dos arquivos e o catálogo de armadilhas plantadas nos documentos. Invocada no início de qualquer exercício dos Cenários 1, 2 e 3. |
| [rag-viability-analysis](rag-viability-analysis/SKILL.md) | Estrutura uma análise de viabilidade técnica de RAG no formato de quatro seções que os avaliadores esperam. Usada no **Exercício 1.1**. |
| [devils-advocate-review](devils-advocate-review/SKILL.md) | Crítica adversarial para fechar o ciclo v1 → v2 que todo exercício exige. Lê, caça pontos fracos e devolve a revisão. |

## Como invocar

Dentro do Claude Code, basta descrever o que se quer — o Claude escolhe a skill pelo campo `description`. Exemplos:

- *"Vamos preparar o entregável do exercício 1.1"* → ativa `rag-viability-analysis`, que por sua vez referencia `novatech-context`.
- *"Critica essa v1 como revisor sênior"* → ativa `devils-advocate-review`.

As skills se cruzam entre si com links no formato `[[nome-da-skill]]`.

## Por que skills locais (e não pessoais)

Estas skills são **do projeto** (`.claude/skills/`), não do usuário (`~/.claude/skills/`). A escolha tem três razões:

1. Quem clonar o repositório recebe as mesmas skills, sem configuração adicional.
2. As próprias skills são entregáveis — demonstram domínio do tópico 8 da trilha ("Skills").
3. Evoluem junto com o material do caso, em `material-pratica-1/`.

---

> _Skills não são ornamento. São o sotaque do projeto._
