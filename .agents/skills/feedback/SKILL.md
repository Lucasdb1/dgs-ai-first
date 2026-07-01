---
name: feedback
description: Esta é a documentação autoritativa do domínio Feedback de Respostas do novatech-assistant — o domínio que captura a avaliação binária do atendente da NovaTech (útil / não útil) sobre uma resposta específica já gerada pelo domínio de consulta do assistente (query-assistant), com um comentário livre opcional, para alimentar o painel de métricas de qualidade e orientar futuras iterações do prompt do assistente. Carregar esta skill para qualquer tarefa envolvendo o endpoint de feedback, o cartão de avaliação exibido junto à resposta do bot no Microsoft Teams (feedback-card), a referência entre um registro de feedback e a resposta do query-assistant à qual ele se refere, os dados de feedback consumidos pelo painel web de métricas, ou o contrato técnico ainda não escrito deste endpoint (rota, schema de requisição/resposta).
metadata:
  author: clovis-cli
  type: domain-skill
---

## Visão geral do domínio

O `novatech-assistant` é o assistente de IA de atendimento da NovaTech (empresa fictícia de logística) usado pelos atendentes do time de suporte para consultar procedimentos, SLAs e regras de frete sem abrir manualmente a documentação interna. O domínio de consulta (`query-assistant`) responde às perguntas do atendente citando sempre a fonte documental usada.

O domínio Feedback de Respostas existe para capturar, depois que o atendente recebe uma dessas respostas, a avaliação desse atendente sobre a qualidade da resposta recebida. O propósito de negócio dessa captura é duplo: alimentar indicadores de qualidade exibidos no painel de métricas interno (consumido por Delivery Manager, Tech Lead e Product Specialist) e servir de insumo para iterações futuras do prompt do assistente.

Este domínio depende diretamente do domínio de consulta (`query-assistant`): um registro de feedback só existe em referência a uma resposta que esse outro domínio já gerou — não há feedback "solto", desvinculado de uma resposta específica. Por sua vez, este domínio é consumido por dois outros domínios: a integração com o Microsoft Teams (que exibe o mecanismo de avaliação ao atendente, embutido junto à resposta recebida no chat, e carrega a referência à resposta avaliada — ver "Como o feedback referencia a resposta avaliada" abaixo) e o painel web de métricas (que agrega os registros de feedback capturados aqui em indicadores de qualidade). Nenhuma regra de negócio desses dois domínios consumidores pertence a esta skill — em particular, a forma como os indicadores são agregados e exibidos é responsabilidade do domínio do painel web, não deste.

## Avaliação capturada

A avaliação que o atendente registra sobre uma resposta do assistente é binária: **útil** ou **não útil**. Junto a essa avaliação binária, o atendente pode incluir um **comentário livre, opcional** — texto sem estrutura ou categorização predefinida, usado como contexto qualitativo adicional para quem revisar o feedback (não há um conjunto fechado de categorias de problema, como "resposta errada" ou "resposta desatualizada", a ser selecionado; o comentário é texto livre).

Nenhuma fonte investigada define um limite de tamanho para esse comentário nem regras adicionais de validação sobre seu conteúdo — trate isso como um detalhe de especificação ainda não escrito no módulo (ver "Contrato técnico do endpoint" abaixo), não como ausência de restrição por decisão de negócio.

## Como o feedback referencia a resposta avaliada

Um registro de feedback sempre se refere a uma resposta específica já gerada pelo domínio de consulta. O contrato de resposta do domínio de consulta (`answer`, `source_document`, `confidence_low`) não inclui, ele mesmo, nenhum identificador de consulta ou de resposta — a referência à resposta avaliada não viaja nesse contrato HTTP.

Esse identificador existe fora do contrato HTTP documentado do domínio de consulta: ele é carregado como metadado interno do cartão de avaliação exibido no Microsoft Teams (mantido pelo domínio de integração com o Teams), que acompanha a resposta apresentada ao atendente no chat e é devolvido junto com a avaliação quando o atendente a submete. O mecanismo exato desse metadado (o que ele contém, como é gerado e transportado pelo bot) é responsabilidade do domínio de integração com o Teams, a ser detalhado quando esse domínio for especificado — não pertence a esta skill.

## Contrato técnico do endpoint

Nenhuma fonte investigada especifica, para o endpoint de feedback, a rota HTTP, o método, o schema exato da requisição ou o schema da resposta — os artefatos que definiriam isso (`requirements.md`, `plan.md` e `tasks.md` do módulo, o handler e o validador do endpoint) existem apenas como itens de estrutura de diretório, sem conteúdo escrito. Isso é diferente do domínio de consulta, cujo contrato (`POST /api/query`) foi de fato especificado em tasks de desenvolvimento aprovadas.

O que já está definido, e deve orientar quem escrever esses artefatos: o corpo da requisição transporta, no mínimo, a avaliação binária (útil / não útil), o comentário livre opcional, e a referência à resposta avaliada (o metadado descrito na seção anterior). A definição literal de nomes de campo, rota e schema de resposta continua sendo trabalho de especificação ainda não realizado para este módulo, não uma regra de negócio em aberto.

## Fluxo conhecido

O único fluxo que as fontes sustentam, em alto nível, é:

1. o atendente recebe uma resposta do domínio de consulta, formatada como mensagem no chat do Microsoft Teams, acompanhada do cartão de avaliação e do metadado que referencia essa resposta;
2. o atendente registra sua avaliação (útil ou não útil) no cartão, com um comentário livre opcional;
3. essa avaliação, junto com a referência à resposta avaliada, é enviada a este domínio, que a persiste para consumo posterior pelo painel de métricas.

Os detalhes de transporte de cada um desses passos (o schema exato da submissão, a rota do endpoint) não estão especificados em nenhuma fonte (ver "Contrato técnico do endpoint").

## Entidades e dados

- **Registro de feedback** — a única entidade própria deste domínio. Contém: a avaliação binária (útil / não útil), um comentário livre opcional, e uma referência à resposta avaliada (o metadado originado no cartão de avaliação do Teams — ver "Como o feedback referencia a resposta avaliada"). A definição literal de campos (nomes, tipos exatos) ainda não foi escrita em nenhum artefato do módulo.
- **Resposta avaliada** — não é uma entidade própria deste domínio; é a resposta do domínio de consulta (`answer` + `source_document` + `confidence_low` opcional) à qual um registro de feedback se refere.

## Restrições e validações

- A avaliação é obrigatória e binária: útil ou não útil.
- O comentário é opcional e de texto livre, sem categorização predefinida.
- Nenhum limite de tamanho ou regra adicional de validação sobre o comentário está evidenciado — ainda não especificado nos artefatos do módulo (ver "Contrato técnico do endpoint").

## Integrações e dependências externas

- **Microsoft Teams (via o domínio de integração com Teams)** — é o único canal evidenciado por onde um atendente registra feedback hoje: o mecanismo de avaliação é exibido como parte da mensagem de resposta dentro do chat, através de um componente dedicado (cartão de avaliação) mantido pelo domínio de integração com o Teams, que também carrega o metadado de referência à resposta avaliada. Nenhuma outra fonte de feedback (por exemplo, via o painel web diretamente) está evidenciada.
- Não há dependência de nenhum serviço de IA (Azure OpenAI, Azure AI Search) neste domínio — ao contrário dos domínios de ingestão e de consulta, capturar e persistir uma avaliação não envolve geração de embeddings nem chamadas a um modelo de linguagem.

## Manutenção da skill

Esta skill é a fonte autoritativa do domínio Feedback de Respostas. Sempre que o comportamento deste domínio mudar de propósito — em particular quando o contrato técnico do endpoint (hoje não especificado) for escrito, ou quando o mecanismo de referência à resposta avaliada, mantido pelo domínio de integração com o Teams, for detalhado — esta skill deve ser atualizada na mesma alteração que define esse comportamento, para permanecer fiel ao que o domínio efetivamente faz.

Drift entre esta skill e a implementação nunca deve ser resolvido silenciosamente. Distinga dois casos: quando a mudança no código foi deliberada e a intenção por trás dela é conhecida, atualize esta skill para refletir a nova intenção. Quando a skill e a implementação divergem semanticamente e não há decisão registrada indicando qual das duas reflete o comportamento pretendido, trate a divergência como um gap e escale para decisão humana — nunca ajuste a skill (nem a implementação) por conta própria para eliminar a divergência.
