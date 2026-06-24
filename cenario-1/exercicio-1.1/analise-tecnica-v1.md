# Análise Técnica de Viabilidade — Assistente de IA NovaTech

**Projeto:** Assistente de atendimento da NovaTech
**Autor:** Lucas Costa — Desenvolvedor
**Papel solicitante:** Tech Lead
**Data:** 16/06/2026
**Versão:** v1 (rascunho para revisão)

---

## Sumário executivo

O projeto é tecnicamente viável, com ressalvas. A documentação da NovaTech apresenta quatro fontes distintas, cada uma com desafios próprios para um pipeline de RAG. A base completa ocupa aproximadamente **6,3 milhões de tokens**, ordem de grandeza muito maior que a janela de qualquer LLM em produção em 2026 — o que confirma a necessidade de RAG (em vez de tentar carregar tudo no contexto a cada query). O gargalo principal **não é o tamanho da janela** do modelo, e sim o **orçamento prático de atenção**: pesquisa estabelecida mostra perda de até 30% de precisão para informações posicionadas no meio de contextos longos (*lost in the middle*) e degradação progressiva conhecida como *context rot* em interações multi-turn. Por isso, a estratégia recomendada combina chunking semântico por seção, recuperação enxuta (5–15 chunks por query) e re-ranking com posicionamento de relevância — não apenas "mais chunks = melhor resposta".

A análise das contradições documentais já identificadas (PROC-042 versus PROC-042-v2 com multiplicadores diferentes e sem indicação de vigência) confirma que o trabalho **não é apenas técnico**: é também de curadoria de dados.

---

## 1. Desafios por tipo de fonte

A documentação da NovaTech vive em três sistemas e quatro formatos distintos. Cada formato impõe desafios específicos ao pipeline de ingestão, que se propagam até a qualidade final da resposta. A Microsoft Learn afirma explicitamente que "a má preparação ou a estratégia de indexação de dados afeta diretamente a qualidade da resposta" [1] — diagnosticar esses desafios cedo é pré-condição para entregar qualidade.

### 1.1. PDFs com tabelas complexas (frete com 15+ colunas)

- **Desafio:** A extração ingênua de PDF para texto (via `pdftotext` ou conversores genéricos) achata a estrutura tabular em uma sequência linear de células, perdendo a associação linha-coluna e o cabeçalho.
- **Impacto na resposta:** O modelo não consegue ligar `multiplicador 1,8` à `Região Norte`. Em consultas do tipo *"Quanto custa frete para Manaus?"*, o assistente recupera a tabela mas devolve valores embaralhados — ou pior, mistura valores de regiões diferentes em uma única resposta confiante.
- **Estratégia:** Usar extrator com reconhecimento de estrutura tabular (`pdfplumber`, `Unstructured.io` ou `Azure AI Document Intelligence`). Armazenar cada tabela como **chunk único em Markdown ou JSON estruturado** — nunca cortar tabela no meio. Para a tabela de multiplicadores regionais do PROC-042, o chunk inteiro fica em ~200 tokens, dentro do orçamento.

### 1.2. PDFs escaneados (~15% da base)

- **Desafio:** Documentos digitalizados são imagens, não texto pesquisável. Exigem OCR. OCR erra mais em documentos antigos, mal escaneados ou com tabelas e selos sobrepondo o texto.
- **Impacto na resposta:** Erros de OCR criam chunks ruidosos — `clase 1 a 6` vira `classe 1 ao 6 da ANTI` (em vez de `ANTT`). Quando o modelo recupera esses chunks, propaga o erro para a resposta ou se confunde no matching semântico durante a busca.
- **Estratégia:** Usar OCR moderno baseado em transformer (Azure AI Vision / Document Intelligence). Aplicar etapa de **validação pós-OCR** com regras de domínio (vocabulário esperado: ANTT, CT-e, classes de carga). Marcar chunks com baixa confiança e excluí-los do índice principal — ou indexá-los com peso reduzido.

### 1.3. Wiki Confluence (~400 páginas com links internos e macros)

- **Desafio:** A wiki tem links cruzados entre páginas e macros customizadas (calendários, queries Jira, conteúdo dinâmico). A extração padrão preserva texto, mas os links viram **texto solto sem referência**, e macros produzem HTML que polui o chunk com ruído estrutural.
- **Impacto na resposta:** Quando um chunk diz "ver procedimento em [link]", o assistente não consegue resolver o link e responde de forma incompleta. Ainda pior: o usuário não percebe a lacuna.
- **Estratégia:** Ingestão via API do Confluence (não scraping HTML). Resolver links durante a ingestão, substituindo por **referência textual qualificada** (`ver PROC-042-v2, seção 2`). Macros são processadas separadamente — calendários e queries dinâmicas vão para uma camada de ferramentas (MCP), não para o índice estático.

### 1.4. Planilhas (~50 XLSX com fórmulas interdependentes)

- **Desafio:** Planilhas vivem da relação entre células. A célula `B5` mostra `R$ 1.200,00` mas isso é o resultado de `=A5*$C$1*Tabela!E3` — fórmula que depende de outra aba. Conversão direta para CSV/texto **perde a lógica** e congela o valor naquele instante.
- **Impacto na resposta:** O assistente responde com valores desatualizados ou com base em uma fórmula que ele não compreende. Risco operacional: cliente recebe cotação errada.
- **Estratégia:** Avaliar todas as fórmulas no momento da ingestão e indexar **o resultado calculado**, com metadado da fonte e timestamp da última atualização. Para planilhas com lógica complexa (cálculos de SLA derivados, tabelas de preço), considerar **não indexar** e expor como ferramenta via MCP — o agente chama uma função, não consulta texto. Anthropic descreve exatamente esse padrão: *just-in-time retrieval com identificadores leves* [2].

---

## 2. Estimativa do tamanho da base em tokens

Aplicando a regra prática `tokens ≈ palavras / 0,75` aos dados fornecidos:

| Fonte | Volume | Palavras estimadas | Tokens estimados |
| :--- | :--- | ---: | ---: |
| PDFs (SharePoint) | 800 docs × ~10 páginas × ~500 palavras/página | 4.000.000 | **~5,3M** |
| Wiki (Confluence) | 400 páginas × ~1.500 palavras | 600.000 | **~0,8M** |
| Planilhas | 50 × ~3.000 palavras equivalentes | 150.000 | **~0,2M** |
| | **Total** | **4.750.000** | **~6,3M tokens** |

**Ressalva importante sobre português:** A regra `1 token ≈ 0,75 palavras` é calibrada em inglês. A documentação da NovaTech é toda em português, que produz **mais tokens por palavra** devido a acentuação, contrações e sufixos morfológicos [3]. Uma estimativa mais conservadora para PT-BR seria multiplicar o total por **~1,2**, levando a base para aproximadamente **7,5M tokens**. Este é o número que deve ser usado no dimensionamento real.

A base total é portanto **da ordem de 60x maior** que a janela do GPT-4o (128K) e **35x maior** que a do Claude Sonnet 4.6 (200K). Confirma-se que carregar a base inteira no contexto é tecnicamente impossível, e que a única arquitetura viável passa por **recuperação seletiva** (RAG).

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

O cálculo acima ignora que LLMs **não atendem uniformemente** a tokens ao longo do contexto. Pesquisa estabelecida (Stanford / UC Berkeley, 2023, ainda válida em 2026) mostra que modelos atendem com força ao **início e ao fim** do contexto, mas a precisão cai **até 30%** quando a informação fica no meio [3][4]. Como afirma a Anthropic, *"every new token introduced depletes [the attention] budget by some amount"* [2].

Resultado prático: o orçamento útil **não é 250 chunks, são entre 5 e 15 chunks bem ranqueados**, posicionados estrategicamente.

### 3.3. *Context rot* em conversas multi-turn

Em interações de múltiplos turnos — exatamente o caso de um chatbot no Teams — surge um segundo problema, cunhado pela Chroma como *context rot*:

> *"When a large context gets operated on repeatedly, for example in multi-turn agent interactions, the context rots, and the model effectively loses its mind, most seriously the failure to follow clearly-stated instructions."* — Jeff Huber, CEO da Chroma [5]

A equipe da Manus, ao construir um agente em produção, confirmou o que pesquisadores chamam de "segredo sujo" do setor: *"128K+ is insufficient for real-world scenarios despite apparent capacity"* [6]. Em outras palavras, **janela maior não resolve o problema** — só esconde até a próxima escala.

### 3.4. Implicações arquiteturais

O orçamento prático recomendado para o assistente da NovaTech é:

| Componente | Tokens | % da janela |
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

A escolha de chunking é onde decisões aparentemente técnicas se traduzem diretamente em qualidade de resposta. A recomendação para a NovaTech, justificada pelo tipo de pergunta esperada e pelos efeitos descritos na seção 3, é:

### 4.1. Granularidade — 256 a 512 tokens

Os documentos da NovaTech são **normativos** (POL-001, PROC-042, PROC-042-v2, SLA-2024) e estruturados em seções curtas. Chunks de 256–512 tokens preservam uma seção semanticamente fechada (uma regra de devolução, uma faixa de SLA, uma faixa da tabela de multiplicadores) sem inflar com texto irrelevante. Estudos da Chroma mostram que *recursive splitting* a ~400 tokens entrega **85–90% de recall**; abordagens mais sofisticadas como *semantic chunking* sobem para 91–92% mas custam embeddings adicionais em ingestão.

### 4.2. Boundaries — heading-based, com regra dura para tabelas

A divisão deve ocorrer em **fronteiras semânticas** (headers Markdown H2/H3, seções numeradas, parágrafos de início de regra). Quebras cegas por contagem de caracteres são rejeitadas — cortam frases no meio e perdem contexto.

**Regra absoluta:** tabelas nunca são divididas. A tabela inteira de multiplicadores regionais do PROC-042 é um único chunk, mesmo que ultrapasse 512 tokens. Tabela cortada dá resposta numericamente errada.

### 4.3. Overlap — 10 a 15%, tunável

A prática consagrada recomenda 10–15% de overlap para evitar perda de informação em fronteiras. Pesquisa de janeiro de 2026 (arXiv) sugere que em alguns setups o overlap **não traz ganho mensurável** e apenas eleva o custo de indexação. Postura recomendada: **começar em 10%**, medir recall com o conjunto de testes do Anexo B, ajustar.

### 4.4. Recuperação e re-ranking — combater o *lost in the middle*

A estratégia de recuperação precisa fechar com o orçamento da seção 3:

- Recuperar **top-20 chunks** por similaridade vetorial.
- Aplicar **re-ranker** (cross-encoder) para refinar a ordem.
- Selecionar os **5–8 melhores** para enviar ao LLM.
- Posicionar o chunk mais relevante **por último** no prompt — explorando o viés de recência e fugindo do meio do contexto.
- Para perguntas multi-domínio (ex: "qual o SLA do meu cliente Gold para devolução de carga perigosa?"), executar **múltiplas sub-queries** e juntar — padrão Agentic RAG descrito pela Microsoft [1].

### 4.5. Tratamento explícito de versões contraditórias

A documentação da NovaTech traz casos como PROC-042 (v1) e PROC-042-v2 com multiplicadores diferentes e **sem indicação clara de qual é o vigente**. A estratégia de chunking precisa preservar metadados de versão (data, status, número de revisão) em cada chunk. No prompt do modelo, a instrução deve ser explícita: *quando dois chunks tratarem do mesmo procedimento com regras diferentes, apresentar ambas as versões com data de vigência, nunca silenciosamente escolher uma*. Isso é decisão de produto, mas o pipeline precisa **expor a contradição**, não esconder.

---

## 5. Conclusão

O projeto é viável. Os limites de janela de contexto e os efeitos cognitivos dos LLMs (lost in the middle, context rot) são reais e bem documentados — mas conhecidos. As decisões arquiteturais aqui defendidas — pipeline de ingestão sensível ao tipo de fonte, orçamento de contexto enxuto, chunking por fronteira semântica, re-ranking, tratamento explícito de versões — endereçam esses limites diretamente.

O maior risco do projeto **não é o LLM**: é a qualidade da base. Documentos contraditórios, ausência de versionamento explícito e curadoria mensal por três áreas sem revisão unificada são problemas de processo, não de modelo. A camada técnica do RAG pode mitigá-los (mostrando contradições, marcando documentos obsoletos), mas a solução completa exige acordo com Operações, Compliance e Comercial sobre processo de curadoria.

**Recomendação final:** seguir com o projeto. Próximos passos sugeridos antes do desenvolvimento:

1. Prova de conceito de extração com 20 documentos representativos de cada tipo (PDFs com tabela, escaneados, wiki, planilha) — validar a hipótese de chunking proposta com o conjunto do Anexo B.
2. Definição com o Product Specialist de como o assistente comunica contradições ao usuário.
3. Conversa com Operações, Compliance e Comercial para alinhar um padrão mínimo de versionamento na origem.

---

## Referências

[1] Microsoft Learn — *RAG (Geração Aumentada por Recuperação) e índices em Microsoft Foundry* (PT-BR). [Link](https://learn.microsoft.com/pt-br/azure/foundry/concepts/retrieval-augmented-generation)
[2] Anthropic — *Effective Context Engineering for AI Agents* (set/2025). [Link](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
[3] Data Science Academy — *A Janela de Contexto dos LLMs* (PT-BR). [Link](https://blog.dsacademy.com.br/a-janela-de-contexto-dos-llms-o-que-e-por-que-importa-e-quais-sao-seus-limites/)
[4] Liu et al. — *Lost in the Middle: How Language Models Use Long Contexts* (Stanford/UC Berkeley, 2023).
[5] Jeff Huber (Chroma) — *Context Engineering for Engineers* (Y Combinator). [Link](https://www.youtube.com/watch?v=3jN77Aw7Utk)
[6] Manus — *Context Engineering for AI Agents: Lessons from Building Manus*. [Link](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

Bibliografia completa: ver [`referencias.md`](./referencias.md).
