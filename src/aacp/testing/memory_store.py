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
    PublicationEvidence,
    VerificationResult,
)


@dataclass(frozen=True)
class HookDecision:
    outcome: Literal["conflict", "uncertain"]
    reason: str
    apply_write: bool = False


CasHook = Callable[[CanonicalState, PreparedPublication, list[dict[str, Any]]], HookDecision | None]


class InMemoryMessageStore:
    """Process-local CAS store for tests only. Not a production Message Store."""

    def __init__(
        self,
        *,
        target_ref: str = "refs/heads/test",
        stream_id: str = "S-test",
        initial: list[dict[str, Any]] | None = None,
        cas_hook: CasHook | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._target_ref = target_ref
        self._stream_id = stream_id
        self._counter = 0
        self._head = "h0"
        self._trees: dict[str, list[dict[str, Any]]] = {
            "h0": [dict(item) for item in (initial or [])]
        }
        self._publication_commits: dict[tuple[str, str], str] = {}
        self.cas_hook = cas_hook
        for item in self._trees["h0"]:
            if "message_id" in item:
                self._publication_commits[("h0", str(item["message_id"]))] = "h0"

    def read_canonical_state(self) -> CanonicalState:
        with self._lock:
            return CanonicalState(self._head, self._target_ref, self._stream_id)

    def list_messages(self, state: CanonicalState) -> list[dict[str, Any]]:
        with self._lock:
            if state.target_ref != self._target_ref or state.stream_id != self._stream_id:
                return []
            return [
                dict(item)
                for item in self._trees[state.token]
                if item.get("stream_id", self._stream_id) == self._stream_id
            ]

    def find_by_message_id(self, state: CanonicalState, message_id: str) -> dict[str, Any] | None:
        for item in self.list_messages(state):
            if item.get("message_id") == message_id:
                return dict(item)
        return None

    def find_publication_evidence(
        self, state: CanonicalState, message_id: str
    ) -> PublicationEvidence | None:
        message = self.find_by_message_id(state, message_id)
        if message is None:
            return None
        with self._lock:
            commit = None
            for token, messages in self._trees.items():
                if any(item.get("message_id") == message_id for item in messages):
                    commit = self._publication_commits.get((token, message_id))
                    if commit:
                        break
        return PublicationEvidence(message=message, publication_commit=commit or state.token)

    def prepare_publication(self, state: CanonicalState, message: dict[str, Any]) -> PreparedPublication:
        return PreparedPublication(expected_state=state, message=dict(message))

    def publish_cas(self, expected_state: CanonicalState, publication: PreparedPublication) -> CasResult:
        with self._lock:
            if expected_state.token != self._head:
                return CasConflict("head_moved")
            if expected_state.target_ref != self._target_ref or expected_state.stream_id != self._stream_id:
                return CasConflict("target_mismatch")

            current = self._trees[self._head]
            message = dict(publication.message)
            sequence = int(message["sequence"])
            used = {
                int(item["sequence"])
                for item in current
                if item.get("stream_id", self._stream_id) == self._stream_id and "sequence" in item
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
        self._publication_commits[(new_token, str(message["message_id"]))] = new_token
        new_state = CanonicalState(new_token, self._target_ref, self._stream_id)
        return CasSuccess(new_state=new_state, message=dict(message), publication_commit=new_token)

    def verify_publication(
        self, state: CanonicalState, message_id: str, sequence: int | None = None
    ) -> VerificationResult:
        found = self.find_by_message_id(state, message_id)
        if found is None:
            return VerificationResult(verified=False, reason="missing")
        if sequence is not None and int(found.get("sequence", -1)) != int(sequence):
            return VerificationResult(verified=False, message=found, reason="sequence_mismatch")
        evidence = self.find_publication_evidence(state, message_id)
        return VerificationResult(
            verified=True,
            message=found,
            publication_commit=evidence.publication_commit if evidence else None,
        )

    def force_commit_for_tests(self, message: dict[str, Any]) -> CanonicalState:
        with self._lock:
            return self._commit_locked(dict(message)).new_state
