"""
Exempel 1: Kortidsminne (Short-term Memory) med Microsoft Agent Framework

Detta exempel visar hur Threads används för att hantera kortidsminne:
- Skapa och återanvända threads för konversationskontext
- Serialisera och deserialiser threads för persistence
- Hantera flera parallella sessions med separata threads
"""

import asyncio
import json
from pathlib import Path

async def main():
    """Huvudfunktion som demonstrerar kortidsminne med threads."""
    print("\n" + "=" * 80)
    print("  🧠 Exempel 1: Kortidsminne (Short-term Memory)")
    print("=" * 80)

    print("""
Microsoft Agent Framework använder Threads för kortidsminne.
Threads lagrar konversationshistorik under application runtime.

Detta exempel visar:
1. Skapa nya threads
2. Bibehålla kontext mellan meddelanden
3. Serialisera och återställa thread-state
4. Hantera flera parallella threads
    """)

    # Försök importera agent framework
    try:
        from agent_framework import ChatAgent
        from agent_framework.openai import OpenAIChatClient
        has_framework = True
    except ImportError:
        print("\n⚠️  agent-framework är inte installerat.")
        print("   Installera med: pip install agent-framework --pre")
        print("\n   Kör simulerad demo istället...\n")
        await demo_simulated()
        return

    # Försök skapa chat client
    try:
        chat_client = OpenAIChatClient(model_id="gpt-4o-mini")

        # Skapa agent
        agent = ChatAgent(
            chat_client=chat_client,
            instructions="Du är en hjälpsam assistent som kan komma ihåg konversationer."
        )
        print("\n✅ Agent skapad med OpenAI\n")

    except Exception as e:
        print(f"\n⚠️  Kunde inte skapa agent: {e}")
        print("   Konfigurera OPENAI_API_KEY i .env-filen")
        print("\n   Kör simulerad demo istället...\n")
        await demo_simulated()
        return

    # Demo 1: Grundläggande thread-användning
    print("\n" + "-" * 80)
    print("  💬 Demo 1: Grundläggande Thread-användning")
    print("-" * 80 + "\n")

    # Skapa en ny thread
    thread = agent.get_new_thread()
    print("✅ Ny thread skapad\n")

    # Konversation med kontext
    messages = [
        "Hej! Jag heter Anna och jag älskar Python-programmering.",
        "Vad heter jag?",
        "Vilket programmeringsspråk gillar jag?"
    ]

    for msg in messages:
        print(f"👤 Användare: {msg}")
        response = await agent.run(msg, thread=thread)
        print(f"🤖 Agent: {response.text}\n")
        await asyncio.sleep(0.5)

    # Demo 2: Thread serialisering
    print("\n" + "-" * 80)
    print("  💾 Demo 2: Serialisera och Återställ Thread")
    print("-" * 80 + "\n")

    # Serialisera
    serialized = await thread.serialize()
    print("✅ Thread serialiserad\n")

    # Spara till fil
    thread_file = Path("thread_demo.json")
    with open(thread_file, 'w') as f:
        json.dump(serialized, f, indent=2)
    print(f"✅ Sparad till {thread_file}\n")

    # Återställ
    with open(thread_file, 'r') as f:
        loaded_data = json.load(f)

    restored_thread = await agent.deserialize_thread(loaded_data)
    print("✅ Thread återställd\n")

    # Fortsätt konversation med återställd thread
    print("👤 Användare: Kan du sammanfatta vad du vet om mig?")
    response = await agent.run(
        "Kan du sammanfatta vad du vet om mig?",
        thread=restored_thread
    )
    print(f"🤖 Agent: {response.text}\n")

    # Rensa upp
    thread_file.unlink()

    # Demo 3: Flera parallella threads
    print("\n" + "-" * 80)
    print("  🔄 Demo 3: Flera Parallella Threads")
    print("-" * 80 + "\n")

    thread_alice = agent.get_new_thread()
    thread_bob = agent.get_new_thread()

    print("Session Alice:")
    print("👤 Alice: Hej! Jag gillar jazz.")
    resp_a1 = await agent.run("Hej! Jag gillar jazz.", thread=thread_alice)
    print(f"🤖 Agent: {resp_a1.text}\n")

    print("Session Bob:")
    print("👤 Bob: Hej! Jag gillar rock.")
    resp_b1 = await agent.run("Hej! Jag gillar rock.", thread=thread_bob)
    print(f"🤖 Agent: {resp_b1.text}\n")

    print("Tillbaka till Alice:")
    print("👤 Alice: Vilken musik gillar jag?")
    resp_a2 = await agent.run("Vilken musik gillar jag?", thread=thread_alice)
    print(f"🤖 Agent: {resp_a2.text}\n")

    print("\n" + "=" * 80)
    print("  ✅ Exempel Avslutat")
    print("=" * 80)
    print("""
Lärdomar:
✓ Threads bibehåller konversationskontext automatiskt
✓ Varje thread är isolerad från andra
✓ Threads kan serialiseras för persistence
✓ Perfekt för sessionsbaserade applikationer

I Produktion:
→ Spara threads i Redis/SQL med user/session ID
→ Implementera TTL för gamla threads
→ Använd ChatMessageStore för mer kontroll
→ Kombinera med långtidsminne (exempel 02)
    """)


async def demo_simulated():
    """Simulerad demo utan AI-konfiguration."""
    print("\n" + "-" * 80)
    print("  🎭 Simulerad Demo")
    print("-" * 80 + "\n")

    print("Så här fungerar threads:\n")
    print("👤 Användare: Hej! Jag heter Anna.")
    print("🤖 Agent: Trevligt! Hej Anna!\n")
    print("👤 Användare: Vad heter jag?")
    print("🤖 Agent: Du heter Anna - vi pratade precis!\n")
    print("📝 Threads bibehåller kontext automatiskt mellan meddelanden.\n")


if __name__ == "__main__":
    asyncio.run(main())
