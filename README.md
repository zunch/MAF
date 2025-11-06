# Microsoft Agent Framework - Exempel

Detta repository innehåller exempel som demonstrerar funktionaliteten i Microsoft Agent Framework (MAF), det nya ramverket som ersätter och förenar Semantic Kernel och AutoGen.

## Översikt

Microsoft Agent Framework är nästa generation av Microsofts AI-agent-ramverk, designat för att bygga intelligenta, autonoma agenter med avancerade funktioner som minne, RAG, och komplex arbetsflödesorkestrering.

## Exempel

### 1. Kortidsminne (Short-term Memory)
**Fil:** `examples/01_short_term_memory.py`

Visar hur man:
- Skapar en agent med kortidsminne
- Håller kontext under en konversation
- Använder sessionsbaserat minne

### 2. Långtidsminne (Long-term Memory)
**Fil:** `examples/02_long_term_memory.py`

Visar hur man:
- Implementerar persistent minneslagring
- Använder vektor-databaser för semantisk sökning
- Hämtar relevant historik från tidigare konversationer

### 3. RAG (Retrieval Augmented Generation)
**Fil:** `examples/03_rag_agent.py`

Visar hur man:
- Indexerar dokument för retrieval
- Skapar en RAG-pipeline
- Kombinerar hämtad information med generering
- Använder embeddings och vektor-sökning

### 4. Middleware
**Fil:** `examples/04_middleware.py`

Visar hur man:
- Skapar custom middleware-komponenter
- Loggar och övervakar agent-beteende
- Implementerar rate limiting
- Lägger till säkerhetslager

### 5. Workflows
**Fil:** `examples/05_workflows.py`

Visar hur man:
- Skapar komplexa multi-step workflows
- Orkestrerar flera agenter
- Hanterar villkorlig logik och förgreningar
- Implementerar felhantering och retry-logik

## Installation

### Förutsättningar
- **Python 3.10 eller högre** (Microsoft Agent Framework kräver Python >=3.10)
- Azure OpenAI eller OpenAI API-nyckel

### Steg 1: Klona repository
```bash
git clone <repository-url>
cd MAF
```

### Steg 2: Skapa virtuell miljö
```bash
python -m venv venv
source venv/bin/activate  # På Windows: venv\Scripts\activate
```

### Steg 3: Installera Microsoft Agent Framework
```bash
# Installera agent-framework (kräver --pre eftersom det är i preview)
pip install agent-framework --pre

# Installera övriga beroenden
pip install -r requirements.txt
```

**Obs!** Microsoft Agent Framework är för närvarande i public preview (version 1.0.0b251104).

### Steg 4: Konfigurera miljövariabler
Skapa en `.env`-fil i root-katalogen (eller använd `.env.example` som mall):

```env
# Azure OpenAI (Rekommenderat)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21

# Eller OpenAI (Alternativ)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL_ID=gpt-4o-mini

# Eller Azure AI Project (för Azure AI Agent Service)
# AZURE_AI_PROJECT_ENDPOINT=https://your-project.api.azureml.ms
# AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o-mini
```

## Användning

Kör individuella exempel:

```bash
# Kortidsminne
python examples/01_short_term_memory.py

# Långtidsminne
python examples/02_long_term_memory.py

# RAG
python examples/03_rag_agent.py

# Middleware
python examples/04_middleware.py

# Workflows
python examples/05_workflows.py
```

## Projektstruktur

```
MAF/
├── README.md
├── requirements.txt
├── .env.example
├── examples/
│   ├── 01_short_term_memory.py
│   ├── 02_long_term_memory.py
│   ├── 03_rag_agent.py
│   ├── 04_middleware.py
│   └── 05_workflows.py
├── shared/
│   ├── __init__.py
│   ├── config.py
│   └── utils.py
└── data/
    └── sample_documents/
        ├── doc1.txt
        ├── doc2.txt
        └── doc3.txt
```

## Teknologier

- **Microsoft Agent Framework (`agent-framework`)** - Det nya ramverket från Microsoft (nov 2025)
  - Python SDK för att bygga AI-agenter
  - Förenar Semantic Kernel och AutoGen
  - Stöd för Threads, ChatMessageStore, ContextProviders, MagenticBuilder
- **Azure OpenAI / OpenAI** - LLM-providers
  - `AzureOpenAIChatClient`, `AzureAIAgentClient`, eller `OpenAIChatClient`
- **Pydantic** - Datavalidering och settings
- **Python 3.10+** - Krävs av agent-framework

**Valfritt (för avancerade exempel):**
- Redis - För RedisChatMessageStore
- Qdrant/ChromaDB - För vektor-baserat långtidsminne
- Mem0 - För semantiskt minne med Mem0Provider

## Lär dig mer

- [Microsoft Agent Framework Dokumentation](https://learn.microsoft.com/agent-framework/)
- [GitHub Repository](https://github.com/microsoft/agent-framework)
- [PyPI Package](https://pypi.org/project/agent-framework/)
- [Quick Start Guide](https://learn.microsoft.com/agent-framework/tutorials/quick-start)
- [Agent Memory Guide](https://learn.microsoft.com/agent-framework/user-guide/agents/agent-memory)
- [Azure AI Foundry Blog](https://devblogs.microsoft.com/foundry/introducing-microsoft-agent-framework-the-open-source-engine-for-agentic-ai-apps/)

## Licens

MIT License

## Bidrag

Bidrag är välkomna! Öppna gärna issues eller pull requests.
