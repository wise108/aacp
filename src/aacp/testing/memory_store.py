"""In-memory Message Store — TEST-ONLY (not a production backend).

Production code MUST use a real Message Store adapter (Phase 2B: Git / GitHub API).
Import from ``aacp.testing``, never treat this as part of ``aacp.message_store``.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Literal

from aacp.message_store.models import (
    CanonicalState,
    CasConflict,
    CasResult,
    CasSuccess,
    CasUncertain,
    PreparedPublication,
    VerificationResult,
)


@dataclass(frozen=True)
class HookDecision:
    """Test-only CAS override.

    ``apply_write`` controls whether an uncertain outcome actually mutated the store.
    """

    outcome: Literal["conflict", "uncertain"]
    reason: str
    apply_write: bool = False


CasHook = Callable[
    [CanonicalState, PreparedPublication, list[dict[str, Any]]],
    HookDecision | None,
]


class InMemoryMessageStore:
    """Process-local CAS store for tests only. Not a production Message Store."""

    def __init__(
        self,
        *,
        target_ref: str = "refs/heads/test",
        initial: list[dict[str, Any]] | None = None,
        cas_hook: CasHook | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._target_ref = target_ref
        self._counter = 0
        self._head = "h0"
        self._trees: dict[str, list[dict[str, Any]]] = {
            "h0": [dict(item) for item in (initial or [])]
        }
        self.cas_hook = cas_hook

    def read_canonical_state(self) -> CanonicalState:
        with self._lock:
            return CanonicalState(token=self._head, target_ref=self._target_ref)

    def list_messages(self, state: CanonicalState) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self._trees[state.token]]

    def find_by_message_id(
        self, state: CanonicalState, message_id: str
    ) -> dict[str, Any] | None:
        for item in self.list_messages(state):
            if item.get("message_id") == message_id:
                return dict(item)
        return None

    def prepare_publication(
        self, state: CanonicalState, message: dict[str, Any]
    ) -> PreparedPublication:
        return PreparedPublication(expected_state=state, message=dict(message))

    def publish_cas(
        self, expected_state: CanonicalState, publication: PreparedPublication
    ) -> CasResult:
        with self._lock:
            if expected_state.token != self._head:
                return CasConflict("head_moved")

            current = self._trees[self._head]
            message = dict(publication.message)
            sequence = int(message["sequence"])
            used = {
                int(item["sequence"]) for item in current if "sequence" in item
            }
            if sequence in used:
                return CasConflict("sequence_taken")

            if self.cas_hook is not None:
                decision = self.cas_hook(expected_state, publication, current)
                if decision is not None:
                    if decision.outcome == "conflict":
                        return CasConflict(decision.reason)
                    if decision.apply_write:
                        self._commit_locked(message)
                    return CasUncertain(decision.reason)

            return self._commit_locked(message)

    def _commit_locked(self, message: dict[str, Any]) -> CasSuccess:
        self._counter += 1
        new_token = f"h{self._counter}"
        self._trees[new_token] = [*self._trees[self._head], dict(message)]
        self._head = new_token
        new_state = CanonicalState(token=new_token, target_ref=self._target_ref)
        return CasSuccess(new_state=new_state, message=dict(message))

    def verify_publication(
        self,
        state: CanonicalState,
        message_id: str,
        sequence: int | None = None,
    ) -> VerificationResult:
        found = self.find_by_message_id(state, message_id)
        if found is None:
            return VerificationResult(verified=False, reason="missing")
        if sequence is not None and int(found.get("sequence", -1)) != int(sequence):
            return VerificationResult(
                verified=False, message=found, reason="sequence_mismatch"
            )
        return VerificationResult(verified=True, message=found)

    def force_commit_for_tests(self, message: dict[str, Any]) -> CanonicalState:
        """Test helper: peer writer bypasses Publisher."""
        with self._lock:
            result = self._commit_locked(dict(message))
            return result.new_state
