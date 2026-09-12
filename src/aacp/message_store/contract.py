"""Abstract Message Store contract used by the Publisher.

Git CLI and GitHub Git Data API are future backends of this contract (Phase 2B).
They are not separate AACP transports.
"""

from __future__ import annotations

from typing import Any, Protocol

from aacp.message_store.models import (
    CanonicalState,
    CasResult,
    PreparedPublication,
    PublicationEvidence,
    VerificationResult,
)


class MessageStore(Protocol):
    """Transport-neutral CAS Message Store for one canonical target/stream."""

    def read_canonical_state(self) -> CanonicalState:
        """Return the authoritative tip token, target ref, and stream domain."""

    def list_messages(self, state: CanonicalState) -> list[dict[str, Any]]:
        """List envelopes visible at ``state`` for that state's one stream domain."""

    def find_by_message_id(
        self, state: CanonicalState, message_id: str
    ) -> dict[str, Any] | None:
        """Return the published envelope with ``message_id``, if present at ``state``."""

    def find_publication_evidence(
        self, state: CanonicalState, message_id: str
    ) -> PublicationEvidence | None:
        """Return the envelope plus the exact canonical publication version, if present."""

    def prepare_publication(
        self, state: CanonicalState, message: dict[str, Any]
    ) -> PreparedPublication:
        """Build an immutable publication against ``state`` without consuming sequence."""

    def publish_cas(
        self, expected_state: CanonicalState, publication: PreparedPublication
    ) -> CasResult:
        """Compare-and-swap publish. MUST NOT force-update past concurrent writers."""

    def verify_publication(
        self,
        state: CanonicalState,
        message_id: str,
        sequence: int | None = None,
    ) -> VerificationResult:
        """Confirm the message and exact publication version are discoverable at ``state``."""
