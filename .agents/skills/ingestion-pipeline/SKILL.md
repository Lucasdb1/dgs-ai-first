---
name: ingestion-pipeline
description: Esta é a documentação autoritativa do domínio Pipeline de Ingestão de Documentos do novatech-assistant — o pipeline que transforma a documentação de negócio da NovaTech (políticas, procedimentos, tabelas de SLA e FAQ) em chunks indexados e pesquisáveis para o assistente de atendimento. Cobre a extração de texto de PDFs (incluindo tabelas complexas e documentos escaneados via OCR), páginas de wiki e planilhas; a estratégia de chunking (perfis de chunk padrão e de tabela, fronteiras semânticas, overlap, conversão de tabela em prosa); a geração de embeddings; a indexação no Azure AI Search; e o metadado de vigência (documento ativo/substituído, versão) usado para lidar com documentos obsoletos, duplicados ou com versões contraditórias. Carregar esta skill para qualquer tarefa envolvendo extração, chunking, embeddings, indexação, deduplicação, versionamento de documentos ou o corpus de entrada do assistente NovaTech.
metadata:
  author: clovis-cli
  type: domain-skill
---

## Visão geral do domínio

O Pipeline de Ingestão de Documentos é a base de dados do `novatech-assistant`: transforma a documentação de negócio da NovaTech (políticas, procedimentos operacionais, tabelas de SLA e o FAQ do time de atendimento) em chunks indexados e pesquisáveis por similaridade semântica. Nenhum outro domínio do assistente funciona sem este — é o domínio de ingestão que produz e mantém o índice de busca consumido pelo domínio de Consulta do Assistente (RAG Query) a cada pergunta de um atendente.

A documentação de origem vive hoje em três sistemas com formatos distintos — um SharePoint corporativo (PDFs e DOCX), uma wiki corporativo (hoje Confluence, HTML/wiki) e uma pasta de rede com planilhas de referência (XLSX) — atualizados mensalmente por três áreas diferentes (Operações, Compliance, Comercial) sem processo unificado de revisão. Essa fragmentação é a causa raiz de duas características que o pipeline precisa tratar como regra de negócio, não como exceção: documentos que se contradizem entre versões, e documentos obsoletos que continuam presentes nas fontes de origem.

Toda a lógica de negócio descrita abaixo representa o comportamento **pretendido** deste domínio na versão de produção do assistente (Azure AI Search + Azure OpenAI). A evidência mais concreta e validada disponível hoje é um protótipo funcional construído com ferramentas open-source (ChromaDB + sentence-transformers) que implementou e testou a estratégia de extração, chunking e indexação — essa estratégia foi validada e decidida como base para a implementação de produção. Nenhum código de produção deste domínio foi escrito ainda (a estrutura de módulos existe apenas como blueprint vazio); onde a especificação e o protótipo divergem entre si, ou onde nenhuma fonte resolve um ponto, isso é sinalizado explicitamente abaixo em vez de presumido.

## Corpus de entrada e ciclo de atualização

- O corpus bruto de origem tem aproximadamente **1.250 fontes** (documentos de SharePoint, páginas de wiki e planilhas).
- Após um processo de deduplicação e limpeza (conduzido como atividade de discovery, anterior à operação contínua do pipeline), o corpus consolidado tem **847 documentos válidos**. Desse total:
  - **12 documentos** têm contradições pendentes de resolução pelo Compliance da NovaTech (ver "Documentos com contradições e vigência" abaixo).
  - **63 documentos** foram descartados por obsolescência.
  - **~340 documentos** foram eliminados como duplicatas ou redundâncias.
- A deduplicação e a remoção de obsoletos acima descrevem o estado do corpus **na consolidação inicial** — nenhuma fonte investigada define um mecanismo pelo qual o pipeline detecta automaticamente, de forma contínua, novas duplicatas ou documentos obsoletos nas atualizações mensais seguintes. Presumir que essa detecção contínua existe seria inventar uma capacidade não evidenciada; hoje o pipeline deve ser entendido como um consumidor do corpus já curado, com a curadoria contínua (dedup/obsolescência) fora do escopo evidenciado deste domínio.
- Requisito de atualização: um novo documento publicado pelas áreas responsáveis deve estar disponível para consulta pelo assistente em **até 24 horas** após a publicação.

## Fluxo de processamento de um documento

Um documento-fonte percorre, nesta ordem, as seguintes etapas até se tornar pesquisável:

1. **Extração** — o texto é extraído da fonte original (PDF, PDF escaneado, página de wiki ou planilha), com tratamento específico por tipo de fonte (ver [`references/extracao-por-tipo-de-fonte.md`](./references/extracao-por-tipo-de-fonte.md)).
2. **Chunking** — o texto extraído é dividido em chunks (unidades indexáveis) segundo a estratégia de chunking do domínio (ver [`references/estrategia-de-chunking.md`](./references/estrategia-de-chunking.md) para o detalhamento completo).
3. **Geração de embeddings** — cada chunk é convertido em um vetor de embedding.
4. **Indexação** — o chunk, seu vetor e seus metadados (documento de origem, seção, status de vigência, tipo de fonte) são gravados no índice de busca consumido pelo domínio de Consulta do Assistente.

## Regras de negócio

### Extração por tipo de fonte

A extração ingênua (conversão direta para texto puro) degrada a qualidade de resposta do assistente de forma sistemática — tabelas perdem a associação linha-coluna, OCR de baixa qualidade introduz ruído, links de wiki tornam-se texto solto, e planilhas com fórmulas congelam valores desatualizados. O domínio trata cada tipo de fonte com uma estratégia de extração específica; o detalhamento completo — desafio, impacto na qualidade da resposta e estratégia — para PDFs com tabelas complexas, documentos escaneados, páginas de wiki e planilhas está em [`references/extracao-por-tipo-de-fonte.md`](./references/extracao-por-tipo-de-fonte.md).

Regra central que atravessa todos os tipos de fonte: uma tabela extraída **nunca é descartada nem tem sua estrutura linha-coluna quebrada** durante a extração — ela é preservada como unidade estruturada (Markdown ou equivalente) para ser tratada como chunk único na etapa de chunking.

Para documentos escaneados, a extração passa por uma etapa de validação pós-OCR contra o vocabulário de domínio esperado (siglas e termos normativos do setor de logística). Chunks originados de um trecho com baixa confiança de OCR são **excluídos do índice principal** — não ficam pesquisáveis pelo domínio de Consulta do Assistente até que passem por revisão humana. Isso significa que informação com erro de OCR não gera respostas incorretas por propagação de ruído, ao custo de, até a revisão, essa informação não estar disponível ao assistente.

### Estratégia de chunking

O domínio usa dois perfis de chunk — **padrão** (texto narrativo) e **tabela** (qualquer tabela estruturada) — com regras de fronteira semântica, overlap e uma técnica de conversão de tabela em prosa que corrige a baixa qualidade de embedding observada em conteúdo tabular. Esta estratégia foi validada em protótipo funcional (5 de 5 perguntas de teste recuperaram os chunks corretos) e é a estratégia decidida para a implementação de produção. O detalhamento completo — tamanhos-alvo, regras de fronteira, overlap, detecção de tabela e a técnica de conversão para prosa — está em [`references/estrategia-de-chunking.md`](./references/estrategia-de-chunking.md).

Resumo dos dois perfis:

| Perfil | Tamanho-alvo | Regra de fronteira |
|---|---|---|
| **Padrão** | até 400 palavras (a fonte estima ~533 tokens) | Dividido em fronteiras semânticas (headings H2/H3), nunca no meio de frase ou parágrafo |
| **Tabela** | tabela inteira, sem corte; cap prático de 1.500 palavras (~2.000 tokens) | Uma tabela nunca é dividida — se ultrapassa o perfil padrão, o perfil tabela se aplica automaticamente |

Estes são os tamanhos de chunk autoritativos para a ingestão — o perfil padrão de ~533 tokens e o teto de ~2.000 tokens do perfil tabela não são um valor provisório, e não devem ser aumentados para se aproximar de nenhuma suposição de tamanho de chunk feita em outro domínio. O orçamento de contexto documentado no domínio de Consulta do Assistente assumia, antes desta decisão, chunks de aproximadamente 1.500 tokens cada (até 5 chunks ≈ 8.000 tokens) — essa suposição está desatualizada em relação aos tamanhos de chunk decididos aqui e o cálculo de orçamento de contexto daquele domínio precisa ser reaberto para refletir chunks menores (o que também implica caber mais chunks dentro do mesmo orçamento de ~8.000 tokens). Essa atualização pertence à skill do domínio de Consulta do Assistente, não a esta.

### Geração de embeddings

- Cada chunk é convertido em um vetor de embedding de **1.536 dimensões**, usando o mesmo modelo usado para embeddar a pergunta do atendente no domínio de Consulta do Assistente (Azure OpenAI `text-embedding-ada-002`). Essa consistência de modelo entre ingestão e consulta é obrigatória — buscar por similaridade só funciona se pergunta e chunk forem embeddados no mesmo espaço vetorial.
- Chunks do perfil tabela recebem, antes de embeddados, uma representação textual em prosa prependida ao conteúdo original (ver seção própria em [`references/estrategia-de-chunking.md`](./references/estrategia-de-chunking.md)) — sem essa conversão, modelos de embedding não capturam bem a estrutura de linhas e colunas de uma tabela Markdown, e o chunk de tabela fica sub-ranqueado na busca por similaridade mesmo quando é o chunk correto.

### Metadados por chunk

Todo chunk indexado carrega, além do texto e do vetor de embedding, os seguintes metadados, herdados do documento de origem:

| Metadado | Valores | Significado |
|---|---|---|
| `doc_id` | identificador do documento de origem (ex.: o código do procedimento ou da política) | liga o chunk ao documento-fonte; é o valor devolvido como fonte citada nas respostas do assistente |
| `source_type` | `normative` \| `informal` | distingue documentação normativa (políticas, procedimentos, SLA) de fontes informais não validadas (o FAQ do time de atendimento) |
| `status` | `active` \| `superseded` | metadado de vigência: identifica se o documento é a versão vigente ou uma versão substituída por outra mais recente |
| `version` | identificador de versão do documento | usado junto com `status`/`superseded_by` para reconstruir o histórico de versões de um mesmo documento |
| `superseded_by` | `doc_id` da versão que substitui este documento (apenas quando `status = superseded`) | liga explicitamente a versão antiga à versão vigente |
| `validated` | booleano | `false` para fontes informais nunca revisadas formalmente (ex.: o FAQ); usado a jusante para tratar essas fontes com menor confiança |
| `section` | cabeçalho/seção de origem dentro do documento | preserva a localização do trecho dentro do documento original |
| `chunk_type` | `standard` \| `table` | identifica qual perfil de chunking gerou o chunk |

Estes metadados são o mecanismo concreto pelo qual este domínio expõe o "metadado de vigência" decidido para lidar com documentos contraditórios: o domínio de Consulta do Assistente lê `status`, `version` e `superseded_by` para instruir o modelo a priorizar a versão mais recente quando chunks de duas versões do mesmo documento aparecem juntos no contexto — a lógica de priorização em si (como o domínio de consulta usa esse metadado na busca ou na montagem do prompt) não pertence a este domínio.

### Documentos com contradições e vigência

Quando duas versões de um mesmo documento normativo coexistem na base (o caso concreto conhecido: um procedimento de frete especial, com uma versão original e uma versão revisada, que altera os multiplicadores regionais usados no cálculo), a regra de negócio é:

- **Nenhuma versão é excluída do índice.** A versão substituída (`status: superseded`) permanece pesquisável — ela pode ainda ser necessária para consultas sobre casos abertos antes da transição de vigência da nova versão.
- A versão vigente recebe `status: active`; a versão substituída recebe `status: superseded` e é ligada à vigente via `superseded_by`.
- Os valores de `status`, `version` e `superseded_by` de um documento **não são inferidos automaticamente pelo pipeline** — são metadados de entrada, fornecidos manualmente pela área responsável pelo documento (Operações, Compliance ou Comercial) ou pelo próprio Compliance, no momento em que o documento é publicado ou atualizado. O pipeline consome esse metadado ao indexar; ele não compara versões, não detecta substituição por conteúdo, e não decide por conta própria quando um documento se tornou obsoleto ou foi substituído por outro.
- Dos 847 documentos válidos do corpus, **12** têm contradições ainda pendentes de resolução pelo Compliance da NovaTech: para esses 12, a área responsável ainda não forneceu o metadado de vigência que determinaria qual versão é a `active` e qual é a `superseded`. Enquanto essa determinação manual não for feita, o pipeline não tem base para atribuir esses valores — os documentos permanecem no índice sem a distinção de vigência resolvida entre si, o que é precisamente o estado que a resolução do Compliance encerra.

### Exclusão de fontes dinâmicas do índice

Nem todo dado de origem deve ser indexado como chunk estático. Critério de decisão:

- **Indexar como chunk** quando o valor extraído é estável entre as atualizações mensais e não depende de variáveis externas dinâmicas (ex.: uma tabela de SLA, uma regra de prazo calculada).
- **Excluir da indexação** quando o dado depende de uma variável que muda com frequência maior que o ciclo de atualização do pipeline, ou de uma entrada fornecida em tempo de consulta. O caso concreto conhecido é o valor-base do frete especial, que vem de uma planilha comercial atualizada mensalmente de forma independente da documentação normativa — indexar esse valor como chunk estático arriscaria devolver um valor desatualizado. Este domínio decide que esse tipo de dado **não deve ser transformado em chunk**; como esse valor passa a ser obtido em tempo de consulta (ex.: chamada de função dedicada) é uma decisão do domínio consumidor, não deste.

## Entidades e dados

- **Documento-fonte** — um documento de negócio da NovaTech antes do processamento (política, procedimento, tabela de SLA ou FAQ), identificado por `doc_id`, com metadados de `source_type`, `status`, `version` e, quando aplicável, `superseded_by`.
- **Chunk** — a unidade indexável e pesquisável produzida a partir de um documento-fonte: texto (bruto, ou com prosa prependida no caso de tabelas), `section`, `chunk_type` e os metadados herdados do documento de origem (ver "Metadados por chunk").
- **Índice de busca** — a coleção de chunks com seus vetores de embedding e metadados, mantida no Azure AI Search; é o artefato final produzido por este domínio e consumido inteiramente pelo domínio de Consulta do Assistente (busca por similaridade semântica, com metadados usados para priorização de versão e para distinguir fontes normativas de informais).

## Restrições e validações

- Chunk padrão: até 400 palavras por chunk (a fonte que validou este perfil estima ~533 tokens em português).
- Chunk de tabela: tabela inteira, nunca dividida; cap prático de 1.500 palavras (~2.000 tokens).
- Divisão em chunks ocorre apenas em fronteiras semânticas (headings H2/H3) — divisão por contagem cega de caracteres é rejeitada.
- Overlap de 40 palavras (~10% de um chunk padrão) entre chunks padrão consecutivos; chunks de tabela não recebem overlap.
- Vetor de embedding: 1.536 dimensões, mesmo modelo usado para embeddar a pergunta do atendente no domínio de Consulta do Assistente.
- Uma tabela extraída nunca tem sua estrutura linha-coluna quebrada durante a extração.
- Chunks originados de um trecho com baixa confiança de OCR são excluídos do índice principal até revisão humana.
- Documentos com `status: superseded` permanecem pesquisáveis — nunca são excluídos do índice.
- Dado de origem cujo valor depende de variável externa dinâmica (atualizada fora do ciclo do pipeline) não é transformado em chunk estático.
- Novo documento publicado deve estar disponível para consulta em até 24 horas após a publicação.

## Integrações e dependências externas

- **Azure AI Search** — hospeda o índice de busca produzido por este domínio; é o destino final da indexação e a única forma pela qual o domínio de Consulta do Assistente acessa os documentos processados.
- **Azure OpenAI** (`text-embedding-ada-002`) — gera os vetores de embedding de 1.536 dimensões para cada chunk indexado.
- **SharePoint corporativo** — sistema de origem dos documentos em PDF e DOCX (políticas, procedimentos, tabelas de SLA).
- **Wiki corporativo** (hoje Confluence) — sistema de origem das páginas de wiki; a extração é feita via API do sistema de wiki, não por scraping de HTML, para poder resolver links internos durante a ingestão.
- **Pasta de rede com planilhas** — sistema de origem das planilhas de referência (XLSX) usadas em cálculos como o de frete especial.

Este domínio não depende de nenhum outro domínio do assistente — é a base de dados sobre a qual o domínio de Consulta do Assistente é construído.

## Manutenção da skill

Esta skill é a fonte autoritativa do domínio Pipeline de Ingestão de Documentos. Sempre que o comportamento deste domínio mudar de propósito — um novo tipo de fonte suportado, uma mudança nos perfis de chunking, um novo campo de metadado, uma definição concreta para os gaps registrados acima, entre outras — esta skill (e suas referências) deve ser atualizada na mesma alteração que muda o comportamento, para permanecer fiel ao que o domínio efetivamente faz.

Drift entre esta skill e a implementação nunca deve ser resolvido silenciosamente. Distinga dois casos: quando a mudança no código foi deliberada e a intenção por trás dela é conhecida, atualize esta skill para refletir a nova intenção. Quando a skill e a implementação divergem semanticamente e não há decisão registrada indicando qual das duas reflete o comportamento pretendido, trate a divergência como um gap e escale para decisão humana — nunca ajuste a skill (nem a implementação) por conta própria para eliminar a divergência.
