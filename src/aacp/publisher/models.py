"""Publisher models: TargetBinding and PublicationReceipt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


REQUIRED_ENVELOPE_FIELDS = (
    "protocol",
    "version",
    "message_id",
    "conversation_id",
    "task_id",
    "type",
    "sender",
    "recipient",
    "created_at",
    "payload",
)


@dataclass(frozen=True)
class TargetBinding:
    """Authorized publication target. Callers cannot freely invent coords."""

    target_ref: str
    conversation_id: str
    stream_id: str
    protocol: str = "AACP"
    version: str = "1.0"


@dataclass(frozen=True)
class PublicationReceipt:
    """Evidence that a message is verified in the canonical Message Store.

    Does NOT mean: accepted, executed, result produced, or task completed.
    """

    message_id: str
    conversation_id: str
    stream_id: str
    sequence: int
    target_ref: str
    publication_commit: str
    published_at: str
    verified: bool

    @staticmethod
    def from_published(
        message: dict[str, Any],
        *,
        target_ref: str,
        publication_commit: str,
        published_at: str | None = None,
    ) -> PublicationReceipt:
        return PublicationReceipt(
            message_id=str(message["message_id"]),
            conversation_id=str(message["conversation_id"]),
            stream_id=str(message["stream_id"]),
            sequence=int(message["sequence"]),
            target_ref=target_ref,
            publication_commit=publication_commit,
            published_at=published_at
            or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            verified=True,
        )
