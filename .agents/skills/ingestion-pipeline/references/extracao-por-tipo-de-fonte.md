# Extração por tipo de fonte

Este documento detalha o desafio, o impacto na qualidade da resposta do assistente e a estratégia de extração para cada tipo de fonte documental da NovaTech. Faz parte da skill [`ingestion-pipeline`](../SKILL.md) — ver ali a visão geral do domínio e o fluxo de processamento completo.

## PDFs com tabelas complexas (SharePoint)

Parte dos PDFs do SharePoint contém tabelas com 15 ou mais colunas (por exemplo, tabelas de multiplicadores de frete por região e faixa de peso).

- **Desafio:** a extração ingênua de PDF para texto (conversores genéricos de PDF-para-texto) achata a estrutura tabular em uma sequência linear de células, perdendo a associação entre linha e coluna e entre célula e cabeçalho.
- **Impacto na resposta:** o modelo não consegue ligar corretamente um valor de multiplicador à região a que ele pertence. Em perguntas de cálculo (ex.: custo de frete para uma região e peso específicos), o assistente pode devolver valores embaralhados entre regiões — ou, mais grave, misturar valores de regiões diferentes numa única resposta apresentada com confiança.
- **Estratégia:** usar um extrator com reconhecimento de estrutura tabular (ex.: Azure AI Document Intelligence, já disponível na conta de Azure AI Services da NovaTech) em vez de um conversor genérico de PDF-para-texto. Cada tabela deve ser preservada como uma unidade estruturada (Markdown ou equivalente) — nunca cortada no meio — para ser tratada como chunk de tabela na etapa de chunking (ver [`estrategia-de-chunking.md`](./estrategia-de-chunking.md)).

## Documentos escaneados (~15% da base)

Uma parcela da base do SharePoint é composta de documentos digitalizados — imagens, não texto pesquisável.

- **Desafio:** documentos escaneados exigem OCR. OCR erra mais em documentos antigos, mal escaneados, ou com tabelas e selos sobrepondo o texto.
- **Impacto na resposta:** erros de OCR criam chunks ruidosos (ex.: um código de classificação normativa reconhecido incorretamente). Quando o modelo recupera um chunk com erro de OCR, ele propaga o erro para a resposta final ou se confunde durante o matching semântico na busca.
- **Estratégia:** usar OCR baseado em transformer (ex.: Azure AI Vision / Azure AI Document Intelligence). Aplicar uma etapa de validação pós-OCR contra um vocabulário de domínio esperado (siglas e termos normativos do setor de logística). Chunks originados de um trecho com baixa confiança de OCR são **excluídos do índice principal** — não ficam pesquisáveis pelo domínio de Consulta do Assistente até passarem por revisão humana. Diferente do tratamento dado a fontes informais (que permanecem pesquisáveis com o metadado `validated: false` sinalizando menor confiança — ver skill principal), aqui a decisão é não expor o conteúdo enquanto sua exatidão não for confirmada, já que um erro de OCR pode alterar um valor numérico ou um termo normativo sem que isso seja perceptível no texto resultante.

## Wiki corporativa (hoje Confluence, ~400 páginas)

A wiki tem links internos entre páginas e usa macros customizadas (calendários, conteúdo dinâmico).

- **Desafio:** a extração padrão de uma página wiki preserva o texto, mas os links internos tornam-se texto solto sem referência resolvida, e as macros produzem marcação que polui o chunk com ruído estrutural.
- **Impacto na resposta:** quando um trecho extraído diz algo como "ver procedimento em [link]" e o link não foi resolvido, o assistente responde de forma incompleta sem que o atendente perceba a lacuna.
- **Estratégia:** ingestão via API do sistema de wiki, não por scraping de HTML. Links internos são resolvidos durante a ingestão, substituindo a referência solta por uma referência textual qualificada (nome do documento e seção referenciada). Macros com conteúdo dinâmico (calendários, consultas dinâmicas) ficam fora do índice estático — se esse tipo de informação precisar estar disponível ao assistente, isso é resolvido fora deste domínio (ex.: como uma chamada de função em tempo de consulta), não pela indexação de um chunk estático.

## Planilhas de referência (~50 arquivos XLSX, pasta de rede)

Planilhas de referência têm células cujo valor depende de fórmulas que referenciam outras células ou outras abas.

- **Desafio:** converter uma planilha diretamente para texto ou CSV captura o valor calculado num instante específico, mas perde a lógica da fórmula que o gerou — se a fórmula depende de uma variável que muda mensalmente, o valor extraído congela e fica desatualizado na próxima atualização.
- **Impacto na resposta:** o assistente responde com um valor desatualizado, ou com base numa fórmula que ele não compreende de fato — risco operacional concreto quando o valor afeta um cálculo cobrado do cliente (ex.: uma cotação de frete).
- **Estratégia e critério de decisão** (ver também "Exclusão de fontes dinâmicas do índice" na skill principal):
  - **Indexar o resultado calculado, com timestamp,** quando o valor é estável entre atualizações mensais e não depende de variáveis externas dinâmicas (ex.: uma tabela de SLA derivada, uma regra de prazo já calculada).
  - **Não indexar — excluir da ingestão** quando a lógica depende de variáveis que mudam com frequência maior que o ciclo do pipeline, ou de uma entrada fornecida em tempo de consulta. O caso concreto conhecido é o valor-base do frete especial, publicado numa planilha comercial atualizada mensalmente de forma independente da documentação normativa de multiplicadores. Este domínio decide apenas que esse tipo de dado não é transformado em chunk; como ele passa a ser obtido em tempo de consulta é uma decisão de outro domínio.
