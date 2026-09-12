"""AACP Publication Layer skeleton (Phase 2A).

This package provides the canonical Publisher + Message Store contracts and a
test-only in-memory Message Store. Production Git/GitHub adapters are Phase 2B.
"""

from aacp.publisher import PublicationReceipt, Publisher, TargetBinding, publish
from aacp.publisher.errors import (
    ProtocolInvalid,
    PublicationConflict,
    PublishRetriesExceeded,
    TargetInvalid,
)

__all__ = [
    "PublicationReceipt",
    "Publisher",
    "TargetBinding",
    "publish",
    "ProtocolInvalid",
    "PublicationConflict",
    "PublishRetriesExceeded",
    "TargetInvalid",
]
