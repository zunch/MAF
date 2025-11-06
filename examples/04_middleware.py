"""
Exempel 4: Middleware med Microsoft Agent Framework

Detta exempel visar hur man använder ContextProviders som middleware för:
- Logging av requests/responses
- Lägga till kontext innan varje anrop
- Bearbeta responses efter varje anrop
"""

import asyncio
from typing import Any
from collections.abc import MutableSequence, Sequence


async def main():
    """Huvudfunktion som demonstrerar middleware."""
    print("\n" + "=" * 80)
    print("  ⚙️ Exempel 4: Middleware (ContextProviders)")
    print("=" * 80)

    print("""
Microsoft Agent Framework använder ContextProviders som middleware.
ContextProviders kan:
- Lägga till kontext innan agent-anrop (invoking)
- Bearbeta responses efter anrop (invoked)
- Logga, validera, transformera data

Detta exempel visar en custom ContextProvider.
    """)

    # Försök importera agent framework
    try:
        from agent_framework import ChatAgent, ChatMessage, ContextProvider, Context, Role
        from agent_framework.openai import OpenAIChatClient
        has_framework = True
    except ImportError:
        print("\n⚠️  agent-framework är inte installerat.")
        print("   Installera med: pip install agent-framework --pre\n")
        await demo_simulated()
        return

    # Custom ContextProvider Implementation
    class LoggingMiddleware(ContextProvider):
        """Middleware för att logga alla agent-interaktioner."""

        def __init__(self):
            self.request_count = 0

        async def invoking(
            self,
            messages: ChatMessage | MutableSequence[ChatMessage],
            **kwargs: Any
        ) -> Context:
            """Anropas INNAN agenten kör."""
            self.request_count += 1

            # Extrahera användarens meddelande
            if isinstance(messages, list) and messages:
                user_msg = messages[-1].text if hasattr(messages[-1], 'text') else str(messages[-1])
            else:
                user_msg = messages.text if hasattr(messages, 'text') else str(messages)

            print(f"\n📥 [{self.request_count}] Inkommande request:")
            print(f"   User: {user_msg[:100]}...")

            # Lägg till extra instruktioner
            instructions = f"Request #{self.request_count}. Var koncis i ditt svar."

            return Context(instructions=instructions)

        async def invoked(
            self,
            request_messages: ChatMessage | Sequence[ChatMessage],
            response_messages: ChatMessage | Sequence[ChatMessage] | None = None,
            invoke_exception: Exception | None = None,
            **kwargs: Any,
        ) -> None:
            """Anropas EFTER agenten har kört."""
            if invoke_exception:
                print(f"   ❌ Fel uppstod: {invoke_exception}")
                return

            # Extrahera response
            if response_messages:
                if isinstance(response_messages, list) and response_messages:
                    resp_text = response_messages[0].text if hasattr(response_messages[0], 'text') else str(response_messages[0])
                else:
                    resp_text = response_messages.text if hasattr(response_messages, 'text') else str(response_messages)

                print(f"📤 [{self.request_count}] Response genererad:")
                print(f"   Agent: {resp_text[:100]}...")

    class UserPreferencesMiddleware(ContextProvider):
        """Middleware för att injicera användarpreferenser."""

        def __init__(self, user_id: str):
            self.user_id = user_id
            # Simulerade user preferences
            self.preferences = {
                "language": "Swedish",
                "style": "professional",
                "detail_level": "concise"
            }

        async def invoking(
            self,
            messages: ChatMessage | MutableSequence[ChatMessage],
            **kwargs: Any
        ) -> Context:
            """Lägg till user preferences i kontexten."""
            prefs_text = ", ".join([f"{k}={v}" for k, v in self.preferences.items()])
            instructions = f"Användarpreferenser: {prefs_text}"

            print(f"\n🎨 Injicerar user preferences för {self.user_id}")

            return Context(instructions=instructions)

        async def invoked(
            self,
            request_messages: ChatMessage | Sequence[ChatMessage],
            response_messages: ChatMessage | Sequence[ChatMessage] | None = None,
            invoke_exception: Exception | None = None,
            **kwargs: Any,
        ) -> None:
            """Inget behöver göras efter anropet."""
            pass

    # Försök skapa agent
    try:
        chat_client = OpenAIChatClient(model_id="gpt-4o-mini")

        # Skapa middlewares
        logging_mw = LoggingMiddleware()
        prefs_mw = UserPreferencesMiddleware("user_123")

        # Skapa agent med middlewares
        agent = ChatAgent(
            chat_client=chat_client,
            instructions="Du är en hjälpsam assistent.",
            context_providers=[logging_mw, prefs_mw]  # Lägg till middlewares här
        )
        print("\n✅ Agent skapad med 2 middlewares\n")

    except Exception as e:
        print(f"\n⚠️  Kunde inte skapa agent: {e}")
        print("   Konfigurera OPENAI_API_KEY i .env-filen\n")
        await demo_simulated()
        return

    # Demo: Kör requests genom middleware-pipeline
    print("\n" + "-" * 80)
    print("  🔄 Demo: Middleware Pipeline")
    print("-" * 80)

    messages = [
        "Vad är Microsoft Agent Framework?",
        "Hur fungerar middleware?",
        "Ge mig ett exempel på workflows"
    ]

    for msg in messages:
        print(f"\n{'=' * 80}")
        print(f"👤 Användare: {msg}")

        response = await agent.run(msg)

        print(f"\n🤖 Agent: {response.text}\n")
        print(f"{'=' * 80}")
        await asyncio.sleep(1)

    print(f"\n📊 Total requests bearbetade: {logging_mw.request_count}")

    print("\n" + "=" * 80)
    print("  ✅ Exempel Avslutat")
    print("=" * 80)
    print("""
Lärdomar:
✓ ContextProviders är MAF's middleware-mekanism
✓ invoking() körs INNAN agent-anrop
✓ invoked() körs EFTER agent-anrop
✓ Flera providers kan kedjas tillsammans
✓ Används för logging, validation, context injection

Vanliga Use Cases:
→ Logging och monitoring
→ User preferences injection
→ Rate limiting
→ Content filtering
→ Cost tracking
→ A/B testing
→ Feature flags
→ Security validation

Example: Rate Limiting Middleware
```python
class RateLimitMiddleware(ContextProvider):
    def __init__(self, max_per_minute=10):
        self.max_per_minute = max_per_minute
        self.requests = []

    async def invoking(self, messages, **kwargs):
        now = datetime.now()
        # Ta bort gamla requests
        self.requests = [r for r in self.requests
                        if now - r < timedelta(minutes=1)]

        if len(self.requests) >= self.max_per_minute:
            raise Exception("Rate limit exceeded")

        self.requests.append(now)
        return Context()
```

Mem0 Integration (för semantiskt minne):
```python
from agent_framework.mem0 import Mem0Provider

mem0_provider = Mem0Provider(
    user_id="user_123",
    mem0_client=mem0_client
)

agent = ChatAgent(
    chat_client=chat_client,
    context_providers=[mem0_provider]
)
```
    """)


async def demo_simulated():
    """Simulerad demo."""
    print("""
Middleware-flöde:

1. Request kommer in
2. invoking() körs på alla providers
3. Extra kontext läggs till
4. Agent kör
5. invoked() körs på alla providers
6. Logging, metrics, etc.
7. Response returneras

Exempel:
📥 LoggingMiddleware: "Request #1 från user_123"
🎨 PreferencesMiddleware: "Injicerar svenska, professional"
🤖 Agent bearbetar...
📤 LoggingMiddleware: "Response genererad, 150 tokens"
    """)


if __name__ == "__main__":
    asyncio.run(main())
