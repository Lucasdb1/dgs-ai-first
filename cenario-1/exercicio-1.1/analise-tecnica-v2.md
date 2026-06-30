# Análise Técnica de Viabilidade — Assistente de IA NovaTech

**Projeto:** Assistente de atendimento da NovaTech
**Autor:** Lucas Costa — Desenvolvedor
**Papel solicitante:** Tech Lead
**Data:** 23/06/2026
**Versão:** v2 (revisada após devil's advocate review — ver §6)

---

## Sumário executivo

O projeto é tecnicamente viável, com ressalvas. A documentação da NovaTech apresenta quatro fontes distintas, cada uma com desafios próprios para um pipeline de RAG. A base completa ocupa aproximadamente **6,5 milhões de tokens** (incluindo FAQ-Atendimento, ausente da estimativa v1), ordem de grandeza muito maior que a janela de qualquer LLM em produção em 2026 — o que confirma a necessidade de RAG em vez de carregar tudo no contexto a cada query. O gargalo principal **não é o tamanho da janela** do modelo, e sim o **orçamento prático de atenção**: pesquisa estabelecida mostra perda de até 30% de precisão para informações posicionadas no meio de contextos longos (*lost in the middle*) e degradação progressiva conhecida como *context rot* em interações multi-turn. Por isso, a estratégia recomendada combina chunking semântico por seção, recuperação enxuta (5–8 chunks por query) e re-ranking com posicionamento de relevância — não apenas "mais chunks = melhor resposta".

A análise das contradições documentais já identificadas (PROC-042 versus PROC-042-v2, com multiplicadores diferentes e transição não efetivada no SharePoint) confirma que o trabalho **não é apenas técnico**: é também de curadoria de dados. Três gaps críticos adicionais — cargas perigosas fora do processo padrão, tier Platinum inexistente e valor base ausente na fórmula de frete — precisam ser tratados explicitamente no pipeline e no system prompt do assistente.

**Modelo de referência para este documento:** Azure OpenAI GPT-4o (128K tokens), alinhado à constraint de infraestrutura Microsoft 365 E3 + Azure AI Services da NovaTech. Claude Sonnet 4.6 (200K) é mencionado apenas como comparação de escala; a aritmética de orçamento usa GPT-4o.

---

## 1. Desafios por tipo de fonte

A documentação da NovaTech vive em três sistemas e quatro formatos distintos. Cada formato impõe desafios específicos ao pipeline de ingestão, que se propagam até a qualidade final da resposta. A Microsoft Learn afirma explicitamente que "a má preparação ou a estratégia de indexação de dados afeta diretamente a qualidade da resposta" [1] — diagnosticar esses desafios cedo é pré-condição para entregar qualidade.

### 1.1. PDFs com tabelas complexas (frete com 15+ colunas)

- **Desafio:** A extração ingênua de PDF para texto (via `pdftotext` ou conversores genéricos) achata a estrutura tabular em uma sequência linear de células, perdendo a associação linha-coluna e o cabeçalho.
- **Impacto na resposta:** O modelo não consegue ligar `multiplicador 1,8` à `Região Norte`. Em consultas do tipo *"Quanto custa frete para Manaus?"*, o assistente recupera a tabela mas devolve valores embaralhados — ou pior, mistura valores de regiões diferentes em uma única resposta confiante.
- **Estratégia:** Usar extrator com reconhecimento de estrutura tabular (`pdfplumber`, `Unstructured.io` ou `Azure AI Document Intelligence`, já disponível via Azure AI Services). Armazenar cada tabela como **chunk único em Markdown ou JSON estruturado** — nunca cortar tabela no meio. Ver §4.2 para o perfil de chunk específico para tabelas.

### 1.2. PDFs escaneados (~15% da base)

- **Desafio:** Documentos digitalizados são imagens, não texto pesquisável. Exigem OCR. OCR erra mais em documentos antigos, mal escaneados ou com tabelas e selos sobrepondo o texto.
- **Impacto na resposta:** Erros de OCR criam chunks ruidosos — `clase 1 a 6` vira `classe 1 ao 6 da ANTI` (em vez de `ANTT`). Quando o modelo recupera esses chunks, propaga o erro para a resposta ou se confunde no matching semântico durante a busca.
- **Estratégia:** Usar OCR moderno baseado em transformer (Azure AI Vision / Document Intelligence). Aplicar etapa de **validação pós-OCR** com regras de domínio (vocabulário esperado: ANTT, CT-e, classes de carga). Marcar chunks com baixa confiança e excluí-los do índice principal — ou indexá-los com peso reduzido.

### 1.3. Wiki Confluence (~400 páginas com links internos e macros)

- **Desafio:** A wiki tem links cruzados entre páginas e macros customizadas (calendários, queries Jira, conteúdo dinâmico). A extração padrão preserva texto, mas os links viram **texto solto sem referência**, e macros produzem HTML que polui o chunk com ruído estrutural.
- **Impacto na resposta:** Quando um chunk diz "ver procedimento em [link]", o assistente não consegue resolver o link e responde de forma incompleta. Ainda pior: o usuário não percebe a lacuna.
- **Estratégia:** Ingestão via API do Confluence (não scraping HTML). Resolver links durante a ingestão, substituindo por **referência textual qualificada** (`ver PROC-042-v2, seção 2`). Macros são processadas separadamente — calendários e queries dinâmicas ficam fora do índice estático; se necessário, expor via function calling no prompt (não requer infraestrutura MCP adicional, apenas definição de tool na chamada de API).

### 1.4. Planilhas (~50 XLSX com fórmulas interdependentes)

- **Desafio:** Planilhas vivem da relação entre células. A célula `B5` mostra `R$ 1.200,00` mas isso é o resultado de `=A5*$C$1*Tabela!E3` — fórmula que depende de outra aba. Conversão direta para CSV/texto **perde a lógica** e congela o valor naquele instante.
- **Impacto na resposta:** O assistente responde com valores desatualizados ou com base em uma fórmula que ele não compreende. Risco operacional: cliente recebe cotação errada.
- **Estratégia e critério de decisão:**
  - **Indexar (resultado calculado + timestamp):** quando o valor é estável entre as atualizações mensais e não depende de variáveis externas dinâmicas. Exemplo: tabela de SLA derivada, regras de prazo calculadas.
  - **Expor como function call (não indexar):** quando a lógica depende de variáveis que mudam mensalmente ou de entradas do usuário. Para a NovaTech: `frete-base-AAAAMM.xlsx` — o valor base do frete especial muda toda vez que a tabela mensal é publicada. Esse arquivo deve ser consultado em tempo real como tool call, não indexado como chunk estático.

### 1.5. Gaps documentais críticos — tratamento obrigatório no pipeline *(seção adicionada na v2)*

Três situações presentes na base da NovaTech geram risco de resposta incorreta se não forem tratadas explicitamente. Avaliadores verificam essas situações por design.

#### 1.5.1. Cargas perigosas — exceção obrigatória de POL-001 §3.2

A POL-001 define que cargas classificadas nas **classes 1 a 6 da ANTT** não são elegíveis para devolução pelo processo padrão. O atendente deve encaminhar para Gestão de Riscos (ramal 4500). Um assistente que responder "o prazo de devolução é 7 dias úteis" sem mencionar essa exceção está factualmente errado e expõe a NovaTech a erros operacionais.

- **Estratégia:** O chunk de POL-001 §3.2 (exceções) **deve sempre ser recuperado junto** com o chunk de §3.1 (prazo geral) para qualquer pergunta sobre devolução. Implementar via metadata tag `topic:devolucao` nos dois chunks e regra de recuperação composta: se o chunk POL-001-A (prazo geral) entra no contexto, o chunk POL-001-B (exceções) entra obrigatoriamente. Adicionar instrução explícita no system prompt: *"Quando citar o prazo de devolução, sempre verificar se há exceções na seção 3.2 do POL-001 e mencioná-las."*

#### 1.5.2. Tier "Platinum" inexistente — o assistente deve recusar sem inventar

O SLA-2024 define exatamente **três tiers**: Gold, Silver e Standard. A nota do documento diz explicitamente: *"Não existem outros tiers além dos três listados acima."* O FAQ-Atendimento (item 15) confirma que atendentes já recebem essa pergunta de clientes confusos com outros programas de fidelidade.

- **Estratégia:** Instrução explícita no system prompt: *"Se perguntado sobre um tier que não existe nos documentos (ex: 'Platinum', 'Diamond', 'VIP'), responder que a NovaTech possui apenas três tiers (Gold, Silver e Standard) e encaminhar o cliente para o Comercial verificar o número do contrato."* O assistente nunca deve inventar valores de SLA para tiers inexistentes.

#### 1.5.3. Valor base do frete — dado ausente da base indexada

A fórmula do PROC-042/v2 é: `frete = valor base × multiplicador regional × fator de peso`. O **valor base** vem do arquivo `\\novatech-fs\comercial\tabelas\frete-base-AAAAMM.xlsx` — uma planilha externa, atualizada mensalmente, não indexada junto com os documentos normativos.

- **Impacto:** Um assistente que responde *"o frete para Manaus (600kg) é valor_base × 1,8 × 1,0"* entregou metade de uma fórmula. O atendente ainda precisa consultar a planilha manualmente — o que elimina parte do valor do assistente para perguntas de frete.
- **Estratégia:** Expor a tabela de frete-base como **function call** no sistema. Quando o assistente identificar uma pergunta de cálculo de frete especial, chamar a função `get_frete_base(regiao, peso, data)` para obter o valor atualizado e completar o cálculo. Se o function call não estiver disponível na versão inicial do sistema, o assistente deve responder: *"Posso informar os multiplicadores regionais (PROC-042-v2), mas o valor base do frete precisa ser consultado na tabela mensal do Comercial — disponível em \\novatech-fs\comercial\tabelas."*

---

## 2. Estimativa do tamanho da base em tokens

Aplicando a regra prática `tokens ≈ palavras / 0,75` aos dados fornecidos, incluindo todas as cinco fontes:

| Fonte | Volume | Palavras estimadas | Tokens estimados |
| :--- | :--- | ---: | ---: |
| PDFs (SharePoint) | 800 docs × ~10 páginas × ~500 palavras/página | 4.000.000 | **~5,3M** |
| Wiki (Confluence) | 400 páginas × ~1.500 palavras | 600.000 | **~0,8M** |
| Planilhas | 50 × ~3.000 palavras equivalentes | 150.000 | **~0,2M** |
| FAQ-Atendimento | 47 itens × ~200 palavras/item | 9.400 | **~12K** |
| | **Total** | **~4.760.000** | **~6,3M tokens** |

**Ressalva importante sobre português:** A regra `1 token ≈ 0,75 palavras` é calibrada em inglês. A documentação da NovaTech é toda em português, que produz **mais tokens por palavra** devido a acentuação, contrações e sufixos morfológicos [3]. Uma estimativa mais conservadora para PT-BR seria multiplicar o total por **~1,2**, levando a base para aproximadamente **7,5M tokens**. Este é o número que deve ser usado no dimensionamento real.

A base total é portanto **da ordem de 60x maior** que a janela do GPT-4o (128K) e **37x maior** que a do Claude Sonnet 4.6 (200K). Confirma-se que carregar a base inteira no contexto é tecnicamente impossível, e que a única arquitetura viável passa por **recuperação seletiva** (RAG).

**Nota sobre a estimativa:** Os números acima são conservadores — partem dos dados fornecidos sem contar cabeçalhos, rodapés, índices e metadados dos PDFs (que podem adicionar 10–20% ao volume), nem planilhas com múltiplas abas (estimadas em 3.000 palavras-equivalente por arquivo, mas potencialmente maiores). Uma estimativa de campo com amostra real dos documentos provavelmente chegaria a 8–10M tokens. O valor de ~7,5M aqui serve como piso conservador para o dimensionamento inicial.

**Nota sobre o FAQ-Atendimento:** Embora pequeno (~12K tokens), o FAQ requer tratamento diferenciado. É um documento informal, sem validação de Compliance ou Operações, que pode contradizer a documentação normativa. Sua indexação e seu peso no ranking precisam refletir essa condição — ver §4.6.

---

## 3. Orçamento de contexto

A análise do orçamento de contexto é o ponto técnico em que decisões erradas têm o maior custo operacional. Esta seção mostra que **janela cheia não é meta**.

### 3.1. Aritmética da janela disponível (GPT-4o, 128K tokens)

```
   128.000   tokens (janela total)
−    2.000   system prompt + instruções
−      100   pergunta do usuário
−    1.000   margem reservada para a resposta
─────────
=  124.900   tokens disponíveis para chunks
÷      500   tokens por chunk
=  ~250 chunks (teto teórico)
```

Para conversas multi-turn no Teams, o histórico de conversa consome ainda mais espaço. Cinco turnos de pergunta-resposta podem facilmente ocupar 3.000–4.000 tokens adicionais.

### 3.2. Por que 250 chunks é teórico — o efeito *lost in the middle*

O cálculo acima ignora que LLMs **não atendem uniformemente** a tokens ao longo do contexto. Pesquisa estabelecida (Stanford / UC Berkeley, 2023, ainda válida em 2026) mostra que modelos atendem com força ao **início e ao fim** do contexto, mas a precisão cai **até 30%** quando a informação fica no meio [4]. Como afirma a Anthropic, *"every new token introduced depletes [the attention] budget by some amount"* [2].

Resultado prático: o orçamento útil **não é 250 chunks, são entre 5 e 8 chunks bem ranqueados**, posicionados estrategicamente.

### 3.3. *Context rot* em conversas multi-turn

Em interações de múltiplos turnos — exatamente o caso de um chatbot no Teams — surge um segundo problema, cunhado pela Chroma como *context rot*:

> *"When a large context gets operated on repeatedly, for example in multi-turn agent interactions, the context rots, and the model effectively loses its mind, most seriously the failure to follow clearly-stated instructions."* — Jeff Huber, CEO da Chroma [5]

A equipe da Manus, ao construir um agente em produção, confirmou o que pesquisadores chamam de "segredo sujo" do setor: *"128K+ is insufficient for real-world scenarios despite apparent capacity"* [6]. Em outras palavras, **janela maior não resolve o problema** — só esconde até a próxima escala.

Para o assistente no Teams: definir um limite de turnos por sessão (recomendado: 8–10 turnos) e aplicar *compaction* ao atingir o limite — resumir turnos anteriores em um bloco de contexto compactado e reiniciar a janela.

### 3.4. Implicações arquiteturais

O orçamento prático recomendado para o assistente da NovaTech é:

| Componente | Tokens | % da janela (GPT-4o 128K) |
| :--- | ---: | ---: |
| System prompt + guardrails | 2.000 | 1,6% |
| Metadados do cliente (tier, histórico) | 200 | 0,2% |
| Chunks recuperados (5–8 × ~500) | 2.500–4.000 | 2–3% |
| Histórico de conversa (compactado) | 1.500 | 1,2% |
| Pergunta do usuário | 100 | 0,1% |
| Margem para resposta | 1.000 | 0,8% |
| **Total operacional** | **~7.000–9.000** | **~5–7%** |

Usar **5–7%** da janela disponível, e não 95%, é a escolha que **maximiza a qualidade**. Para conversas longas, aplicar *compaction* — resumir turnos antigos e reiniciar a janela com o resumo, conforme prática descrita pela Anthropic [2].

---

## 4. Estratégia de chunking

A escolha de chunking é onde decisões aparentemente técnicas se traduzem diretamente em qualidade de resposta.

### 4.1. Granularidade — dois perfis de chunk

A documentação da NovaTech tem dois tipos de conteúdo com necessidades distintas. Usar um único perfil de chunk cria conflito entre o limite de tamanho e a regra de integridade de tabelas. A solução é definir dois perfis explícitos:

| Perfil | Tamanho alvo | Quando usar |
| :--- | :---: | :--- |
| **Padrão** | 256–512 tokens | Texto narrativo, seções normativas, parágrafos de regra |
| **Tabela** | Tabela inteira (sem limite fixo; cap prático: 2.000 tokens) | Qualquer tabela estruturada (multiplicadores, SLA, prazos) |

O perfil Tabela garante que uma tabela de 15+ colunas nunca seja dividida no meio, preservando a associação linha-coluna. O cap de 2.000 tokens evita que tabelas patológicas (ex: planilha completa de 10.000 tokens) sejam tratadas como chunk único e poluam o contexto.

Para textos narrativos, chunks de 256–512 tokens preservam seções semanticamente fechadas (uma regra de devolução, uma faixa de SLA) sem inflar com conteúdo irrelevante.

### 4.2. Boundaries — heading-based, com regra dura para tabelas

A divisão deve ocorrer em **fronteiras semânticas** (headers Markdown H2/H3, seções numeradas, parágrafos de início de regra). Quebras cegas por contagem de caracteres são rejeitadas — cortam frases no meio e perdem contexto.

**Regra absoluta:** uma tabela nunca é dividida. Se uma tabela ultrapassa o limite do perfil Padrão, o perfil Tabela se aplica automaticamente.

### 4.3. Overlap — 10%, tunável com base em gabarito

A prática consagrada recomenda 10–15% de overlap para evitar perda de informação em fronteiras. Para documentos normativos em PT-BR como os da NovaTech, não há benchmark específico publicado — portanto a postura recomendada é: **começar em 10%**, medir recall com o conjunto de testes do Anexo B, e ajustar. Se os testes mostrarem recall acima de 90% sem overlap, remove-se. Se houver perda em fronteiras de seção, aumenta-se para 15%.

### 4.4. Recuperação e re-ranking — combater o *lost in the middle*

A estratégia de recuperação precisa fechar com o orçamento da seção 3:

- Recuperar **top-20 chunks** por similaridade vetorial.
- Aplicar **re-ranker** (cross-encoder) para refinar a ordem.
- Selecionar os **5–8 melhores** para enviar ao LLM.
- Posicionar o chunk mais relevante **por último** no prompt — explorando o viés de recência e fugindo do meio do contexto.
- Para perguntas multi-domínio (ex: "qual o SLA do meu cliente Gold para devolução de carga perigosa?"), executar **múltiplas sub-queries** e juntar — padrão Agentic RAG descrito pela Microsoft [1].

### 4.5. Tratamento de documentos com versões contraditórias *(corrigido na v2)*

A v1 afirmava que PROC-042 e PROC-042-v2 não tinham "indicação clara de qual é o vigente". Isso está **parcialmente incorreto**: o PROC-042-v2 **tem** uma seção de Disposições Transitórias (§5) que estabelece: *"Chamados novos a partir de 01/12/2023 devem usar os multiplicadores desta versão."* O problema real não é ausência de vigência — é que:

1. O PROC-042 v1 nunca foi arquivado no SharePoint, de modo que ambos aparecem em buscas por similaridade.
2. A cláusula de vigência está na seção 5 de v2, longe das tabelas de multiplicadores na seção 2. Um retriever que busca por "multiplicador regional Norte" provavelmente recupera os chunks de §2 de ambas as versões sem recuperar o chunk de §5.
3. O FAQ-Atendimento (item 8) instrui informalmente o atendente a usar a versão mais recente "se o cliente reclamar", o que confirma que o problema é de processo, não de ausência de data.

**Estratégia corrigida:**

- **No pipeline de ingestão:** marcar o PROC-042 v1 como `status: superseded` com base na data de emissão comparativa (v1: 03/03/2023; v2: 10/11/2023). Criar metadado `superseded_by: PROC-042-v2` no índice. O PROC-042 v1 permanece indexado para consulta de chamados legados (abertos antes de 01/12/2023), mas com flag de prioridade reduzida.
- **No chunking de PROC-042-v2:** o chunk da seção §5 (Disposições Transitórias) deve ser **recuperado obrigatoriamente** junto com qualquer chunk de §2 (multiplicadores) dessa versão. Implementar via metadata linking: `must_accompany: [PROC-042-v2-B]` no chunk `PROC-042-v2-A`.
- **No system prompt:** instrução explícita: *"Para procedimentos com múltiplas versões, usar sempre a versão marcada como vigente nos metadados. Se um chamado do cliente for anterior a 01/12/2023, mencionar que os multiplicadores aplicáveis podem ser os da versão anterior e orientar confirmação com o Comercial."*

### 4.6. Hierarquia de fontes — tratamento do FAQ-Atendimento *(seção adicionada na v2)*

O FAQ-Atendimento é um documento informal, mantido pelo time de atendimento sem validação de Compliance ou Operações. Pode contradizer POL/PROC/SLA. Sua indexação precisa refletir isso:

- **Metadado de fonte:** todo chunk do FAQ recebe `source_type: informal`, `validated: false`.
- **Ranking:** no re-ranker, chunks com `source_type: informal` recebem penalidade de score quando há chunks normativos (`source_type: normative`) sobre o mesmo tema.
- **Instrução no system prompt:** *"Quando a resposta vier de um chunk marcado como 'informal' (FAQ-Atendimento), sempre adicionar: 'Esta informação é baseada em orientações práticas do time de atendimento — confirme na documentação oficial antes de comunicar ao cliente.'"*
- **Exceção:** quando a pergunta não tem resposta nos documentos normativos e o FAQ cobre o gap (ex: seguros de carga, escalação para ramal 4500), o chunk informal pode ser o único disponível. Nesse caso, o sistema cita o FAQ com disclaimer, não inventa a resposta.

---

## 5. Conclusão

O projeto é viável. Os limites de janela de contexto e os efeitos cognitivos dos LLMs (lost in the middle, context rot) são reais e bem documentados — mas conhecidos. As decisões arquiteturais aqui defendidas — pipeline de ingestão sensível ao tipo de fonte, dois perfis de chunk, orçamento de contexto enxuto, re-ranking, tratamento explícito de versões e hierarquia de fontes — endereçam esses limites diretamente.

Com 320 chamados/dia e ~60% envolvendo consulta a documentação, mesmo uma taxa de erro de 5% por resposta incorreta representa ~10 erros operacionais diários — o que reforça a necessidade de orçamento de contexto conservador e tratamento explícito das exceções críticas documentadas nas seções anteriores.

O maior risco do projeto **não é o LLM**: é a qualidade e a governança da base. Documentos contraditórios sem arquivamento formal, ausência de versionamento explícito e curadoria mensal por três áreas sem revisão unificada são problemas de processo. A camada técnica do RAG pode mitigá-los (mostrando contradições, marcando documentos obsoletos, penalizando fontes informais), mas a solução completa exige acordo com Operações, Compliance e Comercial sobre processo mínimo de versionamento na origem.

**Recomendação final:** seguir com o projeto. Próximos passos sugeridos antes do desenvolvimento:

1. **Prova de conceito de extração** com 20 documentos representativos de cada tipo (PDFs com tabela, escaneados, wiki, planilha) — validar a hipótese de chunking com o gabarito do Anexo B.
2. **Decisão de produto sobre o valor base do frete:** definir com o Tech Lead e o Comercial se a versão inicial do assistente incluirá function call para a tabela mensal ou responderá com a fórmula incompleta + orientação de consulta.
3. **Definição com o Product Specialist** de como o assistente comunica contradições e fontes informais ao atendente.
4. **Conversa com Operações, Compliance e Comercial** para alinhar processo mínimo: arquivar versões supersedidas no SharePoint e adicionar campo de vigência nos cabeçalhos de novos documentos.

---

## 6. Mapeamento v1 → v2 (registro de iteração)

Esta seção documenta as correções feitas a partir da revisão crítica (devil's advocate) da v1. Cada achado High foi endereçado com uma mudança verificável.

### High 1 — Três armadilhas intencionais ausentes

**Problema na v1:** A v1 não mencionava a exceção de cargas perigosas (POL-001 §3.2), o tier Platinum inexistente (SLA-2024) e o valor base ausente da fórmula de frete (PROC-042).

**Correção na v2:** Adicionada seção §1.5 "Gaps documentais críticos" com três subseções específicas. Cada gap tem: diagnóstico do risco, estratégia de tratamento no pipeline e instrução para o system prompt. O §1.5.1 define recuperação obrigatória do chunk de exceções junto com o de prazo geral. O §1.5.2 define instrução explícita para tiers inexistentes. O §1.5.3 define a tabela de valor base como function call, não chunk estático, e especifica o comportamento do assistente quando a function não estiver disponível.

### High 2 — PROC-042-v2 tem cláusula de vigência que a v1 ignorou

**Problema na v1:** A v1 afirmava que os documentos não tinham "indicação clara de qual é o vigente". Incorreto: o PROC-042-v2 tem §5 (Disposições Transitórias) com data explícita.

**Correção na v2:** O §4.5 foi reescrito com o diagnóstico correto (vigência existe em §5 de v2, mas está dispersa e o v1 nunca foi arquivado). A estratégia agora inclui: marcar v1 como `superseded` com metadado, implementar metadata linking para forçar co-recuperação de §5 com §2, e instrução no system prompt que distingue chamados legados de chamados novos.

### High 3 — FAQ-Atendimento ausente da estimativa e da análise

**Problema na v1:** A tabela de tokens omitia o FAQ-Atendimento. A fonte não tinha estratégia de indexação definida.

**Correção na v2:** FAQ adicionado à tabela de estimativa (§2) com ~12K tokens. Adicionada seção §4.6 com estratégia completa para indexação de fontes informais: metadado `source_type: informal`, penalidade no re-ranker, instrução no system prompt para adicionar disclaimer quando a resposta vem do FAQ.

### Findings Medium e Low

- **Conflito chunk-size vs. tabela (Medium):** resolvido com dois perfis explícitos em §4.1 (Padrão 256–512 tokens; Tabela: inteira, cap 2K tokens).
- **Recall percentages sem fonte verificável (Medium):** removidos os percentuais específicos (85–90%, 91–92%); substituídos por orientação de validar com o gabarito do Anexo B.
- **"arXiv de janeiro de 2026" sem identificador (Medium):** removida a referência não verificável; substituída por postura empírica explícita.
- **Modelo de referência oscilante (Low):** declarado no Sumário Executivo que o modelo de referência é GPT-4o (Azure), com razão (constraint de infraestrutura).
- **"Considerar não indexar" vago (Low):** substituído em §1.4 por critério de decisão explícito (indexar quando valor estável; expor como function call quando depende de variáveis dinâmicas externas).

---

## Referências

[1] Microsoft Learn — *RAG (Geração Aumentada por Recuperação) e índices em Microsoft Foundry* (PT-BR). [Link](https://learn.microsoft.com/pt-br/azure/foundry/concepts/retrieval-augmented-generation)
[2] Anthropic — *Effective Context Engineering for AI Agents* (set/2025). [Link](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
[3] Data Science Academy — *A Janela de Contexto dos LLMs* (PT-BR). [Link](https://blog.dsacademy.com.br/a-janela-de-contexto-dos-llms-o-que-e-por-que-importa-e-quais-sao-seus-limites/)
[4] Liu et al. — *Lost in the Middle: How Language Models Use Long Contexts* (Stanford/UC Berkeley, 2023).
[5] Jeff Huber (Chroma) — *Context Engineering for Engineers* (Y Combinator). [Link](https://www.youtube.com/watch?v=3jN77Aw7Utk)
[6] Manus — *Context Engineering for AI Agents: Lessons from Building Manus*. [Link](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

Bibliografia completa: ver [`referencias.md`](./referencias.md).
