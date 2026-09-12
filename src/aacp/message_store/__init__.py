"""Production Message Store package: contract + models only.

Test backends live in ``aacp.testing`` (not exported here).
Git / GitHub API adapters are Phase 2B.
"""

from aacp.message_store.contract import MessageStore
from aacp.message_store.models import (
    CanonicalState,
    CasConflict,
    CasResult,
    CasSuccess,
    CasUncertain,
    PreparedPublication,
    VerificationResult,
)

__all__ = [
    "MessageStore",
    "CanonicalState",
    "CasConflict",
    "CasResult",
    "CasSuccess",
    "CasUncertain",
    "PreparedPublication",
    "VerificationResult",
]
