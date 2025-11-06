"""Utility functions for MAF examples."""

import json
import logging
from typing import Any, Dict, List
from datetime import datetime
import structlog


def setup_logging(log_level: str = "INFO") -> structlog.BoundLogger:
    """Setup structured logging."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    return structlog.get_logger()


def format_conversation_history(history: List[Dict[str, str]]) -> str:
    """Format conversation history for display."""
    formatted = []
    for msg in history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        formatted.append(f"[{timestamp}] {role.upper()}: {content}")
    return "\n".join(formatted)


def print_section(title: str, content: str = "") -> None:
    """Print a formatted section."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)
    if content:
        print(content)
    print()


def print_agent_response(response: Any, show_metadata: bool = True) -> None:
    """Print agent response in a formatted way."""
    print("\n" + "-" * 80)
    print("🤖 Agent Response:")
    print("-" * 80)

    if hasattr(response, 'content'):
        print(response.content)
    elif isinstance(response, dict):
        print(response.get('content', response))
    else:
        print(response)

    if show_metadata and isinstance(response, dict):
        if 'metadata' in response:
            print("\nMetadata:")
            print(json.dumps(response['metadata'], indent=2))

    print("-" * 80 + "\n")


def save_json(data: Any, filepath: str) -> None:
    """Save data as JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Chunk text into smaller pieces with overlap."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

        if start + chunk_size >= text_length and start < text_length:
            chunks.append(text[start:])
            break

    return chunks


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)
