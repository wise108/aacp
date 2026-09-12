"""TEST-ONLY infrastructure for Publication Layer tests.

This package is NOT a production Message Store backend.
Do not import it from production code paths.
"""

from aacp.testing.memory_store import HookDecision, InMemoryMessageStore

__all__ = [
    "HookDecision",
    "InMemoryMessageStore",
]
