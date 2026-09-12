"""Message Store contract models (transport-neutral)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class CanonicalState:
    """Concurrency token plus the authoritative ordered-stream domain."""

    token: str
    target_ref: str
    stream_id: str


@dataclass(frozen=True)
class PreparedPublication:
    """Immutable artifact prepared against a specific canonical state."""

    expected_state: CanonicalState
    message: dict[str, Any]


@dataclass(frozen=True)
class PublicationEvidence:
    """Canonical evidence tying a published envelope to its store version."""

    message: dict[str, Any]
    publication_commit: str


@dataclass(frozen=True)
class CasSuccess:
    kind: Literal["success"] = "success"
    new_state: CanonicalState = field(default_factory=lambda: CanonicalState("", "", ""))
    message: dict[str, Any] = field(default_factory=dict)
    publication_commit: str = ""


@dataclass(frozen=True)
class CasConflict:
    """CAS lost: store tip advanced or sequence already taken. Retry after reread."""

    reason: str
    kind: Literal["conflict"] = "conflict"


@dataclass(frozen=True)
class CasUncertain:
    """CAS outcome unknown: write may or may not have landed.

    Publisher MUST reconcile by message_id before allocating a new candidate.
    """

    reason: str
    kind: Literal["uncertain"] = "uncertain"


CasResult = CasSuccess | CasConflict | CasUncertain


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    message: dict[str, Any] | None = None
    publication_commit: str | None = None
    reason: str | None = None
