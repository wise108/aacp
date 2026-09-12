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
    VerificationResult,
)


class MessageStore(Protocol):
    """Transport-neutral CAS Message Store."""

    def read_canonical_state(self) -> CanonicalState:
        """Return the authoritative store tip concurrency token."""

    def list_messages(self, state: CanonicalState) -> list[dict[str, Any]]:
        """List published envelopes visible at ``state`` for the store ordering domain."""

    def find_by_message_id(
        self, state: CanonicalState, message_id: str
    ) -> dict[str, Any] | None:
        """Return the published envelope with ``message_id``, if present at ``state``."""

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
        """Confirm the message is discoverable at ``state``."""
