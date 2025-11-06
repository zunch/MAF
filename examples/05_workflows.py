"""
Exempel 5: Workflows med Microsoft Agent Framework

Detta exempel visar hur man använder MagenticBuilder för multi-agent workflows:
- Orkestrera flera specialiserade agenter
- Automatisk hand-off mellan agenter
- Streaming av workflow execution
- Event-baserad monitoring
"""

import asyncio
from typing import Annotated
from pydantic import Field


# Function tools för agenter
def search_web(query: Annotated[str, Field(description="Sökterm att söka efter")]) -> str:
    """Simulerad websök."""
    print(f"  🔍 Söker på webben: '{query}'")
    return f"Sökresultat för '{query}': Microsoft Agent Framework förenar Semantic Kernel och AutoGen..."


def analyze_data(data: Annotated[str, Field(description="Data att analysera")]) -> str:
    """Simulerad dataanalys."""
    print(f"  📊 Analyserar data...")
    return f"Analys av '{data[:50]}...': Ramverket har stöd för agents, workflows och memory..."


async def main():
    """Huvudfunktion som demonstrerar workflows."""
    print("\n" + "=" * 80)
    print("  🔄 Exempel 5: Workflows (Multi-Agent Orchestration)")
    print("=" * 80)

    print("""
Microsoft Agent Framework's MagenticBuilder orkesterar multi-agent workflows.
Flera specialiserade agenter samarbetar för att lösa komplexa uppgifter.

Detta exempel visar:
1. Skapa specialiserade agenter (Researcher, Analyzer, Writer)
2. Orkestrera med MagenticBuilder
3. Automatisk hand-off mellan agenter
4. Event streaming för real-time monitoring
    """)

    # Försök importera agent framework
    try:
        from agent_framework import (
            ChatAgent,
            MagenticBuilder,
            MagenticAgentDeltaEvent,
            MagenticAgentMessageEvent,
            MagenticFinalResultEvent,
            MagenticOrchestratorMessageEvent,
        )
        from agent_framework.openai import OpenAIChatClient
        has_framework = True
    except ImportError:
        print("\n⚠️  agent-framework är inte installerat.")
        print("   Installera med: pip install agent-framework --pre\n")
        await demo_simulated()
        return

    # Försök skapa workflow
    try:
        chat_client = OpenAIChatClient(model_id="gpt-4o-mini")

        # Agent 1: Researcher
        researcher = ChatAgent(
            name="Researcher",
            description="Expert på research och informationshämtning",
            instructions="Du är en researcher. Hitta och sammanfatta information utan analys eller beräkningar.",
            chat_client=chat_client,
            tools=search_web
        )

        # Agent 2: Analyzer
        analyzer = ChatAgent(
            name="Analyzer",
            description="Expert på dataanalys och utvärdering",
            instructions="Du är en analytiker. Analysera information och dra slutsatser.",
            chat_client=chat_client,
            tools=analyze_data
        )

        # Agent 3: Writer
        writer = ChatAgent(
            name="Writer",
            description="Expert på att skriva välformulerade rapporter",
            instructions="Du är en writer. Skriv tydliga, välstrukturerade rapporter baserat på research och analys.",
            chat_client=chat_client
        )

        print("\n✅ Skapade 3 specialiserade agenter")

        # Bygg workflow med MagenticBuilder
        workflow = (
            MagenticBuilder()
            .participants(
                researcher=researcher,
                analyzer=analyzer,
                writer=writer
            )
            .with_standard_manager(
                chat_client=chat_client,
                max_round_count=10,  # Max antal rundor
                max_stall_count=3,   # Max antal rundor utan progress
                max_reset_count=2    # Max antal resets
            )
            .build()
        )

        print("✅ Workflow byggt med MagenticBuilder\n")

    except Exception as e:
        print(f"\n⚠️  Kunde inte skapa workflow: {e}")
        print("   Konfigurera OPENAI_API_KEY i .env-filen\n")
        await demo_simulated()
        return

    # Demo: Kör complex task genom workflow
    print("\n" + "-" * 80)
    print("  🚀 Demo: Multi-Agent Workflow Execution")
    print("-" * 80 + "\n")

    task = """
    Skapa en rapport om Microsoft Agent Framework:
    1. Researcha vad det är och dess nyckelfunktioner
    2. Analysera fördelar och användningsområden
    3. Skriv en sammanfattande rapport (max 200 ord)
    """

    print(f"📋 Task: {task}\n")
    print("🔄 Startar workflow...\n")
    print("=" * 80)

    try:
        # Kör workflow med streaming
        async for event in workflow.run_stream(task):
            # Orchestrator meddelanden
            if isinstance(event, MagenticOrchestratorMessageEvent):
                print(f"\n🎯 [ORCHESTRATOR - {event.kind}]")
                if hasattr(event.message, 'text') and event.message.text:
                    print(f"{event.message.text}")
                print("-" * 80)

            # Agent delta events (streaming output)
            elif isinstance(event, MagenticAgentDeltaEvent):
                if event.text:
                    print(event.text, end="", flush=True)

            # Agent message events
            elif isinstance(event, MagenticAgentMessageEvent):
                print(f"\n\n✅ [{event.agent_id}] Färdig")
                print("-" * 80)

            # Final result
            elif isinstance(event, MagenticFinalResultEvent):
                print("\n\n" + "=" * 80)
                print("  🎉 FINAL RESULT")
                print("=" * 80)
                if event.message and hasattr(event.message, 'text'):
                    print(event.message.text)
                print("=" * 80)

    except Exception as e:
        print(f"\n❌ Workflow misslyckades: {e}")

    print("\n" + "=" * 80)
    print("  ✅ Exempel Avslutat")
    print("=" * 80)
    print("""
Lärdomar:
✓ MagenticBuilder orkesterar multi-agent samarbete
✓ Agenter specialiseras på olika uppgifter
✓ Automatisk hand-off mellan agenter
✓ Event streaming för real-time monitoring
✓ Built-in error handling och retry logic

Workflow Patterns:
→ Sequential: Agenter kör efter varandra
→ Parallel: Flera agenter kör samtidigt
→ Magentic: LLM-driven orchestration
→ Hand-off: Explicit överlämnande mellan agenter

Event Types:
- MagenticOrchestratorMessageEvent: Orchestrator beslut
- MagenticAgentDeltaEvent: Streaming agent output
- MagenticAgentMessageEvent: Agent färdig
- MagenticFinalResultEvent: Slutresultat

Configuration Options:
- max_round_count: Max antal kommunikationsrundor
- max_stall_count: Max rundor utan progress
- max_reset_count: Max antal workflow resets

I Produktion:
→ Använd checkpointing för long-running workflows
→ Implementera human-in-the-loop för godkännande
→ Lägg till metrics och monitoring
→ Konfigurera timeout och error handling
→ Spara workflow state för resumption

Example: Custom Orchestration
```python
from agent_framework import GroupChatBuilder

workflow = (
    GroupChatBuilder()
    .add_agent(researcher)
    .add_agent(analyzer)
    .sequential()  # Kör sekventiellt
    .build()
)
```

Example: Parallel Execution
```python
workflow = (
    MagenticBuilder()
    .participants(agent1=a1, agent2=a2, agent3=a3)
    .concurrent()  # Kör parallellt
    .build()
)
```
    """)


async def demo_simulated():
    """Simulerad demo."""
    print("""
Multi-Agent Workflow Exempel:

Task: "Analysera konkurrenssituation för produkt X"

1. 🔍 Researcher Agent:
   - Söker efter konkurrenter
   - Samlar produktinformation
   → Hand-off till Analyzer

2. 📊 Analyzer Agent:
   - Jämför features
   - Analyserar priser och marknadsposition
   → Hand-off till Writer

3. ✍️ Writer Agent:
   - Skriver strukturerad rapport
   - Inkluderar rekommendationer
   → Final Result

Orchestrator koordinerar hela flödet automatiskt!
    """)


if __name__ == "__main__":
    asyncio.run(main())
