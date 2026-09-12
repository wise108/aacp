"""Publisher contract tests (Phase 2A/2B-0.1 hardening)."""

from __future__ import annotations

import inspect
import threading

import pytest

from aacp.message_store.models import CasConflict, CasSuccess
from aacp.publisher import (
    PublicationConflict,
    PublicationReceipt,
    Publisher,
    TargetInvalid,
)
from aacp.publisher.sequence import candidate_sequence
from aacp.testing import HookDecision, InMemoryMessageStore

from .conftest import TARGET, envelope


def test_single_publication():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    receipt = Publisher(store).publish(envelope("M-1"), TARGET)
    assert isinstance(receipt, PublicationReceipt)
    assert receipt.message_id == "M-1"
    assert receipt.sequence == 1
    assert receipt.verified is True
    assert receipt.target_ref == TARGET.target_ref
    assert receipt.publication_commit == "h1"


def test_duplicate_message_id_idempotent_preserves_original_publication_commit():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    first = Publisher(store).publish(envelope("M-dup"), TARGET)
    Publisher(store).publish(envelope("M-other"), TARGET)
    second = Publisher(store).publish(envelope("M-dup"), TARGET)
    assert second.message_id == first.message_id
    assert second.sequence == first.sequence
    assert second.publication_commit == first.publication_commit == "h1"
    assert len(store.list_messages(store.read_canonical_state())) == 2


def test_duplicate_message_id_conflict_on_different_content():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    Publisher(store).publish(envelope("M-x", payload={"a": 1}), TARGET)
    with pytest.raises(PublicationConflict):
        Publisher(store).publish(envelope("M-x", payload={"a": 2}), TARGET)


def test_cas_conflict_reread_retry():
    calls = {"n": 0}

    def hook(expected, publication, current):
        calls["n"] += 1
        if calls["n"] == 1:
            return HookDecision(outcome="conflict", reason="simulated_head_moved")
        return None

    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id, cas_hook=hook)
    store.force_commit_for_tests({**envelope("M-peer"), "sequence": 1})
    receipt = Publisher(store).publish(envelope("M-retry"), TARGET)
    assert receipt.sequence == 2
    assert calls["n"] >= 1


def test_concurrent_writers_unique_sequences():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    results: list[PublicationReceipt] = []
    errors: list[BaseException] = []

    def worker(message_id: str) -> None:
        try:
            results.append(Publisher(store).publish(envelope(message_id), TARGET))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(f"M-c{i}",)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    assert sorted(item.sequence for item in results) == list(range(1, 9))
    assert len({item.message_id for item in results}) == 8


def test_two_writers_cannot_own_same_sequence():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    state = store.read_canonical_state()
    prep_a = store.prepare_publication(state, {**envelope("M-a"), "sequence": 1})
    prep_b = store.prepare_publication(state, {**envelope("M-b"), "sequence": 1})
    first = store.publish_cas(state, prep_a)
    second = store.publish_cas(state, prep_b)
    assert isinstance(first, CasSuccess)
    assert isinstance(second, CasConflict)
    receipt_b = Publisher(store).publish(envelope("M-b"), TARGET)
    assert receipt_b.sequence == 2


def test_caller_sequence_ignored():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    receipt = Publisher(store).publish(envelope("M-caller-seq", sequence=99), TARGET)
    assert receipt.sequence == 1


def test_public_publish_api_is_envelope_target_only():
    signature = inspect.signature(Publisher.publish)
    assert list(signature.parameters) == ["self", "envelope", "target"]
    assert "fixed_sequence" not in signature.parameters
    assert "store" not in signature.parameters

    import aacp
    import aacp.publisher as publisher_pkg
    assert "publish" not in aacp.__all__
    assert "publish" not in publisher_pkg.__all__
    assert not hasattr(aacp, "publish")
    assert not hasattr(publisher_pkg, "publish")


def test_successful_cas_uniquely_owns_sequence():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    r1 = Publisher(store).publish(envelope("M-own-1"), TARGET)
    r2 = Publisher(store).publish(envelope("M-own-2"), TARGET)
    assert r1.sequence == 1
    assert r2.sequence == 2


def test_publication_verification_on_receipt():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    receipt = Publisher(store).publish(envelope("M-ver"), TARGET)
    verification = store.verify_publication(
        store.read_canonical_state(), "M-ver", receipt.sequence
    )
    assert verification.verified is True
    assert verification.publication_commit == receipt.publication_commit


def test_receipt_does_not_imply_execution_or_completion():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    receipt = Publisher(store).publish(envelope("M-receipt-semantics"), TARGET)
    fields = set(PublicationReceipt.__dataclass_fields__)
    assert "verified" in fields
    assert "accepted" not in fields
    assert "executed" not in fields
    assert "completed" not in fields
    assert "task_state" not in fields
    assert receipt.verified is True
    assert not hasattr(receipt, "execution_status")


def test_uncertain_then_peer_took_sequence_requires_reconcile_not_blind_n_plus_1():
    events: list[str] = []
    injected = {"done": False}

    def hook_with_peer(expected, publication, current):
        mid = publication.message["message_id"]
        if mid == "M-A" and not injected["done"]:
            injected["done"] = True
            events.append("A_uncertain")
            store.force_commit_for_tests({**envelope("M-B"), "sequence": 1})
            events.append("B_published_seq1")
            return HookDecision(outcome="uncertain", reason="A_unknown", apply_write=False)
        events.append(f"cas_ok:{mid}:seq={publication.message['sequence']}")
        return None

    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id, cas_hook=hook_with_peer)

    class TrackingPublisher(Publisher):
        def _reconcile_uncertain(self, prepared, target):
            events.append(f"reconcile:{prepared['message_id']}")
            return super()._reconcile_uncertain(prepared, target)

    receipt = TrackingPublisher(store).publish(envelope("M-A"), TARGET)
    assert "reconcile:M-A" in events
    assert receipt.message_id == "M-A"
    assert receipt.sequence == 2
    assert candidate_sequence([{"sequence": 1}]) == 2


def test_uncertain_lost_response_after_success_idempotent_retry():
    events: list[str] = []
    first = {"done": False}

    def hook(expected, publication, current):
        if publication.message["message_id"] == "M-lost" and not first["done"]:
            first["done"] = True
            events.append("uncertain_applied")
            return HookDecision(outcome="uncertain", reason="lost_response", apply_write=True)
        events.append("unexpected_second_cas")
        return None

    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id, cas_hook=hook)

    class TrackingPublisher(Publisher):
        def _reconcile_uncertain(self, prepared, target):
            events.append(f"reconcile:{prepared['message_id']}")
            return super()._reconcile_uncertain(prepared, target)

    receipt = TrackingPublisher(store).publish(envelope("M-lost"), TARGET)
    assert receipt.sequence == 1
    assert receipt.publication_commit == "h1"
    assert "reconcile:M-lost" in events
    assert "unexpected_second_cas" not in events
    again = Publisher(store).publish(envelope("M-lost"), TARGET)
    assert again.sequence == 1
    assert again.publication_commit == receipt.publication_commit


def test_target_ref_mismatch_rejected_before_idempotency_or_allocation():
    store = InMemoryMessageStore(target_ref="refs/heads/canonical", stream_id=TARGET.stream_id)
    bad_target = TargetBinding(
        target_ref="refs/heads/other",
        conversation_id=TARGET.conversation_id,
        stream_id=TARGET.stream_id,
    )
    with pytest.raises(TargetInvalid, match="target_ref"):
        Publisher(store).publish(envelope("M-target-ref"), bad_target)


def test_stream_domain_is_explicit_in_canonical_state():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref, stream_id=TARGET.stream_id)
    state = store.read_canonical_state()
    assert state.stream_id == TARGET.stream_id
    assert state.target_ref == TARGET.target_ref


def test_other_stream_does_not_affect_candidate_sequence():
    store = InMemoryMessageStore(
        target_ref=TARGET.target_ref,
        stream_id=TARGET.stream_id,
        initial=[{**envelope("M-other-stream"), "stream_id": "S-other", "sequence": 99}],
    )
    receipt = Publisher(store).publish(envelope("M-domain"), TARGET)
    assert receipt.sequence == 1
