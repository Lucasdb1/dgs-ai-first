# Referências — Exercício 1.1

Bibliografia oficial da Trilha AI First (DGS) consolidada com as notas técnicas extraídas em 16/06/2026 para fundamentar a análise de viabilidade.

> Tudo aqui sai do PDF *Trilha de Formação — DGS AI First* (publicado por Roberto Padilha em 26/05/2026) — Blocos 1, 3 e 4, que cobrem os tópicos do Cenário 1.

---

## 1 · Bloco 1 — Fundamentos de IA Generativa

### Vídeos oficiais da trilha

| Título | Idioma | Link |
| :--- | :--- | :--- |
| Andrej Karpathy — *Intro to Large Language Models* (1h) | EN | [youtube.com/watch?v=zjkBMFhNj_g](https://www.youtube.com/watch?v=zjkBMFhNj_g) |
| 3Blue1Brown — *But what is a GPT? Visual intro to Transformers* (27min) | EN | [youtube.com/watch?v=wjZofJX0v4M](https://www.youtube.com/watch?v=wjZofJX0v4M) |
| Fabio Akita — *Entendendo COMO ChatGPT Funciona* | PT-BR | [youtube.com/watch?v=O68y0yRZL1Y](https://www.youtube.com/watch?v=O68y0yRZL1Y) |

### Material escrito

- Google for Developers — *Introduction to LLMs* (ML Crash Course): <https://developers.google.com/machine-learning/crash-course/llm>
- 3Blue1Brown — *Large Language Models explained briefly*: <https://www.3blue1brown.com/lessons/mini-llm/>
- Data Science Academy — *A Janela de Contexto dos LLMs* (PT-BR): <https://blog.dsacademy.com.br/a-janela-de-contexto-dos-llms-o-que-e-por-que-importa-e-quais-sao-seus-limites/>

### Notas técnicas extraídas

**Karpathy — "Intro to LLMs"**
- O "pensamento" de um LLM acontece **token a token** — ele não pensa silenciosamente, gera tokens em sequência.
- A janela de contexto é a **memória de trabalho** do modelo. Parâmetros guardam memória vaga (como algo lido há um mês); o contexto é memória recente, fresca.
- Janela muito curta → o modelo "alucina" e gera respostas off-target.
- Treinamento usa janelas de tokens do dataset, tipicamente até **8.000 tokens**.

**Data Science Academy — "A Janela de Contexto dos LLMs" (PT-BR)** — *Citável diretamente no documento por ser PT-BR.*
- Tokens não são palavras: em **inglês**, 1 token ≈ 0,75 palavras. Em **português**, há **mais tokens por palavra** devido à acentuação e à estrutura morfológica — relevante para a estimativa da NovaTech, cuja documentação é toda em PT-BR.
- Evolução: GPT-3 (2022) tinha 2.048 tokens; modelos atuais chegam a milhões. **200 mil tokens ≈ 500 páginas de livro.**
- *Lost in the middle* citado: pesquisa de Stanford mostra **queda de até 30%** na qualidade quando a informação está no meio do contexto.
- Implicação direta para RAG: **a ordem dos chunks importa muito.**

---

## 2 · Bloco 3 — Engenharia de Contexto

### Vídeos oficiais da trilha

| Título | Idioma | Link |
| :--- | :--- | :--- |
| Y Combinator — *Context Engineering for Engineers* (com Jeff Huber, CEO da Chroma) | EN | [youtube.com/watch?v=3jN77Aw7Utk](https://www.youtube.com/watch?v=3jN77Aw7Utk) |
| Tina Huang — *Context Engineering Clearly Explained* | EN | [youtube.com/watch?v=jLuwLJBQkIs](https://www.youtube.com/watch?v=jLuwLJBQkIs) |
| LangChain — *How to apply context engineering* | EN | [youtube.com/watch?v=nyKvyRrpbyY](https://www.youtube.com/watch?v=nyKvyRrpbyY) |
| Shaw Talebi — *Context Engineering Explained — 5 Practical Tips* | EN | [youtube.com/watch?v=zKHSpwayPBU](https://www.youtube.com/watch?v=zKHSpwayPBU) |

### Material escrito (★ referências primárias)

- ★ **Anthropic — *Effective context engineering for AI agents*** (set/2025): <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- Anthropic — *Effective harnesses for long-running agents*: <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
- Manus — *Context Engineering for AI Agents: Lessons from Building Manus*: <https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus>
- Fabio Olivei — *Engenharia de Contexto VS Prompt Engineering em LLMs* (PT-BR): <https://medium.com/@fabioolivei/engenharia-de-contexto-vs-prompt-engineering-em-llms-c461a2e4bd10>

### Notas técnicas extraídas

**Anthropic — *Effective context engineering for AI agents*** *(referência primária do tema, citável)*

Princípio orientador:
> *"Find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome."*

- **Orçamento de atenção (attention budget):** o transformer cria n² relacionamentos pareados — cada novo token consome esse orçamento.
  > *"Every new token introduced depletes this budget by some amount, increasing the need to carefully curate the tokens available to the LLM."*
- **Context rot:** a recuperação cai conforme o contexto cresce. Não é cliff abrupto, é **gradiente de degradação**. Modelos têm menos experiência com sequências longas porque o treinamento favorece sequências curtas.
- **System prompts:** buscar a "altitude ótima" — específico o bastante para guiar, flexível o bastante para virar heurística. Evitar dois extremos: lógica hardcoded frágil ↔ orientações vagas.
- **Tool sets:** mínimo e não-redundante. *"If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better."*
- **Just-in-time retrieval:** manter identificadores leves (paths, queries) e carregar dados dinamicamente em runtime — espelha a cognição humana (não memorizamos corpora inteiros, usamos índices externos).
- **Progressive disclosure:** descobrir contexto incrementalmente. Metadados (hierarquia de pastas, naming, timestamps) dão sinal comportamental.
- **Compaction:** resumir conversa perto do limite, reiniciar janela com resumo. Preservar decisões, bugs em aberto, detalhes de implementação. Limpeza de tool results = forma mais leve e segura.
- **Structured note-taking:** agente escreve notas fora da janela e recupera depois. Permite rastrear progresso em tarefas longas.
- **Sub-agent architectures:** agentes especializados, janelas limpas. Principal coordena; sub-agentes devolvem resumos condensados **(1.000–2.000 tokens)**.

**Manus — *Context Engineering Lessons*** *(experiência de produção)*

- **KV-cache hit rate** é "a métrica mais importante de um agente em produção". Mantenha prefixos estáveis. Cache hit dá **redução de 10x no custo** (em Claude Sonnet: $0,30/MTok cacheado vs $3/MTok não cacheado).
- Tasks típicas no Manus: **~50 tool calls** por tarefa complexa. Razão input/output **≈ 100:1** (heavily prefill-skewed).
- **Mask, don't remove:** não adicione/remova ferramentas no meio da iteração — invalida cache. Use logit masking via state machine.
- **Filesystem como memória externa:** trate-o como contexto "ilimitado e persistente". Permite compressão restaurável (preservar URL/path, descartar conteúdo).
- **Recitation:** reescrever a todo list a cada passo empurra objetivos pro contexto recente — reduz lost-in-the-middle em tarefas longas.
- **Preserve errors:** mantenha falhas e stack traces no contexto. *"Error recovery is a core indicator of true agentic behavior."*
- **Few-shot armadilha:** padrões uniformes causam overfitting do agente. Introduza variação controlada.
- Veredito: **128K+ não é suficiente** para cenários reais, apesar da capacidade aparente.

**Anthropic — *Effective harnesses for long-running agents***

- Sessões de agentes são discretas — sem memória entre elas. Analogia: *"engineers working in shifts, each new engineer arrives with no memory of what happened on the previous shift."*
- Padrão de duas peças: **initializer** (cria ambiente, `init.sh`, `claude-progress.txt`, feature list de 200+ itens) + **coding agent** (trabalha feature por feature, commita, atualiza progress).
- Git como **mecanismo de recovery**. Toda sessão começa lendo logs e progress files.
- Validação por **browser automation (Puppeteer MCP)** — unit tests sozinhos foram insuficientes.

**Jeff Huber (CEO Chroma) — *Context Engineering for Engineers*** *(YC, citado nominalmente no exercício)*

- Frase-bandeira: *"RAG is dead, context engineering is king."* Ele **detesta o termo RAG** e prefere "context engineering" como framing.
- Definição de **context rot** (cunhada pela Chroma): *"When a large context gets operated on repeatedly, for example in multi-turn agent interactions, the context rots, and the model effectively loses its mind, most seriously the failure to follow clearly-stated instructions."*
- "Dirty little secret" da indústria: janelas maiores **não eliminam o problema**, só escondem.
- Chroma se posiciona como "modern search infrastructure for AI", **não vector database**.

---

## 3 · Bloco 4 — RAG e MCP

### Vídeos oficiais da trilha

| Título | Idioma | Link |
| :--- | :--- | :--- |
| IBM Technology — *What is Retrieval-Augmented Generation (RAG)?* (Marina Danilevsky, ~7min) | EN | [youtube.com/watch?v=T-D1OfcDW1M](https://www.youtube.com/watch?v=T-D1OfcDW1M) |
| Anthropic — *The Model Context Protocol (MCP)* (oficial) | EN | [youtube.com/watch?v=CQywdSdi5iA](https://www.youtube.com/watch?v=CQywdSdi5iA) |
| Código Fonte TV — *RAG // Dicionário do Programador* | PT-BR | [youtube.com/watch?v=eHEHE2fpnWQ](https://www.youtube.com/watch?v=eHEHE2fpnWQ) |
| *Model Context Protocol: Guia que todo Dev precisa saber* | PT-BR | [youtube.com/watch?v=wxD8MaD0xXk](https://www.youtube.com/watch?v=wxD8MaD0xXk) |

### Material escrito

- IBM — *What is RAG?*: <https://www.ibm.com/think/topics/retrieval-augmented-generation>
- ★ **Microsoft Learn — *Índices e geração aumentada de recuperação (RAG)* (PT-BR):** <https://learn.microsoft.com/pt-br/azure/foundry/concepts/retrieval-augmented-generation>
- Model Context Protocol — Documentação oficial: <https://modelcontextprotocol.io/>
- Anthropic — *Introducing the Model Context Protocol* (blog post de lançamento): <https://www.anthropic.com/news/model-context-protocol>

### Notas técnicas extraídas

**Marina Danilevsky (IBM) — *What is RAG?*** *(citável para a definição de RAG na introdução do documento)*

- Dois ganhos principais do RAG: (1) o modelo recebe **fatos atuais e confiáveis**; (2) é possível **mostrar de onde a resposta veio** (citação de fonte) → credibilidade.
- LLMs erram com confiança porque dependem dos dados de treino, que envelhecem.
- RAG = **content store + recuperação + combinação com a pergunta** antes da geração.
- Benefícios: reduz alucinação, reduz vazamento de dados de treino, mantém o LLM atualizado **sem retreino**.

**Microsoft Learn — *RAG no Azure Foundry* (PT-BR)** *(citável para qualquer afirmação sobre o stack Azure da NovaTech)*

Fluxo canônico em três etapas:
1. **Recuperar** — consultar índice/data store por conteúdo relevante.
2. **Augment** — combinar pergunta + conteúdo recuperado em um prompt.
3. **Gerar** — modelo responde com base no prompt aumentado.

Conceitos-chave:
- **Dados de fundamentação (grounding):** conteúdo recuperado fornecido ao modelo.
- **Índice:** estrutura otimizada para recuperação — palavra-chave, semântica, vetor ou híbrida.
- **Embeddings:** representação numérica para busca por similaridade.

Modos de pesquisa disponíveis: keyword, semântica, vetor, **híbrida (kw + vetor + ranking semântico)**.

**Agentic RAG** (evolução): modelo decompõe entrada complexa em sub-consultas, executa em paralelo, retorna dados estruturados com citações e metadados — melhor para multi-turn, ranqueamento semântico interno.

Quando usar:
- **RAG** → respostas fundamentadas em dados privados ou que mudam com frequência.
- **Fine-tuning** → mudar comportamento/estilo, **não** adicionar conhecimento novo.

Riscos explicitamente listados pela Microsoft:
- Qualidade do RAG depende da preparação do conteúdo, do chunking e do design do prompt — **má preparação afeta diretamente a qualidade**.
- Trate conteúdo recuperado como **entrada não-confiável** (risco de prompt injection).
- Custos extras: recuperação, embeddings em ingest e query, tokens de input maiores.
- Limitações conhecidas:
  - **Qualidade ruim de recuperação** → revisar chunking, modelo de embedding, modo de pesquisa.
  - **Alucinação apesar do grounding** → ativar citações, instruir o modelo a usar o conteúdo recuperado.
  - **Latência** → indexação, filtragem, reordenação.
  - **Orçamento de tokens estourado** → filtragem de trechos, ranqueamento, sumarização.

---

## 4 · Mapeamento referência × seção do Exercício 1.1

| Seção do documento | Referência primária | Suporte adicional |
| :--- | :--- | :--- |
| **1. Desafios por tipo de fonte** | Microsoft Learn (limitações conhecidas, prompt injection) | IBM RAG (necessidade de content store curado) |
| **2. Estimativa de tokens** | Data Science Academy (PT-BR: 1 token ≈ 0,75 palavras, mais tokens em PT que em EN) | Karpathy (tokenização) |
| **3. Orçamento de contexto** | Anthropic *Effective context engineering* (attention budget, n², context rot) | Manus (128K não basta), Jeff Huber (RAG is dead, context rot é o real gargalo), Data Science Academy (lost in the middle 30%) |
| **4. Estratégia de chunking** | Microsoft Learn (chunking → qualidade) | Anthropic (just-in-time retrieval, progressive disclosure), Manus (filesystem como memória externa) |

---

## 5 · Vocabulário citável (em ordem alfabética)

| Termo | Definição operacional | Origem |
| :--- | :--- | :--- |
| **Attention budget** | Orçamento finito de atenção do transformer; cada token compete por ele | Anthropic |
| **Context rot** | Degradação da qualidade da resposta conforme o contexto cresce, especialmente em loops multi-turn | Chroma / Jeff Huber |
| **Grounding** | Ato de ancorar a resposta do LLM em dados externos verificáveis | Microsoft |
| **Just-in-time retrieval** | Carregar dados em runtime conforme necessário, em vez de pré-carregar tudo | Anthropic |
| **KV-cache hit rate** | % de tokens reutilizados do cache em chamadas sucessivas; métrica de custo | Manus |
| **Lost in the middle** | Queda de até 30% na precisão quando a informação fica no meio do contexto | Stanford → DSA / Anthropic |
| **Progressive disclosure** | Descobrir contexto incrementalmente; alimentar o modelo em etapas | Anthropic |
| **Recitation** | Repetir objetivos no contexto recente para combater lost-in-the-middle | Manus |
| **RAG (Retrieval-Augmented Generation)** | Padrão de recuperar antes de gerar; reduz alucinação e permite citação | IBM / Microsoft |
| **Sub-agent isolation** | Subagentes com janelas limpas; principal recebe só o resumo condensado | Anthropic |

---

## 6 · Referências cruzadas para os exercícios 1.2 e 1.3

Estas referências também servem aos próximos exercícios — ficam aqui catalogadas para evitar duplicação:

- **DAIR.AI — Prompt Engineering Guide** (Exercício 1.2): <https://www.promptingguide.ai/>
- **Anthropic — Prompt Engineering Documentation** (Exercício 1.2): <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview>
- **Google — Prompt Engineering Whitepaper v4** (Exercício 1.2, model-agnostic): <https://cloud.google.com/discover/what-is-prompt-engineering>
- **Anthropic — Introducing MCP** (Exercício 1.3 → conceito): <https://www.anthropic.com/news/model-context-protocol>
- **MCP Docs** (Exercício 1.3): <https://modelcontextprotocol.io/>
