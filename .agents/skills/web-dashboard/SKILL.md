---
name: web-dashboard
description: Esta é a documentação autoritativa do domínio Painel Web de Métricas do novatech-assistant — o painel interno em React que dá visibilidade a Delivery Manager, Tech Lead e Product Specialist sobre o uso do assistente de atendimento da NovaTech, mostrando volume de consultas, histórico de consultas já respondidas pelo domínio de consulta (query-assistant) e indicadores de qualidade agregados a partir das avaliações capturadas pelo domínio de feedback. Carregar esta skill para qualquer tarefa envolvendo o painel web interno, o dashboard de métricas e histórico, os componentes React do painel (páginas, cards, App.tsx), a agregação de indicadores de qualidade a partir de registros de feedback, a exibição de histórico de consultas, ou os pontos ainda em aberto sobre a origem dos dados de histórico e sobre quais métricas concretas o painel deve exibir.
metadata:
  author: clovis-cli
  type: domain-skill
---

## Visão geral do domínio

O `novatech-assistant` é o assistente de IA de atendimento da NovaTech (empresa fictícia de logística) usado pelos atendentes do time de suporte para consultar procedimentos, SLAs e regras de frete sem abrir manualmente a documentação interna. A arquitetura do assistente tem 4 componentes: o pipeline de ingestão de documentos, a API de consulta (RAG), a integração com o Microsoft Teams e este domínio — o painel web interno.

O Painel Web de Métricas existe para dar visibilidade interna sobre o uso do assistente: quanto ele está sendo usado, o que foi perguntado e respondido, e se as respostas estão sendo úteis para quem as recebe. Diferente dos demais domínios do assistente, o painel web não participa do fluxo de atendimento em si — ele não recebe perguntas de atendentes nem gera respostas; é uma camada de leitura e relatório sobre dados que outros dois domínios já produziram.

Este domínio depende diretamente de dois outros:
- **`query-assistant`** (domínio de Consulta do Assistente) — fonte do volume e do histórico de consultas exibidos no painel.
- **`feedback`** (domínio de Feedback de Respostas) — fonte dos registros de avaliação (útil / não útil) a partir dos quais o painel calcula indicadores de qualidade.

Nenhum outro domínio depende do painel web — ele é uma folha na cadeia de dependências do sistema, consumido apenas pelos três papéis internos descritos abaixo, nunca por outro domínio do assistente.

## Público e propósito de negócio

O painel é de uso **interno** à equipe do projeto NovaTech, não dos atendentes de suporte nem de clientes externos — é uma ferramenta de gestão e acompanhamento, distinta da interface conversacional do Microsoft Teams usada no dia a dia pelo atendente.

Os papéis identificados como público deste painel são:
- **Delivery Manager** — acompanha o uso do assistente como indicador de adoção e saúde do projeto.
- **Tech Lead** — acompanha volume e histórico como sinal técnico (ex.: picos de uso, padrões de pergunta).
- **Product Specialist** — acompanha os indicadores de qualidade derivados do feedback para orientar decisões de produto e iterações do prompt do assistente.

Nenhuma fonte investigada diferencia o que cada um desses três papéis pode ou não visualizar no painel — não há evidência de controle de acesso por papel, de uma visão restrita para um papel específico, nem de qualquer outro consumidor (atendentes, clientes, papéis externos à equipe do projeto). Trate a ausência de diferenciação de acesso como um ponto em aberto (ver "Pontos em aberto" abaixo), não como a regra de que os três papéis necessariamente veem exatamente os mesmos dados.

## O que o painel exibe

As fontes investigadas sustentam, de forma explícita, exatamente duas categorias de conteúdo para este painel:

1. **Volume de consultas e histórico** — quantidade de consultas feitas ao assistente ao longo do tempo, e uma listagem/histórico das consultas já respondidas pelo domínio `query-assistant`.
2. **Indicadores de qualidade** — métricas agregadas a partir dos registros de feedback (avaliação útil / não útil, ver domínio `feedback`) capturados sobre as respostas do assistente.

Nenhuma fonte investigada vai além dessas duas categorias com valores concretos. Em particular, não há evidência de:
- uma lista fechada de métricas (ex.: taxa de respostas úteis, taxa de baixa confiança, tempo médio de resposta, ranking de documentos mais consultados, distribuição de perguntas por tópico);
- uma fórmula de cálculo para qualquer indicador de qualidade (ex.: como a proporção de avaliações "útil" vs. "não útil" seria expressa — percentual, contagem absoluta, tendência ao longo do tempo);
- uma granularidade temporal (tempo real, diário, semanal) para qualquer métrica ou para o histórico;
- filtros de consulta ao histórico (por atendente, por documento de origem, por período, por avaliação recebida);
- paginação, retenção ou volume máximo de itens exibidos no histórico.

Documentar qualquer um desses detalhes com um valor específico seria inventar uma regra de negócio sem respaldo — por isso este ponto está registrado como gap (ver "Pontos em aberto").

## Dependências entre domínios e dados consumidos

### Dados vindos do domínio `query-assistant`

O painel exibe volume e histórico de consultas que já passaram pelo endpoint de consulta (`POST /api/query`) desse domínio. O contrato de resposta desse endpoint (`answer`, `source_document` sempre presente, `confidence_low` opcional) está documentado na skill do domínio `query-assistant` — este domínio (`web-dashboard`) apenas consome esses dados para fins de exibição agregada e histórica, sem alterar nem validar essa lógica.

Nenhuma fonte investigada — nem a skill do domínio `query-assistant`, nem qualquer material de negócio — documenta a existência de um mecanismo de persistência de um histórico de consultas (um registro gravado a cada chamada ao endpoint, com pergunta, resposta e metadados, disponível para leitura posterior). O contrato hoje documentado para `query-assistant` é síncrono: recebe uma pergunta e devolve uma resposta na mesma requisição, sem menção a gravação de um log de consulta. Isso significa que a fonte de dados que alimentaria o "histórico de consultas" deste painel não está definida em nenhuma fonte — é um ponto em aberto que bloqueia a implementação completa deste domínio (ver "Pontos em aberto").

### Dados vindos do domínio `feedback`

O painel calcula indicadores de qualidade a partir dos registros de feedback (avaliação binária útil / não útil, mais um comentário livre opcional) capturados por esse domínio. A skill do domínio `feedback` já documenta que esses registros são persistidos "para consumo posterior pelo painel de métricas" — ou seja, ao contrário do histórico de consultas, a existência de uma fonte de dados persistida para o feedback está confirmada, mesmo que o schema exato de persistência não esteja detalhado em nenhuma fonte (isso é responsabilidade de especificação do próprio domínio `feedback`, não deste).

A agregação desses registros individuais de feedback em indicadores de qualidade (o cálculo em si) é responsabilidade deste domínio (`web-dashboard`) — não do domínio `feedback`, que apenas captura e persiste a avaliação bruta.

## Entidades e dados

- **Indicador de qualidade agregado** — a única entidade própria deste domínio: o resultado do cálculo feito aqui sobre os registros de feedback capturados pelo domínio `feedback`. Nenhuma fonte define os campos exatos, a fórmula de agregação ou a granularidade temporal desse indicador (ver "O que o painel exibe" e "Pontos em aberto").
- **Registro de consulta (histórico)** — não é uma entidade própria deste domínio nem uma entidade confirmada em nenhuma fonte; é a representação, ainda sem uma origem de dados definida, de uma consulta já respondida pelo domínio `query-assistant` que o painel pretende listar no histórico (ver "Pontos em aberto").
- **Registro de feedback** — não é uma entidade própria deste domínio; é a entidade do domínio `feedback` (avaliação útil/não útil + comentário livre) consumida aqui como insumo para o indicador de qualidade agregado.

## Restrições e validações

Nenhuma fonte investigada define restrições ou validações próprias deste domínio (por exemplo, sobre quem pode acessar o painel, sobre limites de período consultável, ou sobre validação de parâmetros de filtro) — não há evidência de que este domínio exponha uma API própria com contrato de entrada a validar; ele é descrito nas fontes apenas como uma interface de leitura/apresentação.

## Integrações e dependências externas

- **React** — stack de front-end decidida para este domínio (decisão herdada do Cenário 1, reafirmada na estruturação do projeto), a única tecnologia de implementação explicitamente associada ao painel web nas fontes investigadas.
- Este domínio não depende de nenhum serviço de IA (Azure OpenAI, Azure AI Search) — assim como o domínio `feedback`, ler e agregar dados já produzidos por outros domínios não envolve geração de embeddings, busca semântica nem chamadas a um modelo de linguagem.

## Pontos em aberto

Os pontos a seguir foram escalados para decisão humana por não terem respaldo em nenhuma fonte investigada, e por serem ambiguidades que impedem a reimplementação completa deste domínio a partir desta skill:

1. **Origem e persistência do histórico de consultas** — o domínio `query-assistant` não documenta, em nenhuma fonte, a gravação de um log de consultas para leitura posterior; sem isso, não há de onde este painel leria o "histórico de consultas" que lhe é atribuído como responsabilidade. É necessário decidir se `query-assistant` passa a persistir esse histórico, se este domínio (`web-dashboard`) mantém sua própria captura independente, ou se essa captura é tratada como uma capacidade técnica transversal (observabilidade/logging) fora do escopo de regra de negócio de qualquer um dos dois domínios.
2. **Métricas concretas e diferenciação de acesso por papel** — nenhuma fonte define a lista fechada de métricas/indicadores exibidos além de "volume de consultas" e "indicadores de qualidade", nem se Delivery Manager, Tech Lead e Product Specialist têm a mesma visão ou visões diferenciadas dos dados.

Enquanto esses pontos não forem resolvidos por decisão humana, esta skill documenta apenas o que está confirmado (propósito, público, dependências de domínio) e não presume valores para o que está em aberto.

## Manutenção da skill

Esta skill é a fonte autoritativa do domínio Painel Web de Métricas. Sempre que o comportamento deste domínio mudar de propósito — em particular quando os pontos em aberto acima forem resolvidos (origem do histórico de consultas, lista de métricas, controle de acesso por papel), ou quando qualquer outro comportamento evoluir — esta skill deve ser atualizada na mesma alteração que define esse comportamento, para permanecer fiel ao que o domínio efetivamente faz.

Drift entre esta skill e a implementação nunca deve ser resolvido silenciosamente. Distinga dois casos: quando a mudança no código foi deliberada e a intenção por trás dela é conhecida, atualize esta skill para refletir a nova intenção. Quando a skill e a implementação divergem semanticamente e não há decisão registrada indicando qual das duas reflete o comportamento pretendido, trate a divergência como um gap e escale para decisão humana — nunca ajuste a skill (nem a implementação) por conta própria para eliminar a divergência.
