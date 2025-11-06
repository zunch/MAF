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
- Python 3.10 eller högre
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

### Steg 3: Installera beroenden
```bash
pip install -r requirements.txt
```

### Steg 4: Konfigurera miljövariabler
Skapa en `.env`-fil i root-katalogen:

```env
# Azure OpenAI (rekommenderat)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Eller OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# För långtidsminne och RAG (valfritt)
QDRANT_URL=http://localhost:6333
CHROMA_PATH=./chroma_db
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

- **Microsoft Agent Framework** - Huvudramverket
- **Azure OpenAI / OpenAI** - LLM-provider
- **Qdrant/ChromaDB** - Vektor-databaser för minne och RAG
- **LangChain** - Kompletterande verktyg för RAG
- **Pydantic** - Datavalidering

## Lär dig mer

- [Microsoft Agent Framework Dokumentation](https://docs.microsoft.com/azure/ai-services/agents/)
- [Azure AI Agent Service](https://azure.microsoft.com/services/ai-agent-service/)
- [Migreringsguide från Semantic Kernel](https://docs.microsoft.com/azure/ai-services/agents/migration)

## Licens

MIT License

## Bidrag

Bidrag är välkomna! Öppna gärna issues eller pull requests.
