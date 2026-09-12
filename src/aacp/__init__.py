"""AACP Publication Layer skeleton (Phase 2A).

Canonical API:

    Publisher(store).publish(envelope, target) -> PublicationReceipt

``aacp.testing`` provides test-only Message Store doubles — not for production.
"""

from aacp.publisher import PublicationReceipt, Publisher, TargetBinding
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
    "ProtocolInvalid",
    "PublicationConflict",
    "PublishRetriesExceeded",
    "TargetInvalid",
]
