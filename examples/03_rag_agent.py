"""
Exempel 3: RAG (Retrieval Augmented Generation) med Microsoft Agent Framework

Detta exempel visar hur man implementerar RAG med:
- Function tools för dokumenthämtning
- Enkel vektor-sökning
- Citering av källor i svar
"""

import asyncio
from typing import Annotated, List
from pydantic import Field
from pathlib import Path


# Simulerad dokument-databas
DOCUMENTS = {
    "doc1": {
        "title": "Microsoft Agent Framework Översikt",
        "content": """Microsoft Agent Framework (MAF) är det nya ramverket som förenar
        Semantic Kernel och AutoGen. Det erbjuder enhetligt API, minneshantering,
        RAG-stöd, middleware och workflow orchestration."""
    },
    "doc2": {
        "title": "Minneshantering i MAF",
        "content": """MAF stödjer både kortidsminne (Threads) och långtidsminne
        (ChatMessageStore). Threads används för sessionsbaserad kontext, medan
        ChatMessageStore ger persistent lagring mellan sessioner."""
    },
    "doc3": {
        "title": "Workflows i MAF",
        "content": """MAF har kraftfull workflow orchestration med stöd för
        sequential, parallel och conditional execution. MagenticBuilder används
        för att orkestrera multi-agent samarbete."""
    }
}


def search_documents(
    query: Annotated[str, Field(description="Sökfrågan för att hitta relevanta dokument")]
) -> str:
    """
    Sök efter relevanta dokument baserat på query.
    Denna funktion kan anropas av agenten för att hämta information.
    """
    print(f"\n🔍 Söker dokument för: '{query}'")

    # Enkel keyword-baserad sökning (i produktion: använd vector search)
    results = []
    query_lower = query.lower()

    for doc_id, doc in DOCUMENTS.items():
        content_lower = doc["content"].lower()
        title_lower = doc["title"].lower()

        # Räkna matchningar
        score = content_lower.count(query_lower[:10]) + title_lower.count(query_lower[:10]) * 2

        if score > 0 or any(word in content_lower for word in query_lower.split()):
            results.append((score, doc))

    # Sortera efter score
    results.sort(reverse=True, key=lambda x: x[0])

    # Returnera top 2 resultat
    if not results:
        return "Inga relevanta dokument hittades."

    output = "Hittade följande relevanta dokument:\n\n"
    for _, doc in results[:2]:
        output += f"**{doc['title']}**\n{doc['content']}\n\n"

    print(f"   ✅ Returnerade {min(2, len(results))} dokument")
    return output


async def main():
    """Huvudfunktion som demonstrerar RAG."""
    print("\n" + "=" * 80)
    print("  📚 Exempel 3: RAG - Retrieval Augmented Generation")
    print("=" * 80)

    print("""
Microsoft Agent Framework stödjer RAG genom Function Tools.
Agenten kan anropa funktioner för att hämta relevant information.

Detta exempel visar:
1. Definiera function tools för dokumentsökning
2. Agenten anropar tools automatiskt vid behov
3. Svar baseras på hämtad information
    """)

    # Försök importera agent framework
    try:
        from agent_framework import ChatAgent
        from agent_framework.openai import OpenAIChatClient
        has_framework = True
    except ImportError:
        print("\n⚠️  agent-framework är inte installerat.")
        print("   Installera med: pip install agent-framework --pre\n")
        await demo_simulated()
        return

    # Försök skapa agent
    try:
        chat_client = OpenAIChatClient(model_id="gpt-4o-mini")

        # Skapa agent med search tool
        agent = ChatAgent(
            chat_client=chat_client,
            instructions="""Du är en expert på Microsoft Agent Framework.
            Använd search_documents funktionen för att hitta information när användaren ställer frågor.
            Citera alltid källor i dina svar.""",
            tools=search_documents  # Ge agenten tillgång till search-funktionen
        )
        print("\n✅ RAG Agent skapad med search tool\n")

    except Exception as e:
        print(f"\n⚠️  Kunde inte skapa agent: {e}")
        print("   Konfigurera OPENAI_API_KEY i .env-filen\n")
        await demo_simulated()
        return

    # Demo: Ställ frågor som kräver dokumenthämtning
    print("\n" + "-" * 80)
    print("  ❓ Demo: Frågor med RAG")
    print("-" * 80 + "\n")

    questions = [
        "Vad är Microsoft Agent Framework?",
        "Hur fungerar minneshantering i MAF?",
        "Berätta om workflows i MAF",
    ]

    for question in questions:
        print(f"👤 Användare: {question}")
        print()

        # Agenten kommer automatiskt anropa search_documents om behövs
        response = await agent.run(question)

        print(f"\n🤖 Agent: {response.text}\n")
        print("-" * 80 + "\n")
        await asyncio.sleep(1)

    print("\n" + "=" * 80)
    print("  ✅ Exempel Avslutat")
    print("=" * 80)
    print("""
Lärdomar:
✓ Function tools ger agenten tillgång till extern data
✓ Agenten bestämmer själv när den behöver anropa tools
✓ RAG minskar hallucinations och ger faktabaserade svar
✓ Källor kan citeras för transparens

I Produktion:
→ Använd vektor-databaser (Qdrant, ChromaDB, Azure AI Search)
→ Implementera proper embeddings med Azure OpenAI
→ Chunka dokument för bättre precision
→ Lägg till re-ranking för bättre resultat
→ Implementera hybrid search (keyword + semantic)

Example med vector search:
```python
from qdrant_client import QdrantClient
from openai import OpenAI

def vector_search(query: str) -> str:
    # Skapa embedding för query
    embedding = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    ).data[0].embedding

    # Sök i Qdrant
    results = qdrant.search(
        collection_name="documents",
        query_vector=embedding,
        limit=3
    )

    return format_results(results)
```

För att ladda dokument i MAF:
→ Chunka dokument (500-1000 tokens per chunk)
→ Skapa embeddings för varje chunk
→ Lagra i vektor-databas med metadata
→ Indexera för snabb retrieval
    """)


async def demo_simulated():
    """Simulerad demo."""
    print("""
RAG-processen:
1. Användare ställer fråga: "Vad är MAF?"
2. Agent anropar search_documents("MAF")
3. Dokument hämtas från databas
4. Agent genererar svar baserat på hämtad info
5. Svar inkluderar källciteringar

Exempel output:
"Microsoft Agent Framework (MAF) är det nya ramverket som förenar
Semantic Kernel och AutoGen [Källa: MAF Översikt]"
    """)


if __name__ == "__main__":
    asyncio.run(main())
