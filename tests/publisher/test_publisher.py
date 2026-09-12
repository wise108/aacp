"""Publisher contract tests (Phase 2A)."""

from __future__ import annotations

import inspect
import threading

import pytest

from aacp.message_store import HookDecision, InMemoryMessageStore
from aacp.message_store.models import CasConflict, CasSuccess
from aacp.publisher import (
    PublicationConflict,
    PublicationReceipt,
    Publisher,
    publish,
)
from aacp.publisher.publisher import Publisher as PublisherClass
from aacp.publisher.sequence import candidate_sequence

from .conftest import TARGET, envelope


def test_single_publication():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    receipt = publish(store, envelope("M-1"), TARGET)
    assert isinstance(receipt, PublicationReceipt)
    assert receipt.message_id == "M-1"
    assert receipt.sequence == 1
    assert receipt.verified is True
    assert receipt.target_ref == TARGET.target_ref
    assert receipt.publication_commit


def test_duplicate_message_id_idempotent():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    first = publish(store, envelope("M-dup"), TARGET)
    second = publish(store, envelope("M-dup"), TARGET)
    assert second.message_id == first.message_id
    assert second.sequence == first.sequence
    messages = store.list_messages(store.read_canonical_state())
    assert len(messages) == 1


def test_duplicate_message_id_conflict_on_different_content():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    publish(store, envelope("M-x", payload={"a": 1}), TARGET)
    with pytest.raises(PublicationConflict):
        publish(store, envelope("M-x", payload={"a": 2}), TARGET)


def test_cas_conflict_reread_retry():
    calls = {"n": 0}

    def hook(expected, publication, current):
        calls["n"] += 1
        if calls["n"] == 1:
            return HookDecision(outcome="conflict", reason="simulated_head_moved")
        return None

    store = InMemoryMessageStore(target_ref=TARGET.target_ref, cas_hook=hook)
    # Peer takes seq=1 while first attempt conflicts.
    store.force_commit_for_tests(
        {
            **envelope("M-peer"),
            "sequence": 1,
        }
    )
    receipt = publish(store, envelope("M-retry"), TARGET)
    assert receipt.sequence == 2
    assert calls["n"] >= 1


def test_concurrent_writers_unique_sequences():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    results: list[PublicationReceipt] = []
    errors: list[BaseException] = []

    def worker(message_id: str) -> None:
        try:
            results.append(Publisher(store).publish(envelope(message_id), TARGET))
        except BaseException as exc:  # noqa: BLE001 — collect for assertion
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(f"M-c{i}",)) for i in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    sequences = sorted(item.sequence for item in results)
    assert sequences == list(range(1, 9))
    assert len({item.message_id for item in results}) == 8


def test_two_writers_cannot_own_same_sequence():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    state = store.read_canonical_state()
    prep_a = store.prepare_publication(state, {**envelope("M-a"), "sequence": 1})
    prep_b = store.prepare_publication(state, {**envelope("M-b"), "sequence": 1})
    first = store.publish_cas(state, prep_a)
    second = store.publish_cas(state, prep_b)
    assert isinstance(first, CasSuccess)
    assert isinstance(second, CasConflict)

    receipt_b = publish(store, envelope("M-b"), TARGET)
    assert receipt_b.sequence == 2
    messages = store.list_messages(store.read_canonical_state())
    assert {m["message_id"]: int(m["sequence"]) for m in messages} == {
        "M-a": 1,
        "M-b": 2,
    }


def test_caller_sequence_ignored():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    receipt = publish(store, envelope("M-caller-seq", sequence=99), TARGET)
    assert receipt.sequence == 1
    published = store.find_by_message_id(store.read_canonical_state(), "M-caller-seq")
    assert published is not None
    assert published["sequence"] == 1


def test_no_public_fixed_sequence_parameter():
    signature = inspect.signature(PublisherClass.publish)
    assert "fixed_sequence" not in signature.parameters
    signature_fn = inspect.signature(publish)
    assert "fixed_sequence" not in signature_fn.parameters


def test_successful_cas_uniquely_owns_sequence():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    r1 = publish(store, envelope("M-own-1"), TARGET)
    r2 = publish(store, envelope("M-own-2"), TARGET)
    assert r1.sequence == 1
    assert r2.sequence == 2
    messages = store.list_messages(store.read_canonical_state())
    by_seq = {int(item["sequence"]): item["message_id"] for item in messages}
    assert by_seq[1] == "M-own-1"
    assert by_seq[2] == "M-own-2"


def test_publication_verification_on_receipt():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    receipt = publish(store, envelope("M-ver"), TARGET)
    assert receipt.verified is True
    state = store.read_canonical_state()
    verification = store.verify_publication(state, "M-ver", receipt.sequence)
    assert verification.verified is True


def test_receipt_does_not_imply_execution_or_completion():
    store = InMemoryMessageStore(target_ref=TARGET.target_ref)
    receipt = publish(store, envelope("M-receipt-semantics"), TARGET)
    fields = set(PublicationReceipt.__dataclass_fields__)
    assert "verified" in fields
    assert "accepted" not in fields
    assert "executed" not in fields
    assert "completed" not in fields
    assert "task_state" not in fields
    # Receipt is publication evidence only.
    assert receipt.verified is True
    assert not hasattr(receipt, "execution_status")


def test_uncertain_then_peer_took_sequence_requires_reconcile_not_blind_n_plus_1():
    """Writer A uncertain at N; Writer B publishes N; A must reconcile by message_id."""
    events: list[str] = []
    injected = {"done": False}

    def hook_with_peer(expected, publication, current):
        mid = publication.message["message_id"]
        if mid == "M-A" and not injected["done"]:
            injected["done"] = True
            events.append("A_uncertain")
            # Peer B claims sequence N while A's outcome is unknown.
            store.force_commit_for_tests({**envelope("M-B"), "sequence": 1})
            events.append("B_published_seq1")
            return HookDecision(
                outcome="uncertain", reason="A_unknown", apply_write=False
            )
        events.append(f"cas_ok:{mid}:seq={publication.message['sequence']}")
        return None

    store = InMemoryMessageStore(target_ref=TARGET.target_ref, cas_hook=hook_with_peer)

    class TrackingPublisher(Publisher):
        def _reconcile_uncertain(self, prepared):
            events.append(f"reconcile:{prepared['message_id']}")
            return super()._reconcile_uncertain(prepared)

    receipt = TrackingPublisher(store).publish(envelope("M-A"), TARGET)

    assert "reconcile:M-A" in events
    assert receipt.message_id == "M-A"
    assert receipt.sequence == 2
    state = store.read_canonical_state()
    messages = store.list_messages(state)
    assert {m["message_id"]: int(m["sequence"]) for m in messages} == {
        "M-B": 1,
        "M-A": 2,
    }
    assert candidate_sequence([{"sequence": 1}]) == 2


def test_uncertain_lost_response_after_success_idempotent_retry():
    """CAS actually succeeded; response lost; retry discovers by message_id."""
    events: list[str] = []
    first = {"done": False}

    def hook(expected, publication, current):
        if publication.message["message_id"] == "M-lost" and not first["done"]:
            first["done"] = True
            events.append("uncertain_applied")
            return HookDecision(
                outcome="uncertain", reason="lost_response", apply_write=True
            )
        events.append("unexpected_second_cas")
        return None

    store = InMemoryMessageStore(target_ref=TARGET.target_ref, cas_hook=hook)

    class TrackingPublisher(Publisher):
        def _reconcile_uncertain(self, prepared):
            events.append(f"reconcile:{prepared['message_id']}")
            return super()._reconcile_uncertain(prepared)

    receipt = TrackingPublisher(store).publish(envelope("M-lost"), TARGET)
    assert receipt.message_id == "M-lost"
    assert receipt.sequence == 1
    assert "reconcile:M-lost" in events
    assert "unexpected_second_cas" not in events
    messages = store.list_messages(store.read_canonical_state())
    assert len(messages) == 1
    assert messages[0]["message_id"] == "M-lost"

    # Explicit retransmission: same message_id, no new sequence.
    again = publish(store, envelope("M-lost"), TARGET)
    assert again.sequence == 1
    assert len(store.list_messages(store.read_canonical_state())) == 1
