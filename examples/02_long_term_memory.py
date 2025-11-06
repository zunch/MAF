"""
Exempel 2: Långtidsminne (Long-term Memory)

Detta exempel visar hur man implementerar persistent långtidsminne som kan:
- Lagra konversationer över flera sessioner
- Söka semantiskt i historisk data
- Hämta relevant kontext från tidigare interaktioner
- Använda vektor-databaser för effektiv retrieval
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Lägg till parent directory till path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import config
from shared.utils import setup_logging, print_section, calculate_similarity


class VectorStore:
    """Enkel vektor-store för demonstration (i produktion: använd Qdrant/ChromaDB)."""

    def __init__(self):
        self.vectors: List[Dict[str, Any]] = []
        self.logger = setup_logging()

    def _create_simple_embedding(self, text: str) -> List[float]:
        """
        Skapa en enkel embedding (i produktion: använd Azure OpenAI embeddings).

        Detta är en MYCKET förenklad version för demonstration.
        """
        # Simple character-based "embedding" för demo
        embedding = [0.0] * 10
        for i, char in enumerate(text.lower()[:10]):
            embedding[i] = ord(char) / 255.0
        return embedding

    def add(self, text: str, metadata: Dict[str, Any]) -> str:
        """Lägg till text i vektordatabasen."""
        vector_id = f"vec_{len(self.vectors)}"
        embedding = self._create_simple_embedding(text)

        self.vectors.append({
            "id": vector_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        })

        self.logger.info("vector_added", id=vector_id, text_length=len(text))
        return vector_id

    def search(self, query: str, top_k: int = 3, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Sök efter liknande vektorer."""
        query_embedding = self._create_simple_embedding(query)

        results = []
        for vec in self.vectors:
            similarity = calculate_similarity(query_embedding, vec["embedding"])
            if similarity >= threshold:
                results.append({
                    **vec,
                    "similarity": similarity
                })

        # Sortera efter similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:top_k]

    def get_all(self) -> List[Dict[str, Any]]:
        """Hämta alla vektorer."""
        return self.vectors

    def clear(self) -> None:
        """Rensa databasen."""
        self.vectors.clear()
        self.logger.info("vector_store_cleared")


class LongTermMemory:
    """Långtidsminne med persistent lagring och semantisk sökning."""

    def __init__(self, user_id: str, similarity_threshold: float = 0.3):
        """
        Initiera långtidsminne.

        Args:
            user_id: Unik identifierare för användaren
            similarity_threshold: Minsta similarity för relevanta minnen
        """
        self.user_id = user_id
        self.similarity_threshold = similarity_threshold
        self.vector_store = VectorStore()
        self.logger = setup_logging()

        # I produktion skulle vi använda:
        # from qdrant_client import QdrantClient
        # self.client = QdrantClient(url=config.vector_db.qdrant_url)

    def remember(self, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Spara ett minne.

        Args:
            content: Innehållet att komma ihåg
            metadata: Extra metadata om minnet
        """
        meta = metadata or {}
        meta.update({
            "user_id": self.user_id,
            "created_at": datetime.utcnow().isoformat()
        })

        self.vector_store.add(content, meta)
        self.logger.info("memory_saved", user_id=self.user_id, content_length=len(content))

    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hämta relevanta minnen baserat på en query.

        Args:
            query: Sökfrågan
            top_k: Antal minnen att returnera

        Returns:
            Lista med relevanta minnen
        """
        results = self.vector_store.search(
            query,
            top_k=top_k,
            threshold=self.similarity_threshold
        )

        self.logger.info(
            "memory_recalled",
            query=query,
            results_found=len(results)
        )

        return results

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Hämta all konversationshistorik."""
        return self.vector_store.get_all()

    def get_stats(self) -> Dict[str, Any]:
        """Få statistik om långtidsminnet."""
        memories = self.vector_store.get_all()
        return {
            "total_memories": len(memories),
            "user_id": self.user_id,
            "oldest_memory": memories[0]["timestamp"] if memories else None,
            "newest_memory": memories[-1]["timestamp"] if memories else None,
        }


class AgentWithLongTermMemory:
    """Agent med både kort- och långtidsminne."""

    def __init__(self, user_id: str):
        """
        Initiera agent.

        Args:
            user_id: Unik identifierare för användaren
        """
        self.user_id = user_id
        self.long_term_memory = LongTermMemory(user_id)
        self.session_messages: List[Dict[str, str]] = []
        self.logger = setup_logging()

    async def chat(self, message: str) -> Dict[str, Any]:
        """
        Chatta med agenten.

        Args:
            message: Användarens meddelande

        Returns:
            Dict med response och metadata
        """
        # 1. Spara användarens meddelande i långtidsminne
        self.long_term_memory.remember(
            content=message,
            metadata={"role": "user", "session_id": "current"}
        )

        # 2. Hämta relevanta minnen från tidigare
        relevant_memories = self.long_term_memory.recall(message, top_k=3)

        # 3. Bygg kontext
        context_parts = []
        if relevant_memories:
            context_parts.append("Relevanta tidigare minnen:")
            for mem in relevant_memories:
                context_parts.append(
                    f"  - [{mem['timestamp']}] {mem['text'][:100]} "
                    f"(similarity: {mem['similarity']:.2f})"
                )

        # 4. Generera svar (simulerat)
        response_text = self._generate_response(message, relevant_memories)

        # 5. Spara agentens svar i långtidsminne
        self.long_term_memory.remember(
            content=response_text,
            metadata={"role": "assistant", "session_id": "current"}
        )

        return {
            "response": response_text,
            "relevant_memories": len(relevant_memories),
            "context": "\n".join(context_parts) if context_parts else "Inga tidigare minnen hittade",
        }

    def _generate_response(self, message: str, memories: List[Dict]) -> str:
        """Generera svar baserat på meddelande och minnen."""
        # Simulerad respons för demonstration
        if memories:
            memory_context = f"Jag kommer ihåg att vi pratade om detta för {len(memories)} gång(er) sedan."
            return f"Baserat på våra tidigare konversationer: {memory_context} Du sa: '{message}'"
        else:
            return f"Detta är första gången vi pratar om detta. Du sa: '{message}'"


async def demo_session_1(agent: AgentWithLongTermMemory):
    """Första sessionen - bygger upp minnen."""
    print_section("📅 Session 1: Bygga upp långtidsminne")

    messages = [
        "Hej! Jag heter Emma och jag älskar att spela gitarr.",
        "Min favoritmusik är jazz och blues.",
        "Jag har spelat gitarr i 5 år nu.",
    ]

    for msg in messages:
        print(f"\n👤 Emma: {msg}")
        result = await agent.chat(msg)
        print(f"🤖 Agent: {result['response']}")
        await asyncio.sleep(0.3)

    # Visa stats
    stats = agent.long_term_memory.get_stats()
    print(f"\n📊 Minnen sparade: {stats['total_memories']}")


async def demo_session_2(agent: AgentWithLongTermMemory):
    """Andra sessionen - hämtar från långtidsminne."""
    print_section("📅 Session 2: Hämta från långtidsminne (senare samma dag)")

    messages = [
        "Vilket instrument spelar jag?",
        "Vad gillar jag för musik?",
        "Vill du veta mer om min musiksmak?",
    ]

    for msg in messages:
        print(f"\n👤 Emma: {msg}")
        result = await agent.chat(msg)
        print(f"🤖 Agent: {result['response']}")

        if result['relevant_memories'] > 0:
            print(f"\n   🔍 Hämtade {result['relevant_memories']} relevanta minnen:")
            print(f"   {result['context']}")

        await asyncio.sleep(0.3)


async def main():
    """Huvudfunktion som demonstrerar långtidsminne."""
    print_section("🧠 Exempel 2: Långtidsminne (Long-term Memory)")

    print("""
Detta exempel visar hur en agent använder långtidsminne för att:
1. Spara konversationer persistent över sessioner
2. Söka semantiskt i tidigare interaktioner
3. Hämta relevant kontext från historiken
4. Bygga upp en djup förståelse över tid
    """)

    # Skapa agent för användare "emma_123"
    agent = AgentWithLongTermMemory(user_id="emma_123")

    # Session 1: Bygg upp minnen
    await demo_session_1(agent)

    # Kort paus mellan sessioner
    print("\n⏸️  ... några timmar senare ...\n")
    await asyncio.sleep(1)

    # Session 2: Använd minnen
    await demo_session_2(agent)

    # Visa fullständig historik
    print_section("📚 Fullständig Konversationshistorik")
    history = agent.long_term_memory.get_conversation_history()
    for i, mem in enumerate(history, 1):
        role = mem['metadata'].get('role', 'unknown')
        print(f"{i}. [{mem['timestamp']}] {role.upper()}: {mem['text']}")

    # Visa statistik
    print_section("📊 Långtidsminne Statistik")
    stats = agent.long_term_memory.get_stats()
    print(f"Totalt antal minnen: {stats['total_memories']}")
    print(f"Användare: {stats['user_id']}")
    print(f"Äldsta minne: {stats['oldest_memory']}")
    print(f"Nyaste minne: {stats['newest_memory']}")

    print_section("✅ Exempel Avslutat")
    print("""
Lärdomar:
- Långtidsminne bibehålls mellan sessioner
- Semantisk sökning hittar relevanta minnen automatiskt
- Agenten kan bygga upp djup förståelse över tid
- I produktion: använd Qdrant, ChromaDB eller Azure AI Search
- I produktion: använd Azure OpenAI för riktiga embeddings

Nästa steg:
- Implementera med riktig vektor-databas
- Lägg till memory consolidation (sammanfattning av gamla minnen)
- Implementera forgetting strategies (glöm irrelevant data)
- Lägg till privacy controls (GDPR-compliance)
    """)


if __name__ == "__main__":
    asyncio.run(main())
