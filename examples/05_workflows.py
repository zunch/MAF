"""
Exempel 5: Workflows

Detta exempel visar hur man skapar och orkestrerar komplexa workflows som kan:
- Köra multi-step processer
- Hantera villkorlig logik och förgreningar
- Orkestrera flera agenter
- Implementera error handling och compensating transactions
- Köra parallella tasks
- Hantera state mellan steg
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

# Lägg till parent directory till path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import config
from shared.utils import setup_logging, print_section


class TaskStatus(Enum):
    """Status för workflow tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowContext:
    """Kontext som delas mellan workflow steps."""
    workflow_id: str
    user_id: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class TaskResult:
    """Resultat från en workflow task."""
    task_id: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class WorkflowTask(ABC):
    """Bas-klass för workflow tasks."""

    def __init__(self, task_id: str, name: str):
        """
        Initiera task.

        Args:
            task_id: Unikt ID för tasken
            name: Beskrivande namn
        """
        self.task_id = task_id
        self.name = name
        self.logger = setup_logging()

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> TaskResult:
        """
        Kör tasken.

        Args:
            context: Workflow context

        Returns:
            Resultat från tasken
        """
        pass

    async def compensate(self, context: WorkflowContext) -> None:
        """
        Kompensera/ångra tasken vid fel (optional).

        Args:
            context: Workflow context
        """
        self.logger.info(f"Compensating task: {self.task_id}")


class SimpleTask(WorkflowTask):
    """En enkel task med en funktion."""

    def __init__(self, task_id: str, name: str, func: Callable):
        """
        Initiera simple task.

        Args:
            task_id: Task ID
            name: Task name
            func: Funktion att köra
        """
        super().__init__(task_id, name)
        self.func = func

    async def execute(self, context: WorkflowContext) -> TaskResult:
        """Kör funktionen."""
        import time
        start = time.time()

        try:
            self.logger.info(f"Executing task: {self.name}")
            result = await self.func(context)
            duration = (time.time() - start) * 1000

            return TaskResult(
                task_id=self.task_id,
                status=TaskStatus.COMPLETED,
                output=result,
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            self.logger.error(f"Task failed: {self.name}", error=str(e))
            return TaskResult(
                task_id=self.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                duration_ms=duration
            )


class AgentTask(WorkflowTask):
    """Task som kör en agent."""

    def __init__(self, task_id: str, agent_name: str, prompt_template: str):
        """
        Initiera agent task.

        Args:
            task_id: Task ID
            agent_name: Namn på agenten
            prompt_template: Template för prompt
        """
        super().__init__(task_id, f"Agent: {agent_name}")
        self.agent_name = agent_name
        self.prompt_template = prompt_template

    async def execute(self, context: WorkflowContext) -> TaskResult:
        """Kör agenten."""
        import time
        start = time.time()

        try:
            # Fyll i prompt template med context
            prompt = self.prompt_template.format(**context.outputs)

            self.logger.info(f"Running agent: {self.agent_name}", prompt=prompt)

            # Simulera agent execution
            await asyncio.sleep(0.2)
            response = f"[{self.agent_name} response to: {prompt[:50]}...]"

            duration = (time.time() - start) * 1000

            return TaskResult(
                task_id=self.task_id,
                status=TaskStatus.COMPLETED,
                output=response,
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TaskResult(
                task_id=self.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                duration_ms=duration
            )


class ConditionalTask(WorkflowTask):
    """Task som kör baserat på ett villkor."""

    def __init__(
        self,
        task_id: str,
        condition: Callable[[WorkflowContext], bool],
        true_task: WorkflowTask,
        false_task: Optional[WorkflowTask] = None
    ):
        """
        Initiera conditional task.

        Args:
            task_id: Task ID
            condition: Funktion som returnerar bool
            true_task: Task att köra om True
            false_task: Task att köra om False (optional)
        """
        super().__init__(task_id, "Conditional")
        self.condition = condition
        self.true_task = true_task
        self.false_task = false_task

    async def execute(self, context: WorkflowContext) -> TaskResult:
        """Kör task baserat på villkor."""
        import time
        start = time.time()

        try:
            condition_result = self.condition(context)
            self.logger.info(
                f"Condition evaluated: {condition_result}",
                task_id=self.task_id
            )

            if condition_result:
                result = await self.true_task.execute(context)
            elif self.false_task:
                result = await self.false_task.execute(context)
            else:
                result = TaskResult(
                    task_id=self.task_id,
                    status=TaskStatus.SKIPPED,
                    output="Condition false, no false_task",
                    duration_ms=(time.time() - start) * 1000
                )

            return result

        except Exception as e:
            return TaskResult(
                task_id=self.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )


class ParallelTask(WorkflowTask):
    """Task som kör flera tasks parallellt."""

    def __init__(self, task_id: str, tasks: List[WorkflowTask]):
        """
        Initiera parallel task.

        Args:
            task_id: Task ID
            tasks: Lista av tasks att köra parallellt
        """
        super().__init__(task_id, f"Parallel ({len(tasks)} tasks)")
        self.tasks = tasks

    async def execute(self, context: WorkflowContext) -> TaskResult:
        """Kör alla tasks parallellt."""
        import time
        start = time.time()

        try:
            self.logger.info(f"Running {len(self.tasks)} tasks in parallel")

            # Kör alla tasks samtidigt
            results = await asyncio.gather(
                *[task.execute(context) for task in self.tasks],
                return_exceptions=True
            )

            # Samla resultat
            all_outputs = {}
            failed_tasks = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_tasks.append(self.tasks[i].task_id)
                elif result.status == TaskStatus.FAILED:
                    failed_tasks.append(result.task_id)
                else:
                    all_outputs[self.tasks[i].task_id] = result.output

            duration = (time.time() - start) * 1000

            if failed_tasks:
                return TaskResult(
                    task_id=self.task_id,
                    status=TaskStatus.FAILED,
                    error=f"Failed tasks: {', '.join(failed_tasks)}",
                    duration_ms=duration
                )

            return TaskResult(
                task_id=self.task_id,
                status=TaskStatus.COMPLETED,
                output=all_outputs,
                duration_ms=duration
            )

        except Exception as e:
            return TaskResult(
                task_id=self.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )


class Workflow:
    """Orkestrator för workflow execution."""

    def __init__(self, workflow_id: str, name: str):
        """
        Initiera workflow.

        Args:
            workflow_id: Unikt ID för workflow
            name: Beskrivande namn
        """
        self.workflow_id = workflow_id
        self.name = name
        self.tasks: List[WorkflowTask] = []
        self.logger = setup_logging()
        self.results: List[TaskResult] = []

    def add_task(self, task: WorkflowTask) -> "Workflow":
        """
        Lägg till en task i workflow.

        Args:
            task: Task att lägga till

        Returns:
            Self för method chaining
        """
        self.tasks.append(task)
        return self

    async def execute(self, inputs: Dict[str, Any], user_id: str = "default") -> WorkflowContext:
        """
        Kör workflow.

        Args:
            inputs: Input-data för workflow
            user_id: Användar-ID

        Returns:
            Slutgiltigt workflow context
        """
        self.logger.info(f"Starting workflow: {self.name}", workflow_id=self.workflow_id)

        # Skapa context
        context = WorkflowContext(
            workflow_id=self.workflow_id,
            user_id=user_id,
            inputs=inputs
        )

        # Kör alla tasks i ordning
        for i, task in enumerate(self.tasks, 1):
            self.logger.info(
                f"Step {i}/{len(self.tasks)}: {task.name}",
                task_id=task.task_id
            )

            result = await task.execute(context)
            self.results.append(result)

            # Spara output i context
            if result.status == TaskStatus.COMPLETED and result.output is not None:
                context.outputs[task.task_id] = result.output

            # Hantera fel
            if result.status == TaskStatus.FAILED:
                error_msg = f"Task {task.task_id} failed: {result.error}"
                context.errors.append(error_msg)
                self.logger.error("workflow_task_failed", task_id=task.task_id, error=result.error)

                # Här skulle man kunna implementera compensating transactions
                # await self._compensate(context, i-1)
                break

        self.logger.info(
            "Workflow completed",
            workflow_id=self.workflow_id,
            total_tasks=len(self.tasks),
            completed=sum(1 for r in self.results if r.status == TaskStatus.COMPLETED),
            failed=sum(1 for r in self.results if r.status == TaskStatus.FAILED)
        )

        return context

    def get_summary(self) -> Dict[str, Any]:
        """Få sammanfattning av workflow execution."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "total_tasks": len(self.tasks),
            "completed": sum(1 for r in self.results if r.status == TaskStatus.COMPLETED),
            "failed": sum(1 for r in self.results if r.status == TaskStatus.FAILED),
            "skipped": sum(1 for r in self.results if r.status == TaskStatus.SKIPPED),
            "total_duration_ms": sum(r.duration_ms for r in self.results),
            "results": self.results
        }


# Demo functions
async def demo_simple_workflow():
    """Demonstrera ett enkelt sekvensiellt workflow."""
    print_section("📝 Demo 1: Enkelt Sekvensiellt Workflow")

    async def step1(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.1)
        return f"Processed input: {ctx.inputs.get('query')}"

    async def step2(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.1)
        prev_result = ctx.outputs.get('step1')
        return f"Analyzed: {prev_result}"

    async def step3(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.1)
        return "Final report generated"

    # Bygg workflow
    workflow = Workflow("wf_simple", "Simple Sequential Workflow")
    workflow.add_task(SimpleTask("step1", "Data Processing", step1))
    workflow.add_task(SimpleTask("step2", "Data Analysis", step2))
    workflow.add_task(SimpleTask("step3", "Report Generation", step3))

    # Kör workflow
    result = await workflow.execute({"query": "Vad är MAF?"}, user_id="user_123")

    # Visa resultat
    print("\n✅ Workflow slutförd!")
    print(f"Outputs: {result.outputs}")

    summary = workflow.get_summary()
    print(f"\n📊 Totalt: {summary['completed']}/{summary['total_tasks']} tasks slutförda")
    print(f"⏱️  Total tid: {summary['total_duration_ms']:.2f}ms")


async def demo_conditional_workflow():
    """Demonstrera workflow med villkorlig logik."""
    print_section("🔀 Demo 2: Workflow med Villkor")

    async def check_input(ctx: WorkflowContext) -> str:
        query = ctx.inputs.get('query', '')
        return f"Input validated: '{query}'"

    async def handle_short_query(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.1)
        return "Quick response for short query"

    async def handle_long_query(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.2)
        return "Detailed response for long query"

    # Bygg workflow
    workflow = Workflow("wf_conditional", "Conditional Workflow")

    # Steg 1: Validera input
    workflow.add_task(SimpleTask("validate", "Validate Input", check_input))

    # Steg 2: Villkorlig bearbetning
    def is_short_query(ctx: WorkflowContext) -> bool:
        query = ctx.inputs.get('query', '')
        return len(query) < 20

    workflow.add_task(
        ConditionalTask(
            "conditional",
            condition=is_short_query,
            true_task=SimpleTask("short", "Handle Short Query", handle_short_query),
            false_task=SimpleTask("long", "Handle Long Query", handle_long_query)
        )
    )

    # Test med kort query
    print("\n🔵 Test 1: Kort query")
    result1 = await workflow.execute({"query": "Hej!"}, user_id="user_1")
    print(f"Result: {result1.outputs}")

    # Reset för nästa test
    workflow.results = []

    # Test med lång query
    print("\n🔵 Test 2: Lång query")
    result2 = await workflow.execute(
        {"query": "Kan du förklara Microsoft Agent Framework i detalj?"},
        user_id="user_2"
    )
    print(f"Result: {result2.outputs}")


async def demo_parallel_workflow():
    """Demonstrera parallell exekvering."""
    print_section("⚡ Demo 3: Parallellt Workflow")

    async def analyze_sentiment(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.3)
        return "sentiment: positive"

    async def extract_entities(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.2)
        return "entities: [MAF, Microsoft, AI]"

    async def classify_intent(ctx: WorkflowContext) -> str:
        await asyncio.sleep(0.25)
        return "intent: information_request"

    async def summarize_results(ctx: WorkflowContext) -> str:
        parallel_results = ctx.outputs.get('parallel_analysis', {})
        return f"Summary of {len(parallel_results)} analyses"

    # Bygg workflow
    workflow = Workflow("wf_parallel", "Parallel Analysis Workflow")

    # Steg 1: Kör flera analyser parallellt
    parallel_tasks = [
        SimpleTask("sentiment", "Sentiment Analysis", analyze_sentiment),
        SimpleTask("entities", "Entity Extraction", extract_entities),
        SimpleTask("intent", "Intent Classification", classify_intent),
    ]
    workflow.add_task(ParallelTask("parallel_analysis", parallel_tasks))

    # Steg 2: Sammanfatta resultat
    workflow.add_task(SimpleTask("summary", "Summarize Results", summarize_results))

    # Kör workflow
    result = await workflow.execute(
        {"text": "Microsoft Agent Framework är fantastiskt!"},
        user_id="user_parallel"
    )

    print("\n✅ Parallell analys slutförd!")
    print(f"Results: {result.outputs}")

    summary = workflow.get_summary()
    print(f"\n⏱️  Total tid: {summary['total_duration_ms']:.2f}ms")
    print("   (Notera: Parallell execution är snabbare än sekventiell!)")


async def demo_multi_agent_workflow():
    """Demonstrera multi-agent orkestrering."""
    print_section("🤝 Demo 4: Multi-Agent Workflow")

    # Bygg workflow med flera agenter
    workflow = Workflow("wf_multi_agent", "Multi-Agent Research Workflow")

    # Agent 1: Research agent
    workflow.add_task(
        AgentTask(
            "research",
            "ResearchAgent",
            "Research topic: {topic}"
        )
    )

    # Agent 2: Analysis agent
    workflow.add_task(
        AgentTask(
            "analyze",
            "AnalysisAgent",
            "Analyze findings: {research}"
        )
    )

    # Agent 3: Writing agent
    workflow.add_task(
        AgentTask(
            "write",
            "WritingAgent",
            "Write report based on: {analyze}"
        )
    )

    # Agent 4: Review agent
    workflow.add_task(
        AgentTask(
            "review",
            "ReviewAgent",
            "Review and improve: {write}"
        )
    )

    # Kör workflow
    result = await workflow.execute(
        {"topic": "Microsoft Agent Framework features"},
        user_id="user_research"
    )

    print("\n✅ Multi-agent workflow slutförd!")
    print("\nAgent outputs:")
    for task_id, output in result.outputs.items():
        print(f"  {task_id}: {output}")

    summary = workflow.get_summary()
    print(f"\n📊 {summary['completed']}/{summary['total_tasks']} agents slutförde sitt arbete")


async def main():
    """Huvudfunktion som demonstrerar workflows."""
    print_section("🔄 Exempel 5: Workflows")

    print("""
Detta exempel visar hur workflows används för att:
- Orkestrera multi-step processer
- Hantera villkorlig logik
- Köra tasks parallellt för bättre performance
- Orkestrera flera agenter tillsammans
- Hantera state mellan steg
    """)

    # Kör alla demos
    await demo_simple_workflow()
    await asyncio.sleep(1)

    await demo_conditional_workflow()
    await asyncio.sleep(1)

    await demo_parallel_workflow()
    await asyncio.sleep(1)

    await demo_multi_agent_workflow()

    print_section("✅ Exempel Avslutat")
    print("""
Lärdomar:
- Workflows orkesterar komplexa multi-step processer
- Sekventiella, parallella och villkorliga flows stöds
- State delas via WorkflowContext mellan steg
- Perfekt för multi-agent samarbete

Workflow Patterns:
1. Sequential - Steg kör ett efter ett
2. Parallel - Flera steg kör samtidigt
3. Conditional - Steg kör baserat på villkor
4. Loop - Upprepa steg (ej implementerat här)
5. Fork/Join - Dela upp och sammanfoga parallella grenar
6. Saga - Kompensering vid fel (för distributed transactions)

I Microsoft Agent Framework:
- Använd built-in workflow orchestration
- Definiera workflows deklarativt eller programmatiskt
- Implementera error handling och retry policies
- Använd checkpointing för long-running workflows
- Monitor workflow execution med telemetry

Avancerade Features:
- Human-in-the-loop (vänta på användar-input)
- Event-driven workflows (triggas av events)
- Long-running workflows med persistence
- Distributed workflows över flera services
- Workflow versioning och migration

Nästa steg:
- Implementera fel-hantering med compensating transactions
- Lägg till workflow persistence (spara state)
- Implementera human-in-the-loop steps
- Skapa återanvändbara workflow templates
- Lägg till workflow monitoring och visualisering
    """)


if __name__ == "__main__":
    asyncio.run(main())
