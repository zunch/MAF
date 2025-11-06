"""
Exempel 1: Kortidsminne (Short-term Memory)

Detta exempel visar hur man skapar en agent med kortidsminne som kan:
- Komma ihåg konversationshistorik under en session
- Använda kontext från tidigare meddelanden
- Begränsa minnesstorleken för att hålla nere token-användning
"""

import asyncio
import sys
from pathlib import Path

# Lägg till parent directory till path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import config
from shared.utils import setup_logging, print_section, print_agent_response
from typing import List, Dict, Any
from datetime import datetime


class ShortTermMemory:
    """Kortidsminne som håller de senaste N meddelandena."""

    def __init__(self, max_size: int = 10):
        """
        Initiera kortidsminne.

        Args:
            max_size: Maximalt antal meddelanden att komma ihåg
        """
        self.max_size = max_size
        self.messages: List[Dict[str, Any]] = []
        self.logger = setup_logging()

    def add_message(self, role: str, content: str) -> None:
        """Lägg till ett meddelande i minnet."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.messages.append(message)

        # Håll bara de senaste max_size meddelandena
        if len(self.messages) > self.max_size:
            removed = self.messages.pop(0)
            self.logger.info(
                "memory_cleanup",
                removed_message=removed["role"],
                current_size=len(self.messages)
            )

    def get_context(self) -> List[Dict[str, str]]:
        """Hämta alla meddelanden som kontext."""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]

    def get_summary(self) -> str:
        """Få en sammanfattning av minnet."""
        return f"Minnesstorlek: {len(self.messages)}/{self.max_size} meddelanden"

    def clear(self) -> None:
        """Rensa minnet."""
        self.messages.clear()
        self.logger.info("memory_cleared")


class ConversationalAgent:
    """En enkel konversationsagent med kortidsminne."""

    def __init__(self, memory_size: int = 10):
        """
        Initiera agent.

        Args:
            memory_size: Storlek på kortidsminne
        """
        self.memory = ShortTermMemory(max_size=memory_size)
        self.logger = setup_logging()
        self.llm_config = config.get_llm_config()

        # I verklig implementation skulle vi använda MAF's AgentRuntime
        # För detta exempel använder vi en simulerad respons
        self.use_simulation = True

    def _simulate_llm_response(self, user_message: str, context: List[Dict]) -> str:
        """Simulera LLM-respons baserat på kontext."""
        # Detta är bara för demonstration när Azure/OpenAI inte är konfigurerat
        context_summary = f" (med {len(context)} meddelanden i minnet)" if context else ""

        responses = {
            "vad heter jag": "Du har inte berättat ditt namn än!",
            "jag heter": f"Trevligt att träffas! Jag kommer ihåg ditt namn{context_summary}.",
            "kommer du ihåg": f"Ja, jag har {len(context)} meddelanden i mitt kortidsminne.",
        }

        for key, response in responses.items():
            if key in user_message.lower():
                return response

        return f"Jag hörde dig säga: '{user_message}'{context_summary}"

    async def chat(self, user_message: str) -> str:
        """
        Chatta med agenten.

        Args:
            user_message: Användarens meddelande

        Returns:
            Agentens svar
        """
        # Lägg till användarens meddelande i minnet
        self.memory.add_message("user", user_message)

        # Hämta kontext från minnet
        context = self.memory.get_context()

        self.logger.info(
            "processing_message",
            message_length=len(user_message),
            context_size=len(context)
        )

        # I verklig implementation:
        # from azure.ai.agent import AgentRuntime
        # runtime = AgentRuntime(config=self.llm_config)
        # response = await runtime.run(messages=context)

        # För detta exempel använder vi simulering
        if self.use_simulation:
            response_text = self._simulate_llm_response(user_message, context)
        else:
            # Här skulle du anropa din LLM
            response_text = "LLM response here"

        # Lägg till agentens svar i minnet
        self.memory.add_message("assistant", response_text)

        return response_text


async def main():
    """Huvudfunktion som demonstrerar kortidsminne."""
    print_section("🧠 Exempel 1: Kortidsminne (Short-term Memory)")

    print("""
Detta exempel visar hur en agent använder kortidsminne för att:
1. Komma ihåg konversationshistorik
2. Svara baserat på tidigare kontext
3. Automatiskt glömma gamla meddelanden när minnesgränsen nås
    """)

    # Skapa agent med minnesstorlek på 6 meddelanden
    agent = ConversationalAgent(memory_size=6)

    # Testkonversation
    conversations = [
        "Hej! Jag heter Anna.",
        "Vad heter jag?",
        "Jag älskar att programmera i Python.",
        "Vilket programmeringsspråk nämnde jag?",
        "Vad är din favorit måltid?",
        "Vad var mitt namn igen?",  # Efter några meddelanden
        "Kommer du ihåg allt vi pratat om?",
    ]

    print_section("💬 Konversation startar")

    for i, message in enumerate(conversations, 1):
        print(f"\n👤 Användare: {message}")

        response = await agent.chat(message)
        print(f"🤖 Agent: {response}")

        print(f"   📊 {agent.memory.get_summary()}")

        # Kort paus för läsbarhet
        await asyncio.sleep(0.5)

    # Visa slutgiltigt minnesstatus
    print_section("📊 Slutgiltigt Minnesstatus")
    print(agent.memory.get_summary())
    print("\nMeddelanden i minnet:")
    for msg in agent.memory.messages:
        print(f"  [{msg['timestamp']}] {msg['role']}: {msg['content'][:50]}...")

    # Demonstration av att rensa minnet
    print_section("🧹 Rensa Minnet")
    agent.memory.clear()
    print(f"Minnet rensat: {agent.memory.get_summary()}")

    print_section("✅ Exempel Avslutat")
    print("""
Lärdomar:
- Kortidsminne behåller endast de senaste N meddelandena
- Äldre meddelanden glöms automatiskt när gränsen nås
- Detta hjälper att kontrollera token-användning och kostnader
- Perfekt för sessionsbaserade konversationer
    """)


if __name__ == "__main__":
    asyncio.run(main())
