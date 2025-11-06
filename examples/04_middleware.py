"""
Exempel 4: Middleware

Detta exempel visar hur man skapar och använder middleware för att:
- Logga alla agent-interaktioner
- Mäta performance och latency
- Implementera rate limiting
- Lägga till säkerhetsvalidering
- Transformera input/output
- Hantera fel och retry-logik
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import json

# Lägg till parent directory till path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import config
from shared.utils import setup_logging, print_section


@dataclass
class AgentContext:
    """Kontext som passeras genom middleware-pipelinen."""
    request_id: str
    user_id: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    response: Optional[str] = None


class Middleware(ABC):
    """Bas-klass för middleware."""

    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logging()

    @abstractmethod
    async def process(self, context: AgentContext, next_middleware: Callable) -> AgentContext:
        """
        Bearbeta contextet och anropa nästa middleware.

        Args:
            context: Aktuellt context
            next_middleware: Nästa middleware i kedjan

        Returns:
            Uppdaterat context
        """
        pass


class LoggingMiddleware(Middleware):
    """Middleware för att logga alla requests och responses."""

    def __init__(self):
        super().__init__("LoggingMiddleware")

    async def process(self, context: AgentContext, next_middleware: Callable) -> AgentContext:
        """Logga request och response."""
        # Logga inkommande request
        self.logger.info(
            "agent_request",
            request_id=context.request_id,
            user_id=context.user_id,
            message_length=len(context.message),
            timestamp=context.timestamp.isoformat()
        )

        # Anropa nästa middleware
        context = await next_middleware(context)

        # Logga response
        self.logger.info(
            "agent_response",
            request_id=context.request_id,
            response_length=len(context.response) if context.response else 0,
            processing_time_ms=context.metadata.get("processing_time_ms", 0)
        )

        return context


class PerformanceMiddleware(Middleware):
    """Middleware för att mäta performance."""

    def __init__(self):
        super().__init__("PerformanceMiddleware")
        self.metrics: List[Dict[str, Any]] = []

    async def process(self, context: AgentContext, next_middleware: Callable) -> AgentContext:
        """Mät exekveringstid."""
        start_time = time.time()

        # Anropa nästa middleware
        context = await next_middleware(context)

        # Beräkna elapsed time
        elapsed_ms = (time.time() - start_time) * 1000

        # Lägg till i context metadata
        context.metadata["processing_time_ms"] = elapsed_ms

        # Spara metrik
        self.metrics.append({
            "request_id": context.request_id,
            "elapsed_ms": elapsed_ms,
            "timestamp": context.timestamp.isoformat()
        })

        self.logger.info(
            "performance_metric",
            request_id=context.request_id,
            elapsed_ms=round(elapsed_ms, 2)
        )

        return context

    def get_stats(self) -> Dict[str, float]:
        """Få performance-statistik."""
        if not self.metrics:
            return {"count": 0}

        times = [m["elapsed_ms"] for m in self.metrics]
        return {
            "count": len(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "total_ms": sum(times)
        }


class RateLimitMiddleware(Middleware):
    """Middleware för rate limiting."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initiera rate limiter.

        Args:
            max_requests: Max antal requests per window
            window_seconds: Tidsfönster i sekunder
        """
        super().__init__("RateLimitMiddleware")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[str, List[datetime]] = {}

    async def process(self, context: AgentContext, next_middleware: Callable) -> AgentContext:
        """Kontrollera rate limit."""
        user_id = context.user_id
        now = datetime.utcnow()

        # Initiera om inte finns
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        # Ta bort gamla requests utanför window
        cutoff_time = now - timedelta(seconds=self.window_seconds)
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > cutoff_time
        ]

        # Kontrollera limit
        current_count = len(self.user_requests[user_id])
        if current_count >= self.max_requests:
            self.logger.warning(
                "rate_limit_exceeded",
                user_id=user_id,
                current_count=current_count,
                max_requests=self.max_requests
            )
            context.response = (
                f"Rate limit överskriden. Max {self.max_requests} requests "
                f"per {self.window_seconds} sekunder."
            )
            context.metadata["rate_limited"] = True
            return context

        # Lägg till denna request
        self.user_requests[user_id].append(now)

        # Fortsätt till nästa middleware
        context = await next_middleware(context)

        self.logger.info(
            "rate_limit_check",
            user_id=user_id,
            current_count=current_count + 1,
            max_requests=self.max_requests
        )

        return context


class ContentFilterMiddleware(Middleware):
    """Middleware för innehållsfiltrering och säkerhet."""

    def __init__(self):
        super().__init__("ContentFilterMiddleware")
        # Lista över blockerade ord (exempel)
        self.blocked_keywords = ["spam", "hack", "malware"]

    async def process(self, context: AgentContext, next_middleware: Callable) -> AgentContext:
        """Filtrera innehåll."""
        message_lower = context.message.lower()

        # Kontrollera blockerade ord
        for keyword in self.blocked_keywords:
            if keyword in message_lower:
                self.logger.warning(
                    "content_filtered",
                    request_id=context.request_id,
                    keyword=keyword
                )
                context.response = "Din förfrågan innehöll otillåtet innehåll och har blockerats."
                context.metadata["filtered"] = True
                return context

        # Validera längd
        if len(context.message) > 5000:
            self.logger.warning(
                "message_too_long",
                request_id=context.request_id,
                length=len(context.message)
            )
            context.response = "Din förfrågan är för lång. Max 5000 tecken."
            context.metadata["filtered"] = True
            return context

        # Allt OK, fortsätt
        context = await next_middleware(context)
        return context


class RetryMiddleware(Middleware):
    """Middleware för att hantera fel med retry-logik."""

    def __init__(self, max_retries: int = 3, backoff_seconds: float = 1.0):
        """
        Initiera retry middleware.

        Args:
            max_retries: Max antal retry-försök
            backoff_seconds: Initial backoff-tid
        """
        super().__init__("RetryMiddleware")
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    async def process(self, context: AgentContext, next_middleware: Callable) -> AgentContext:
        """Försök anropa med retry-logik."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # Försök anropa nästa middleware
                context = await next_middleware(context)

                if attempt > 0:
                    self.logger.info(
                        "retry_succeeded",
                        request_id=context.request_id,
                        attempt=attempt
                    )

                return context

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    backoff = self.backoff_seconds * (2 ** attempt)
                    self.logger.warning(
                        "retry_attempt",
                        request_id=context.request_id,
                        attempt=attempt + 1,
                        backoff_seconds=backoff,
                        error=str(e)
                    )
                    await asyncio.sleep(backoff)
                else:
                    self.logger.error(
                        "retry_failed",
                        request_id=context.request_id,
                        max_retries=self.max_retries,
                        error=str(e)
                    )

        # Alla retries misslyckades
        context.response = f"Ett fel uppstod efter {self.max_retries} försök: {last_error}"
        context.metadata["error"] = str(last_error)
        return context


class MiddlewarePipeline:
    """Pipeline som kör flera middleware i ordning."""

    def __init__(self, middlewares: List[Middleware]):
        """
        Initiera pipeline.

        Args:
            middlewares: Lista med middleware att köra
        """
        self.middlewares = middlewares
        self.logger = setup_logging()

    async def execute(self, context: AgentContext, handler: Callable) -> AgentContext:
        """
        Kör alla middleware och slutligen handleren.

        Args:
            context: Initialt context
            handler: Slutlig handler som genererar response

        Returns:
            Slutgiltigt context
        """

        async def build_chain(index: int) -> Callable:
            """Bygg middleware-kedjan rekursivt."""
            if index >= len(self.middlewares):
                # Sista steget - anropa handleren
                return handler

            middleware = self.middlewares[index]
            next_chain = await build_chain(index + 1)

            async def chain(ctx: AgentContext) -> AgentContext:
                return await middleware.process(ctx, next_chain)

            return chain

        # Bygg och kör kedjan
        chain = await build_chain(0)
        return await chain(context)


# Mock agent handler
async def simple_agent_handler(context: AgentContext) -> AgentContext:
    """Enkel agent-handler för demonstration."""
    # Simulera processing time
    await asyncio.sleep(0.1)

    # Generera svar
    context.response = f"Echo: {context.message} (processed at {datetime.utcnow().isoformat()})"
    return context


async def demo_basic_middleware():
    """Demonstrera grundläggande middleware."""
    print_section("🔧 Demo 1: Grundläggande Middleware")

    # Skapa pipeline med logging och performance
    pipeline = MiddlewarePipeline([
        LoggingMiddleware(),
        PerformanceMiddleware(),
    ])

    # Skicka några requests
    for i in range(3):
        context = AgentContext(
            request_id=f"req_{i}",
            user_id="user_123",
            message=f"Test meddelande {i}"
        )

        result = await pipeline.execute(context, simple_agent_handler)
        print(f"✅ Request {i}: {result.response}")
        print(f"   ⏱️  Processing time: {result.metadata.get('processing_time_ms', 0):.2f}ms\n")


async def demo_rate_limiting():
    """Demonstrera rate limiting."""
    print_section("🚦 Demo 2: Rate Limiting")

    # Skapa pipeline med rate limiting (max 3 requests per 10 sekunder)
    rate_limiter = RateLimitMiddleware(max_requests=3, window_seconds=10)
    pipeline = MiddlewarePipeline([
        rate_limiter,
        LoggingMiddleware(),
    ])

    # Försök skicka 5 requests snabbt
    print("Skickar 5 requests snabbt (limit: 3 per 10 sek)...\n")
    for i in range(5):
        context = AgentContext(
            request_id=f"req_{i}",
            user_id="user_456",
            message=f"Snabb request {i}"
        )

        result = await pipeline.execute(context, simple_agent_handler)

        if result.metadata.get("rate_limited"):
            print(f"❌ Request {i}: RATE LIMITED")
        else:
            print(f"✅ Request {i}: Success")

        await asyncio.sleep(0.1)


async def demo_content_filter():
    """Demonstrera innehållsfiltrering."""
    print_section("🛡️ Demo 3: Content Filtering")

    # Skapa pipeline med content filter
    pipeline = MiddlewarePipeline([
        ContentFilterMiddleware(),
        LoggingMiddleware(),
    ])

    test_messages = [
        "Normal meddelande",
        "Ett meddelande med spam i sig",
        "Försök att hack systemet",
        "A" * 6000,  # För långt
    ]

    for msg in test_messages:
        context = AgentContext(
            request_id=f"req_{hash(msg)}",
            user_id="user_789",
            message=msg
        )

        result = await pipeline.execute(context, simple_agent_handler)

        if result.metadata.get("filtered"):
            print(f"🚫 BLOCKED: '{msg[:50]}...'")
            print(f"   Reason: {result.response}\n")
        else:
            print(f"✅ ALLOWED: '{msg[:50]}...'\n")


async def demo_complete_pipeline():
    """Demonstrera komplett pipeline med alla middleware."""
    print_section("🔄 Demo 4: Komplett Middleware Pipeline")

    # Skapa komplett pipeline
    perf_middleware = PerformanceMiddleware()
    pipeline = MiddlewarePipeline([
        RetryMiddleware(max_retries=2),
        ContentFilterMiddleware(),
        RateLimitMiddleware(max_requests=10, window_seconds=60),
        perf_middleware,
        LoggingMiddleware(),
    ])

    # Skicka några requests
    messages = [
        "Vad är Microsoft Agent Framework?",
        "Hur använder jag RAG?",
        "Berätta om långtidsminne",
    ]

    for i, msg in enumerate(messages):
        context = AgentContext(
            request_id=f"req_{i}",
            user_id="user_complete",
            message=msg
        )

        result = await pipeline.execute(context, simple_agent_handler)
        print(f"✅ {msg}")
        print(f"   Response: {result.response}")
        print(f"   Time: {result.metadata.get('processing_time_ms', 0):.2f}ms\n")

    # Visa performance stats
    print_section("📊 Performance Statistik")
    stats = perf_middleware.get_stats()
    print(f"Total requests: {stats['count']}")
    print(f"Average time: {stats['avg_ms']:.2f}ms")
    print(f"Min time: {stats['min_ms']:.2f}ms")
    print(f"Max time: {stats['max_ms']:.2f}ms")


async def main():
    """Huvudfunktion som demonstrerar middleware."""
    print_section("⚙️ Exempel 4: Middleware")

    print("""
Detta exempel visar hur middleware används för att:
- Logga alla interaktioner
- Mäta performance
- Implementera rate limiting
- Filtrera innehåll
- Hantera fel med retry-logik
    """)

    # Kör demos
    await demo_basic_middleware()
    await asyncio.sleep(1)

    await demo_rate_limiting()
    await asyncio.sleep(1)

    await demo_content_filter()
    await asyncio.sleep(1)

    await demo_complete_pipeline()

    print_section("✅ Exempel Avslutat")
    print("""
Lärdomar:
- Middleware separerar concerns (logging, säkerhet, etc.)
- Pipeline-pattern gör det enkelt att komponera middleware
- Middleware kan köras före OCH efter agent-anropet
- Perfekt för cross-cutting concerns

Vanliga Middleware Use Cases:
- Authentication & Authorization
- Logging & Monitoring
- Rate Limiting & Throttling
- Content Filtering & Safety
- Caching
- Error Handling & Retry Logic
- Request/Response Transformation
- Metrics & Analytics
- A/B Testing
- Feature Flags

I Microsoft Agent Framework:
- Använd built-in middleware när tillgängligt
- Skapa custom middleware för specifika behov
- Kedja middleware i rätt ordning (t.ex. auth före rate limiting)
- Håll middleware focused och single-purpose

Nästa steg:
- Implementera custom middleware för dina behov
- Lägg till metrics export (Prometheus, Application Insights)
- Implementera distributed tracing
- Skapa middleware för cost tracking
    """)


if __name__ == "__main__":
    asyncio.run(main())
