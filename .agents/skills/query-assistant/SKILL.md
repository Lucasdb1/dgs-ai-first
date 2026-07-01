---
name: query-assistant
description: Esta é a documentação autoritativa do domínio Consulta do Assistente (RAG Query) do novatech-assistant — o endpoint que recebe perguntas em linguagem natural dos atendentes da NovaTech, busca os chunks de documentos mais relevantes já indexados pelo pipeline de ingestão, monta o prompt respeitando um orçamento de contexto controlado e gera uma resposta ancorada nos documentos (grounded), sempre citando a fonte e sinalizando baixa confiança quando nada relevante é encontrado. Carregar esta skill para qualquer tarefa envolvendo o endpoint POST /api/query, validação da pergunta recebida, geração de embeddings, busca semântica no Azure AI Search, orçamento de contexto (context budget), priorização entre versões conflitantes de um mesmo documento (ex.: PROC-042 v1 e v2), chamadas ao GPT-4o via Azure OpenAI, o contrato de resposta com `source_document` obrigatório, a regra de anti-alucinação/grounding, ou o harness de validação determinística de respostas.
metadata:
  author: clovis-cli
  type: domain-skill
---

## Visão geral do domínio

O domínio Consulta do Assistente é o núcleo de RAG (Retrieval-Augmented Generation) do `novatech-assistant`: recebe a pergunta de um atendente da NovaTech (empresa fictícia de logística) em linguagem natural, recupera os trechos de documentação (chunks) mais relevantes já indexados pelo domínio de ingestão de documentos, monta um prompt controlado por orçamento de tokens e devolve uma resposta em linguagem natural que cita sempre a fonte documental usada. O objetivo de negócio é permitir que os 45 atendentes da NovaTech consultem procedimentos, SLAs e regras de frete sem precisar abrir manualmente os documentos internos, com a garantia de que a resposta nunca extrapola o que está escrito nesses documentos.

Este domínio depende do domínio de ingestão de documentos (que produz e indexa os chunks pesquisáveis) e é, por sua vez, consumido por outros dois domínios: o de feedback (que associa uma avaliação de utilidade a uma resposta específica gerada aqui) e o de integração com o Microsoft Teams (que encaminha a pergunta do atendente a este domínio e formata a resposta recebida como cartão do Teams). Nenhuma regra de negócio desses domínios consumidores pertence a esta skill.

Toda a lógica de negócio descrita abaixo representa o comportamento **pretendido** do domínio, conforme especificado nas tasks de desenvolvimento aprovadas para o módulo — a implementação de código encontrada no projeto é apenas um esboço inicial (setup do endpoint HTTP e validação de entrada), com o restante do pipeline (busca, orçamento de contexto, montagem de prompt, chamada ao modelo, resposta final) ainda não codificado. Onde a especificação e o código divergem, ou onde nenhuma fonte resolve um ponto, isso é sinalizado explicitamente abaixo em vez de presumido.

## Contrato do endpoint de consulta

O domínio expõe uma única operação de negócio: `POST /api/query`.

### Requisição

Corpo da requisição, em JSON:

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `question` | string | sim | não pode ser vazia nem conter apenas espaços em branco (espaços nas extremidades são removidos antes da validação); no máximo 1.000 caracteres |

Erros de validação retornam HTTP `400` com uma mensagem de erro única (a primeira regra violada), entre:
- `"question é obrigatório"` — campo ausente;
- `"question deve ser string"` — tipo diferente de string;
- `"question não pode ser vazio"` — string vazia ou composta só por espaços em branco;
- `"question excede 1000 caracteres"` — acima do limite;
- `"Body inválido: JSON malformado"` — corpo da requisição não é um JSON válido.

Nenhum outro campo de entrada (identificador de sessão, histórico de conversa anterior, identificador de usuário, etc.) está definido no contrato de requisição hoje — ver observação sobre histórico de conversa na seção de orçamento de contexto.

### Resposta

Resposta de sucesso, HTTP `200`, em JSON:

| Campo | Tipo | Presença | Regra |
|---|---|---|---|
| `answer` | string | sempre | texto da resposta em linguagem natural |
| `source_document` | string | sempre | identifica o documento de onde a resposta foi extraída (ex.: `"POL-001"`, `"PROC-042-v2"`, `"SLA-2024"`); **nunca pode ser `null` nem estar ausente** — este é um contrato explícito e intencional do domínio, não uma sugestão |
| `confidence_low` | boolean | apenas quando a confiança é baixa | quando presente e `true`, indica que a resposta foi gerada em condição de baixa confiança; a resposta em `answer` recebe também um prefixo textual de aviso nesse caso |

O cenário mínimo evidenciado que aciona `confidence_low: true` é a busca de chunks não retornar nenhum resultado relevante para a pergunta. O schema de saída é validado antes de a resposta ser devolvida ao chamador — o domínio nunca retorna uma resposta com formato inválido.

Para requisições com método HTTP diferente de `POST`, o endpoint registra explicitamente múltiplos métodos HTTP na definição da rota (não apenas `POST`) e devolve `405 Method Not Allowed` através de um guard no próprio handler que verifica o método antes de qualquer processamento de negócio. Esse guard é o que efetivamente produz o `405` — se a rota registrasse apenas `POST`, o runtime do Azure Functions rejeitaria métodos não registrados antes mesmo de o handler ser invocado, tipicamente com `404 Not Found`, tornando o guard interno inalcançável; por isso o registro de múltiplos métodos é parte inseparável desta regra, não um detalhe de implementação livre. Em qualquer caso, a regra de negócio inequívoca é: **nenhum método diferente de POST deve disparar geração de embedding, busca ou chamada ao modelo de linguagem** — a rejeição acontece antes de qualquer processamento de negócio.

## Fluxo de processamento de uma consulta

Uma consulta bem-sucedida percorre, nesta ordem, os seguintes passos:

1. **Validação da entrada** — a pergunta é validada conforme o contrato de requisição acima; falha aqui encerra o fluxo com `400` sem qualquer chamada a serviços externos (nenhum custo de IA é gerado para entradas inválidas).
2. **Geração do embedding da pergunta** — a pergunta validada é convertida em um vetor de embedding.
3. **Busca semântica dos chunks mais relevantes** — o vetor é usado para buscar, no índice de busca mantido pelo domínio de ingestão, os chunks de documentação mais relevantes para a pergunta.
4. **Aplicação do orçamento de contexto** — os chunks recuperados são filtrados para caber no orçamento de tokens disponível (ver seção própria abaixo).
5. **Montagem do prompt** — o prompt final é montado combinando o system prompt do assistente, os chunks selecionados e a pergunta, com eventual instrução de priorização de versão quando aplicável.
6. **Geração da resposta pelo modelo de linguagem** — o prompt montado é enviado ao modelo de completude, que devolve o texto da resposta e o documento de origem.
7. **Formatação da resposta final** — a resposta é formatada garantindo a presença obrigatória de `source_document` e, se aplicável, o sinalizador de baixa confiança.
8. **Validação determinística da resposta (harness)** — antes de a resposta chegar ao usuário, um harness de validação estrutural adicional a verifica (ver seção "Harness de validação da resposta" abaixo).

Falha em qualquer uma das chamadas externas (geração de embedding ou geração de resposta) após as tentativas de repetição descritas na próxima seção interrompe o fluxo com um erro de domínio específico, sem chegar a uma resposta parcial.

## Regras de negócio

### Geração de embedding da pergunta

- A pergunta validada é convertida em um vetor de embedding de **1.536 dimensões**.
- A chamada ao serviço de embeddings é repetida em caso de falha, com no máximo **3 tentativas** e espera exponencial entre elas de **1s, 2s e 4s**.
- Se todas as tentativas falharem, o domínio interrompe o fluxo com um erro de domínio dedicado a essa falha (erro de geração de embedding).
- A latência de cada tentativa é registrada para fins de observabilidade.

### Busca de chunks relevantes

- A busca retorna, no máximo, **5 chunks**, ordenados por relevância (score) decrescente.
- Cada chunk retornado contém: o texto do trecho, o documento de origem (`source_document`, nunca nulo — ex.: `"POL-001"`, `"PROC-042-v2"`), a seção do documento de origem, e o score de relevância.
- Quando a busca não encontra nenhum chunk relevante, o resultado é uma lista vazia — isso **não** é tratado como erro, e sim como o gatilho conhecido para a resposta de baixa confiança (ver seção própria).
- A mesma política de repetição da geração de embedding (3 tentativas, backoff de 1s/2s/4s) se aplica à busca.

### Orçamento de contexto (context budget)

O prompt enviado ao modelo de linguagem tem um orçamento de tokens fixo, decidido para a versão de produção do assistente:
- **~4.000 tokens** reservados para o system prompt do assistente;
- **~8.000 tokens** (equivalente a aproximadamente 6.000 palavras) reservados para os chunks recuperados — o correspondente a até 5 chunks de aproximadamente 1.500 tokens cada;
- espaço adicional reservado para a pergunta do atendente e para um histórico de conversa limitado a **3 turnos anteriores**, quando esse histórico existir.

Regra de descarte dos chunks: se os chunks recuperados na busca cabem inteiramente no orçamento de ~8.000 tokens, todos são incluídos no prompt. Se algum chunk faz o total ultrapassar o orçamento, esse chunk e os que viriam depois dele são **descartados por inteiro** — nunca truncados no meio do texto. O orçamento utilizado e a quantidade de chunks efetivamente incluídos são registrados para fins de observabilidade.

**Observação sobre histórico de conversa:** a existência de um orçamento reservado para até 3 turnos de histórico é uma decisão de negócio já estabelecida, mas nenhuma fonte investigada define o mecanismo pelo qual esse histórico chegaria ao endpoint (não há campo de histórico ou identificador de sessão no contrato de requisição documentado acima). Este é, portanto, um detalhe de desenho ainda não especificado, não uma regra a inventar.

### Priorização entre versões conflitantes de documentos

Alguns documentos de origem existem em mais de uma versão simultaneamente ativa na base indexada (o caso conhecido é o procedimento de frete especial, com uma versão original e uma versão revisada). Quando os chunks selecionados para o prompt incluem, ao mesmo tempo, chunks da versão original e da versão revisada do mesmo documento, o prompt deve incluir a instrução explícita:

> "Existem duas versões de [documento]. Priorize [versão mais recente] (mais recente)."

Regra geral: entre versões conflitantes de um mesmo documento presentes simultaneamente no contexto, **a versão mais recente deve prevalecer** na resposta gerada.

### Geração da resposta com o modelo de linguagem

- O prompt final é enviado ao modelo de linguagem com **temperatura 0** — a resposta deve ser determinística, não criativa, o que também facilita testes automatizados.
- Cada tentativa de chamada tem um **timeout de 30 segundos**.
- Em caso de falha, a chamada é repetida com a mesma política de backoff exponencial das demais integrações (até 3 tentativas); se todas falharem, o domínio interrompe o fluxo com um erro de domínio dedicado a essa falha (erro de geração de resposta).
- O modelo sempre devolve, junto com o texto da resposta, o documento de origem — que nunca pode ser nulo ou omitido, mesmo em cenários de baixa confiança (ver próxima seção).

### Grounding e prevenção de alucinação

Regra central do domínio: **o assistente só pode responder com base nas informações presentes nos chunks efetivamente recuperados para aquela pergunta.** Se uma informação não está em nenhum chunk retornado pela busca, o assistente não deve mencioná-la — mencionar informação não presente no contexto recuperado é considerado risco de alucinação e é o principal modo de falha que este domínio existe para evitar.

Consequência direta desta regra: quando a busca não encontra chunks relevantes para a pergunta (por exemplo, uma pergunta sobre uma faixa de peso de frete não coberta por nenhum procedimento documentado, ou sobre uma categoria de cliente que não existe na tabela de SLA), a resposta correta é informar que a informação não foi encontrada na documentação disponível — nunca inventar um valor, uma regra ou uma exceção plausível para preencher a lacuna. Esse é exatamente o cenário que aciona `confidence_low: true` (ver "Contrato do endpoint de consulta" acima).

O comportamento esperado do assistente, conforme definido em sua instrução de sistema (versão vigente, ainda em evolução desde o Cenário 1 anterior a este domínio), é: atuar como assistente de atendimento da NovaTech (empresa de logística); responder apenas perguntas sobre procedimentos, SLAs e regras de frete; usar exclusivamente as informações dos documentos fornecidos como contexto; sempre citar a fonte da informação; e, quando não souber a resposta, dizer explicitamente que não sabe em vez de arriscar uma resposta incorreta.

### Baixa confiança

Quando a confiança na resposta é baixa — o único gatilho concretamente especificado é a busca não retornar nenhum chunk relevante — a resposta final deve:
- incluir o campo `confidence_low: true`;
- incluir um prefixo de aviso no texto da resposta (`answer`), sinalizando ao atendente que a resposta foi gerada em condição de baixa confiança;
- ainda assim, sempre incluir um `source_document` válido (nunca nulo), mesmo neste cenário.

Nenhuma fonte investigada define um limiar de score de relevância abaixo do qual a confiança também deveria ser considerada baixa (isto é, o gatilho documentado é binário — zero chunks encontrados — e não um limiar de qualidade sobre chunks encontrados com baixo score). Tratar isso como um gatilho adicional seria uma regra inventada; não está documentado.

### Harness de validação da resposta

O domínio inclui um componente de validação determinística da resposta (`services/response-validator.ts`), executado antes de ela ser devolvida ao atendente — este componente é a capacidade que sustenta a formação sobre validação determinística de saídas de IA ("Harness Engineering") associada a este domínio. Seu escopo é deliberadamente restrito: ele executa **apenas validações estruturais adicionais**, complementares às validações estruturais já realizadas na formatação da resposta (schema de saída via Zod, presença obrigatória de `source_document`) — não há sobreposição entre as duas camadas, cada uma cobre um conjunto distinto de checagens estruturais.

Fora do escopo deste componente, por decisão de negócio: **nenhuma checagem semântica**. O harness não confirma que a resposta se restringe ao conteúdo dos chunks recuperados (isso é responsabilidade da regra de grounding e prevenção de alucinação, aplicada na geração da resposta — ver seção própria), nem valida a resposta contra um conjunto de perguntas de referência com respostas esperadas. Validação semântica de grounding e validação contra golden queries não são responsabilidades deste harness.

## Entidades e dados

- **Pergunta de consulta** — a entrada do domínio: uma pergunta em texto livre (`question`) feita pelo atendente.
- **Chunk recuperado** — um trecho de documento retornado pela busca, contendo: texto do trecho, documento de origem (`source_document`), seção do documento de origem, e score de relevância.
- **Resposta da consulta** — a saída do domínio: `answer` (texto da resposta), `source_document` (documento de origem, nunca nulo) e, opcionalmente, `confidence_low`.
- **Erro de geração de embedding** — erro de domínio lançado quando a geração do vetor de embedding da pergunta falha após todas as tentativas de repetição.
- **Erro de geração de resposta** — erro de domínio lançado quando a chamada ao modelo de linguagem falha após todas as tentativas de repetição.

## Restrições e validações

- `question`: string obrigatória, sem espaços nas extremidades, mínimo 1 caractere de conteúdo real, máximo 1.000 caracteres.
- Corpo da requisição deve ser JSON válido.
- Busca retorna no máximo 5 chunks por consulta.
- Orçamento de contexto: ~4.000 tokens para o system prompt, ~8.000 tokens (~6.000 palavras) para os chunks, mais espaço para a pergunta e até 3 turnos de histórico de conversa.
- Chunks que excedem o orçamento são descartados inteiros, nunca truncados.
- Geração de embedding e geração de resposta: até 3 tentativas cada, com espera exponencial de 1s, 2s e 4s entre tentativas.
- Chamada ao modelo de linguagem: timeout de 30 segundos por tentativa, temperatura 0.
- `source_document` na resposta final nunca pode ser nulo ou estar ausente, em nenhum cenário — incluindo respostas de baixa confiança.
- Vetor de embedding: 1.536 dimensões.

## Integrações e dependências externas

- **Azure AI Search** — mantém o índice de busca semântica sobre os documentos indexados pelo domínio de ingestão de documentos; é a integração usada para recuperar os chunks mais relevantes para cada pergunta.
- **Azure OpenAI** — usado em dois papéis distintos: geração do embedding da pergunta (modelo `text-embedding-ada-002`, vetor de 1.536 dimensões) e geração da resposta final em linguagem natural (modelo GPT-4o, com janela de contexto de 128 mil tokens, decisão de negócio já estabelecida para o assistente como um todo).

Este domínio depende diretamente do domínio de ingestão de documentos, que é quem produz e mantém atualizado o índice de chunks pesquisáveis consumido aqui — nenhuma regra sobre como os documentos são transformados em chunks, versionados ou marcados como vigentes/obsoletos pertence a esta skill.

## Manutenção da skill

Esta skill é a fonte autoritativa do domínio Consulta do Assistente (RAG Query). Sempre que o comportamento deste domínio mudar de propósito — um novo campo no contrato do endpoint, uma mudança no orçamento de contexto, uma nova regra de priorização de documentos, uma definição concreta para o harness de validação, entre outras — esta skill deve ser atualizada na mesma alteração que muda o comportamento, para permanecer fiel ao que o domínio efetivamente faz.

Drift entre esta skill e a implementação nunca deve ser resolvido silenciosamente. Distinga dois casos: quando a mudança no código foi deliberada e a intenção por trás dela é conhecida, atualize esta skill para refletir a nova intenção. Quando a skill e a implementação divergem semanticamente e não há decisão registrada indicando qual das duas reflete o comportamento pretendido, trate a divergência como um gap e escale para decisão humana — nunca ajuste a skill (nem a implementação) por conta própria para eliminar a divergência.
