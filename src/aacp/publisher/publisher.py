"""Canonical AACP Publisher (Phase 2A skeleton).

Caller does NOT own authoritative sequence. No public fixed_sequence API.
"""

from __future__ import annotations

from typing import Any

from aacp.message_store.contract import MessageStore
from aacp.message_store.models import CasConflict, CasSuccess, CasUncertain
from aacp.publisher.errors import (
    ProtocolInvalid,
    PublicationConflict,
    PublishRetriesExceeded,
    TargetInvalid,
)
from aacp.publisher.models import (
    REQUIRED_ENVELOPE_FIELDS,
    PublicationReceipt,
    TargetBinding,
)
from aacp.publisher.sequence import candidate_sequence, semantic_fingerprint


class Publisher:
    """publish(envelope, target) -> PublicationReceipt against a MessageStore."""

    def __init__(self, store: MessageStore, *, max_attempts: int = 16) -> None:
        self.store = store
        self.max_attempts = max_attempts

    def publish(
        self, envelope: dict[str, Any], target: TargetBinding
    ) -> PublicationReceipt:
        """Publish with CAS allocation. Strips any caller-supplied sequence."""
        prepared = self._validate_and_normalize(envelope, target)

        last_reason = "none"
        for _ in range(self.max_attempts):
            state = self.store.read_canonical_state()
            existing = self.store.find_by_message_id(state, prepared["message_id"])
            if existing is not None:
                return self._receipt_or_conflict(prepared, existing, state.token)

            messages = self.store.list_messages(state)
            sequence = candidate_sequence(messages)
            message = {**prepared, "sequence": sequence}
            publication = self.store.prepare_publication(state, message)
            outcome = self.store.publish_cas(state, publication)

            if isinstance(outcome, CasSuccess):
                return self._verify_and_receipt(outcome.new_state, message)

            if isinstance(outcome, CasConflict):
                last_reason = outcome.reason
                continue

            if isinstance(outcome, CasUncertain):
                last_reason = outcome.reason
                receipt = self._reconcile_uncertain(prepared)
                if receipt is not None:
                    return receipt
                # Proven absent after rediscovery → retry with fresh candidate.
                continue

            last_reason = f"unexpected_outcome:{type(outcome)!r}"

        raise PublishRetriesExceeded(
            f"exhausted {self.max_attempts} attempts; last={last_reason}"
        )

    def _validate_and_normalize(
        self, envelope: dict[str, Any], target: TargetBinding
    ) -> dict[str, Any]:
        if not isinstance(envelope, dict):
            raise ProtocolInvalid("envelope must be an object")
        missing = [field for field in REQUIRED_ENVELOPE_FIELDS if field not in envelope]
        if missing:
            raise ProtocolInvalid(f"missing fields: {', '.join(missing)}")
        if envelope.get("protocol") != target.protocol:
            raise ProtocolInvalid("protocol mismatch")
        if envelope.get("version") != target.version:
            raise ProtocolInvalid("version mismatch")
        if envelope.get("conversation_id") != target.conversation_id:
            raise TargetInvalid("conversation_id does not match target binding")
        stream = envelope.get("stream_id", target.stream_id)
        if stream != target.stream_id:
            raise TargetInvalid("stream_id does not match target binding")

        # Caller MUST NOT own authoritative sequence — always drop it.
        normalized = dict(envelope)
        normalized.pop("sequence", None)
        normalized["stream_id"] = target.stream_id
        normalized["conversation_id"] = target.conversation_id
        return normalized

    def _receipt_or_conflict(
        self,
        prepared: dict[str, Any],
        existing: dict[str, Any],
        publication_commit: str,
    ) -> PublicationReceipt:
        if semantic_fingerprint(existing) != semantic_fingerprint(prepared):
            raise PublicationConflict(
                f"message_id={prepared['message_id']} already published with different content"
            )
        state = self.store.read_canonical_state()
        return PublicationReceipt.from_published(
            existing,
            target_ref=state.target_ref,
            publication_commit=publication_commit or state.token,
        )

    def _reconcile_uncertain(
        self, prepared: dict[str, Any]
    ) -> PublicationReceipt | None:
        """Mandatory path after CasUncertain: reconcile by message_id first."""
        state = self.store.read_canonical_state()
        existing = self.store.find_by_message_id(state, prepared["message_id"])
        if existing is None:
            return None
        return self._receipt_or_conflict(prepared, existing, state.token)

    def _verify_and_receipt(
        self, state, message: dict[str, Any]
    ) -> PublicationReceipt:
        verification = self.store.verify_publication(
            state, message["message_id"], int(message["sequence"])
        )
        if not verification.verified or verification.message is None:
            # Ambiguous verify after apparent success → reconcile, do not invent sequence.
            reconciled = self._reconcile_uncertain(message)
            if reconciled is not None:
                return reconciled
            raise PublishRetriesExceeded(
                f"verification failed for message_id={message['message_id']}: "
                f"{verification.reason}"
            )
        return PublicationReceipt.from_published(
            verification.message,
            target_ref=state.target_ref,
            publication_commit=state.token,
        )
