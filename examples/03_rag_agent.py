"""
Exempel 3: RAG - Retrieval Augmented Generation

Detta exempel visar hur man implementerar en RAG-agent som kan:
- Indexera dokument i en vektor-databas
- Hämta relevant information baserat på frågor
- Generera svar som kombinerar hämtad kontext med LLM-kunskap
- Citera källor i svar
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Lägg till parent directory till path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import config
from shared.utils import setup_logging, print_section, chunk_text, calculate_similarity


@dataclass
class Document:
    """Representation av ett dokument."""
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    source: str


@dataclass
class DocumentChunk:
    """En chunk av ett dokument."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None


class DocumentStore:
    """Lagrar och indexerar dokument för RAG."""

    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.chunks: List[DocumentChunk] = []
        self.logger = setup_logging()

    def _create_simple_embedding(self, text: str) -> List[float]:
        """
        Skapa en enkel embedding för demonstration.
        I produktion: använd Azure OpenAI text-embedding-ada-002
        """
        # Extremt förenklad embedding för demo
        embedding = [0.0] * 20
        words = text.lower().split()[:20]
        for i, word in enumerate(words):
            embedding[i] = sum(ord(c) for c in word) / (len(word) * 255.0)
        return embedding

    def add_document(self, doc: Document, chunk_size: int = 500, overlap: int = 100) -> int:
        """
        Lägg till och indexera ett dokument.

        Args:
            doc: Dokumentet att lägga till
            chunk_size: Storlek på chunks
            overlap: Överlapp mellan chunks

        Returns:
            Antal chunks skapade
        """
        # Spara dokumentet
        self.documents[doc.id] = doc

        # Dela upp i chunks
        text_chunks = chunk_text(doc.content, chunk_size, overlap)

        # Skapa och indexera chunks
        for i, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                id=f"{doc.id}_chunk_{i}",
                document_id=doc.id,
                content=chunk_text,
                chunk_index=i,
                embedding=self._create_simple_embedding(chunk_text),
                metadata={
                    "title": doc.title,
                    "source": doc.source,
                    "chunk_index": i,
                    "total_chunks": len(text_chunks)
                }
            )
            self.chunks.append(chunk)

        self.logger.info(
            "document_indexed",
            doc_id=doc.id,
            chunks_created=len(text_chunks)
        )

        return len(text_chunks)

    def search(self, query: str, top_k: int = 3, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Sök efter relevanta chunks.

        Args:
            query: Sökfrågan
            top_k: Antal resultat att returnera
            threshold: Minsta similarity score

        Returns:
            Lista med relevanta chunks
        """
        query_embedding = self._create_simple_embedding(query)

        results = []
        for chunk in self.chunks:
            similarity = calculate_similarity(query_embedding, chunk.embedding)
            if similarity >= threshold:
                doc = self.documents[chunk.document_id]
                results.append({
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "similarity": similarity,
                    "source": doc.source,
                    "title": doc.title,
                    "metadata": chunk.metadata
                })

        # Sortera efter similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)

        self.logger.info("search_completed", query=query, results_found=len(results))

        return results[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Få statistik om document store."""
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "avg_chunks_per_doc": len(self.chunks) / len(self.documents) if self.documents else 0
        }


class RAGAgent:
    """Agent som använder Retrieval Augmented Generation."""

    def __init__(self):
        """Initiera RAG-agent."""
        self.document_store = DocumentStore()
        self.logger = setup_logging()
        self.llm_config = config.get_llm_config()

    def index_documents(self, documents: List[Document]) -> Dict[str, int]:
        """
        Indexera en lista av dokument.

        Args:
            documents: Lista med dokument att indexera

        Returns:
            Dict med statistik om indexeringen
        """
        total_chunks = 0
        for doc in documents:
            chunks = self.document_store.add_document(doc)
            total_chunks += chunks

        self.logger.info(
            "indexing_completed",
            documents_indexed=len(documents),
            total_chunks=total_chunks
        )

        return {
            "documents_indexed": len(documents),
            "total_chunks": total_chunks
        }

    async def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Ställ en fråga till RAG-agenten.

        Args:
            question: Frågan att besvara
            top_k: Antal dokument att hämta

        Returns:
            Dict med svar och metadata
        """
        # 1. Hämta relevanta dokument
        relevant_chunks = self.document_store.search(question, top_k=top_k)

        if not relevant_chunks:
            return {
                "answer": "Jag kunde inte hitta någon relevant information i dokumenten.",
                "sources": [],
                "context_used": False
            }

        # 2. Bygg kontext från hämtade chunks
        context_parts = []
        sources = []

        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(
                f"[Källa {i}: {chunk['title']}]\n{chunk['content']}\n"
            )
            sources.append({
                "title": chunk["title"],
                "source": chunk["source"],
                "similarity": chunk["similarity"]
            })

        context = "\n".join(context_parts)

        # 3. Generera svar (simulerat)
        # I produktion skulle du använda:
        # from azure.ai.agent import AgentRuntime
        # response = await runtime.run(
        #     prompt=f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        #     config=self.llm_config
        # )

        answer = self._generate_answer(question, relevant_chunks)

        self.logger.info(
            "query_completed",
            question=question,
            chunks_used=len(relevant_chunks)
        )

        return {
            "answer": answer,
            "sources": sources,
            "context": context,
            "context_used": True,
            "chunks_retrieved": len(relevant_chunks)
        }

    def _generate_answer(self, question: str, chunks: List[Dict]) -> str:
        """Generera svar baserat på fråga och hämtade chunks."""
        # Simulerad svarsgenerering för demonstration
        sources_text = ", ".join([c["title"] for c in chunks])
        return (
            f"Baserat på informationen från {sources_text}, "
            f"så kan jag besvara din fråga: '{question}'. "
            f"Jag hittade {len(chunks)} relevanta avsnitt i dokumenten."
        )


# Skapa exempel-dokument
SAMPLE_DOCUMENTS = [
    Document(
        id="doc1",
        title="Introduktion till Python",
        content="""
        Python är ett högnivå-programmeringsspråk som är känt för sin läsbarhet
        och enkla syntax. Det skapades av Guido van Rossum och släpptes första
        gången 1991. Python används idag för webbutveckling, data science,
        maskininlärning, automation och mycket mer.

        Pythons filosofi betonar kodens läsbarhet och använder signifikant
        indragning för att definiera kodblock. Detta gör koden lättare att
        läsa och underhålla jämfört med många andra programmeringsspråk.

        Python har ett stort och aktivt community med tusentals open-source
        bibliotek och ramverk tillgängliga via Python Package Index (PyPI).
        """,
        metadata={"category": "programming", "language": "Swedish"},
        source="python_intro.txt"
    ),
    Document(
        id="doc2",
        title="Maskininlärning Grundläggande",
        content="""
        Maskininlärning (ML) är en gren av artificiell intelligens som fokuserar
        på att bygga system som kan lära sig från data. Istället för att explicit
        programmeras med regler, lär sig ML-modeller mönster från exempel.

        Det finns tre huvudtyper av maskininlärning:
        1. Supervised Learning - Modellen tränas på märkta data
        2. Unsupervised Learning - Modellen hittar mönster i omärkta data
        3. Reinforcement Learning - Modellen lär sig genom trial and error

        Python är det mest populära språket för maskininlärning tack vare
        bibliotek som scikit-learn, TensorFlow och PyTorch.
        """,
        metadata={"category": "AI", "language": "Swedish"},
        source="ml_basics.txt"
    ),
    Document(
        id="doc3",
        title="Azure AI Services",
        content="""
        Azure AI Services är Microsofts samling av AI-tjänster som gör det enkelt
        att bygga intelligenta applikationer. Tjänsterna inkluderar:

        - Azure OpenAI Service: Tillgång till GPT-4 och andra OpenAI-modeller
        - Computer Vision: Bildanalys och objektdetektering
        - Speech Services: Tal-till-text och text-till-tal
        - Language Services: Textanalys, översättning och sentimentanalys

        Azure AI Agent Service är det nya ramverket som förenar funktionalitet
        från Semantic Kernel och AutoGen. Det gör det enkelt att bygga
        intelligenta agenter med minne, RAG och komplex orkestrering.
        """,
        metadata={"category": "cloud", "language": "Swedish"},
        source="azure_ai.txt"
    ),
]


async def main():
    """Huvudfunktion som demonstrerar RAG."""
    print_section("📚 Exempel 3: RAG - Retrieval Augmented Generation")

    print("""
Detta exempel visar hur en RAG-agent:
1. Indexerar dokument i en vektor-databas
2. Hämtar relevant information baserat på frågor
3. Genererar svar som kombinerar hämtad kontext med LLM-kunskap
4. Citerar källor för transparens
    """)

    # Skapa RAG-agent
    agent = RAGAgent()

    # Indexera dokument
    print_section("📥 Indexerar Dokument")
    stats = agent.index_documents(SAMPLE_DOCUMENTS)
    print(f"✅ Indexerade {stats['documents_indexed']} dokument")
    print(f"✅ Skapade {stats['total_chunks']} chunks")

    # Document store statistik
    store_stats = agent.document_store.get_stats()
    print(f"📊 Genomsnitt chunks per dokument: {store_stats['avg_chunks_per_doc']:.1f}")

    # Ställ frågor
    print_section("❓ Frågor och Svar")

    questions = [
        "Vem skapade Python?",
        "Vilka typer av maskininlärning finns det?",
        "Vad är Azure AI Agent Service?",
        "Hur används Python inom AI?",
    ]

    for question in questions:
        print(f"\n🔍 Fråga: {question}")
        print("-" * 80)

        result = await agent.query(question, top_k=2)

        print(f"💡 Svar: {result['answer']}\n")

        if result['sources']:
            print("📖 Källor:")
            for i, source in enumerate(result['sources'], 1):
                print(f"   {i}. {source['title']} (similarity: {source['similarity']:.2f})")
                print(f"      Källa: {source['source']}")

        print()
        await asyncio.sleep(0.5)

    # Visa exempel på kontext som hämtades
    print_section("🔎 Exempel på Hämtad Kontext")
    result = await agent.query("Berätta om Python", top_k=1)
    print("För frågan 'Berätta om Python' hämtades följande kontext:\n")
    print(result['context'][:500] + "...")

    print_section("✅ Exempel Avslutat")
    print("""
Lärdomar:
- RAG kombinerar retrieval med generering för faktabaserade svar
- Dokument delas upp i chunks för bättre precision
- Semantisk sökning hittar relevant kontext automatiskt
- Källor citeras för transparens och verifierbarhet
- Minskar hallucinations jämfört med ren LLM-generation

I Produktion:
- Använd Azure OpenAI för riktiga embeddings (text-embedding-ada-002)
- Använd Qdrant, ChromaDB eller Azure AI Search som vektor-databas
- Implementera re-ranking för bättre resultat
- Lägg till hybrid search (keyword + semantic)
- Implementera citation tracking
- Cacha embeddings för bättre performance

Nästa steg:
- Testa med dina egna dokument
- Experimentera med olika chunk-storlekar
- Implementera multi-turn conversations med RAG
- Lägg till filter på metadata (datum, kategori, etc.)
    """)


if __name__ == "__main__":
    asyncio.run(main())
