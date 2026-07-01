# Estratégia de chunking

Este documento detalha a estratégia de chunking do domínio Pipeline de Ingestão de Documentos — validada em um protótipo funcional (ChromaDB + sentence-transformers) que indexou os 5 documentos-chave da base de referência da NovaTech e recuperou corretamente os chunks esperados em 5 de 5 perguntas de teste. É a estratégia decidida para a implementação de produção, incluindo os tamanhos de chunk (~533 tokens no perfil padrão, até ~2.000 tokens no perfil tabela), que são autoritativos para este domínio. Faz parte da skill [`ingestion-pipeline`](../SKILL.md) — ver ali a visão geral do domínio e os metadados por chunk.

## Os dois perfis de chunk

A documentação da NovaTech tem dois tipos de conteúdo com necessidades de chunking distintas. Usar um único perfil de tamanho fixo cria um conflito entre o limite de tamanho e a regra de integridade de tabelas — por isso o domínio define dois perfis explícitos:

| Perfil | Tamanho-alvo | Quando se aplica |
|---|---|---|
| **Padrão** | até 400 palavras (a fonte que validou este perfil estima ~533 tokens em português) | Texto narrativo, seções normativas, parágrafos de regra — qualquer seção sem tabela |
| **Tabela** | a tabela inteira, sem limite fixo de palavras; cap prático de 1.500 palavras (~2.000 tokens) | Qualquer seção que contenha uma tabela estruturada (multiplicadores, SLA, prazos) |

O perfil tabela garante que uma tabela com 15 ou mais colunas nunca seja dividida no meio, preservando a associação entre linha e coluna. O cap prático de 1.500 palavras evita que uma tabela patologicamente grande seja tratada como um único chunk que domine o contexto de uma consulta — mas nas tabelas da documentação normativa da NovaTech (multiplicadores, SLA), esse cap é uma salvaguarda que não chega a ser acionada na prática, pois essas tabelas têm tipicamente 200–400 palavras.

**Detecção de tabela:** uma seção é tratada como chunk de tabela quando contém ao menos 3 linhas de tabela estruturada (linhas que seguem a sintaxe de tabela do formato de origem). Abaixo desse limite, a seção é tratada pelo perfil padrão mesmo que contenha alguma marcação tabular esparsa.

## Fronteiras de divisão

- A divisão em chunks ocorre **apenas em fronteiras semânticas**: cabeçalhos de nível 2 e 3 (seções e subseções), nunca no meio de uma frase ou de um parágrafo. Divisão por contagem cega de caracteres é rejeitada — corta frases no meio e perde contexto.
- O cabeçalho de nível 1 (título do documento) **não** é usado como fronteira de divisão — ele permanece no mesmo chunk que a primeira seção do documento, evitando que o bloco de título e metadados (versão, responsável, classificação) se torne um chunk órfão de poucas palavras.
- Quando uma seção do perfil padrão excede o tamanho-alvo de 400 palavras, ela é subdividida em fronteiras de parágrafo (nunca no meio de um parágrafo): os parágrafos são agrupados sequencialmente em um novo chunk até se aproximar do limite de palavras, e o próximo parágrafo inicia o chunk seguinte.
- **Regra absoluta para tabelas:** uma tabela nunca é dividida, independentemente do tamanho da seção que a contém. Se uma seção com tabela ultrapassa o tamanho-alvo do perfil padrão, o perfil tabela se aplica automaticamente a ela.

## Overlap entre chunks

Chunks consecutivos do perfil padrão recebem um overlap de **40 palavras** (aproximadamente 10% de um chunk padrão de 400 palavras): as últimas 40 palavras do chunk anterior são prependidas ao chunk seguinte. Isso garante continuidade de contexto em fronteiras de seção, sem duplicar uma quantidade excessiva de conteúdo entre chunks.

Chunks do perfil tabela **não** recebem overlap — uma tabela é uma unidade fechada e não se beneficia de repetir palavras do chunk anterior.

## Conversão de tabela em prosa (table-to-prose)

Modelos de embedding não capturam bem a estrutura de linhas e colunas de uma tabela em formato Markdown — os caracteres de separação de coluna e a repetição de células ao longo das linhas reduzem a qualidade semântica do vetor gerado. Na prática validada em protótipo, o chunk de uma tabela de SLA ficou classificado na 6ª posição de relevância (fora do conjunto tipicamente enviado ao modelo de linguagem) para uma pergunta que a própria tabela respondia diretamente, porque seções de texto narrativo que meramente *mencionavam* os mesmos termos da pergunta (nomes de tier, palavra "SLA") pontuaram mais alto por sobreposição de palavras-chave.

A correção aplicada — e decidida como parte da estratégia de chunking de produção — é: para todo chunk do perfil tabela, antes de gerar o embedding, uma representação em prosa do conteúdo da tabela é gerada e prependida ao chunk, antes da tabela original em Markdown. Cada linha da tabela é convertida numa frase no formato "métrica — cabeçalho 1: valor 1, cabeçalho 2: valor 2, (...)."; as frases de todas as linhas são concatenadas para formar o bloco de prosa.

O chunk final indexado contém, nesta ordem: a prosa gerada (que melhora a qualidade do embedding e portanto a posição do chunk na busca por similaridade) seguida da tabela original em Markdown (preservada para que o modelo de linguagem leia os valores exatos ao montar a resposta final). Essa correção foi validada no protótipo: o mesmo chunk de tabela subiu de posição na relevância o suficiente para entrar no conjunto de chunks tipicamente enviado ao modelo de linguagem, sem alterar nenhum valor do conteúdo original.

## Metadados atribuídos durante o chunking

Além dos metadados herdados do documento de origem (ver "Metadados por chunk" na skill principal), cada chunk recebe, no momento em que é criado:

- `section` — o texto do cabeçalho da seção de origem.
- `chunk_type` — `standard` ou `table`, conforme o perfil aplicado.
- Um índice sequencial do chunk dentro do documento (usado para rastreabilidade e depuração, sem significado de negócio próprio).
