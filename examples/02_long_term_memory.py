"""
Exempel 2: Långtidsminne (Long-term Memory) med Microsoft Agent Framework

Detta exempel visar hur man implementerar persistent långtidsminne med:
- ChatMessageStoreProtocol för custom storage
- Persistent lagring mellan sessioner
- Serialisering och deserialisering av state
"""

import asyncio
from typing import Any, Sequence
from collections.abc import MutableSequence


async def main():
    """Huvudfunktion som demonstrerar långtidsminne."""
    print("\n" + "=" * 80)
    print("  🧠 Exempel 2: Långtidsminne (Long-term Memory)")
    print("=" * 80)

    print("""
Microsoft Agent Framework stödjer persistent memory genom:
1. ChatMessageStore för att lagra meddelanden
2. Serialisering av store state
3. Återställning mellan sessioner

Detta exempel visar en custom implementation.
    """)

    # Försök importera agent framework
    try:
        from agent_framework import ChatAgent, ChatMessage, ChatMessageStoreProtocol, Role
        from agent_framework.openai import OpenAIChatClient
        has_framework = True
    except ImportError:
        print("\n⚠️  agent-framework är inte installerat.")
        print("   Installera med: pip install agent-framework --pre\n")
        await demo_simulated()
        return

    # Custom Message Store Implementation
    class SimplePersistentStore(ChatMessageStoreProtocol):
        """Enkel persistent message store för demonstration."""

        def __init__(self, session_id: str):
            self.session_id = session_id
            self._messages: list[ChatMessage] = []
            print(f"✅ Store skapad för session: {session_id}")

        async def add_messages(self, messages: Sequence[ChatMessage]) -> None:
            """Lägg till meddelanden."""
            self._messages.extend(messages)
            print(f"   📝 Sparade {len(messages)} meddelanden")

        async def list_messages(self) -> list[ChatMessage]:
            """Hämta alla meddelanden."""
            return self._messages

        async def serialize(self, **kwargs: Any) -> Any:
            """Serialisera state."""
            return {
                "session_id": self.session_id,
                "message_count": len(self._messages)
            }

        async def update_from_state(self, serialized_store_state: Any, **kwargs: Any) -> None:
            """Uppdatera från serialiserad state."""
            if serialized_store_state:
                self.session_id = serialized_store_state.get("session_id", self.session_id)

    # Försök skapa agent
    try:
        chat_client = OpenAIChatClient(model_id="gpt-4o-mini")

        # Factory funktion för att skapa store
        def create_store():
            return SimplePersistentStore("user_emma_session_1")

        # Skapa agent med custom store
        agent = ChatAgent(
            chat_client=chat_client,
            instructions="Du är en hjälpsam assistent med långtidsminne.",
            chat_message_store_factory=create_store
        )
        print("\n✅ Agent skapad med persistent memory\n")

    except Exception as e:
        print(f"\n⚠️  Kunde inte skapa agent: {e}")
        print("   Konfigurera OPENAI_API_KEY i .env-filen\n")
        await demo_simulated()
        return

    # Demo: Session 1
    print("\n" + "-" * 80)
    print("  📅 Session 1: Bygga upp minnen")
    print("-" * 80 + "\n")

    thread1 = agent.get_new_thread()

    messages_session1 = [
        "Hej! Jag heter Emma och jag älskar att spela gitarr.",
        "Min favoritgenre är blues.",
        "Jag har spelat i 5 år."
    ]

    for msg in messages_session1:
        print(f"👤 Emma: {msg}")
        response = await agent.run(msg, thread=thread1)
        print(f"🤖 Agent: {response.text}\n")
        await asyncio.sleep(0.5)

    # Serialisera thread för "session end"
    print("💾 Avslutar session 1...\n")
    serialized_thread1 = await thread1.serialize()

    # Demo: Session 2 (simulera ny session)
    print("\n" + "-" * 80)
    print("  📅 Session 2: Återställ minnen")
    print("-" * 80 + "\n")

    # Skapa ny agent med samma store factory
    def create_store_session2():
        return SimplePersistentStore("user_emma_session_2")

    agent2 = ChatAgent(
        chat_client=chat_client,
        instructions="Du är en hjälpsam assistent med långtidsminne.",
        chat_message_store_factory=create_store_session2
    )

    # Återställ thread från session 1
    thread2 = await agent2.deserialize_thread(serialized_thread1)
    print("✅ Thread återställd från session 1\n")

    # Fortsätt konversation
    messages_session2 = [
        "Vilket instrument spelar jag?",
        "Hur länge har jag spelat?"
    ]

    for msg in messages_session2:
        print(f"👤 Emma: {msg}")
        response = await agent2.run(msg, thread=thread2)
        print(f"🤖 Agent: {response.text}\n")
        await asyncio.sleep(0.5)

    print("\n" + "=" * 80)
    print("  ✅ Exempel Avslutat")
    print("=" * 80)
    print("""
Lärdomar:
✓ ChatMessageStore ger persistent memory
✓ State kan serialiseras mellan sessioner
✓ Custom stores kan integrera med databaser
✓ Kombinera med threads för fullständig memory

I Produktion:
→ Implementera RedisChatMessageStore
→ Använd SQL/NoSQL för långtidslagring
→ Lägg till vector search för semantisk retrieval
→ Implementera memory consolidation
→ GDPR-compliance och data retention policies

För Redis-baserad memory:
```python
from agent_framework.redis import RedisChatMessageStore

def create_redis_store():
    return RedisChatMessageStore(
        redis_url="redis://localhost:6379",
        thread_id="user_123",
        max_messages=100
    )
```
    """)


async def demo_simulated():
    """Simulerad demo."""
    print("""
Långtidsminne gör att agenten kan:
- Komma ihåg tidigare sessioner
- Lagra information persistent
- Hämta historisk kontext

Exempel:
Session 1: "Jag heter Emma och gillar blues."
Session 2: "Vad gillar jag för musik?" → "Blues!"
    """)


if __name__ == "__main__":
    asyncio.run(main())
