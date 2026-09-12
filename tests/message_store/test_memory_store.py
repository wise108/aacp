"""Message Store contract tests (in-memory backend)."""

from __future__ import annotations

from aacp.message_store import HookDecision, InMemoryMessageStore
from aacp.message_store.models import CasConflict, CasSuccess, CasUncertain


def test_read_list_cas_verify_roundtrip():
    store = InMemoryMessageStore(target_ref="refs/heads/test")
    state = store.read_canonical_state()
    assert store.list_messages(state) == []

    message = {
        "protocol": "AACP",
        "version": "1.0",
        "message_id": "M-ms-1",
        "conversation_id": "C-test",
        "task_id": "T-test",
        "type": "event",
        "sender": "a",
        "recipient": "b",
        "created_at": "2026-09-12T00:00:00Z",
        "stream_id": "S-test",
        "payload": {},
        "sequence": 1,
    }
    prepared = store.prepare_publication(state, message)
    outcome = store.publish_cas(state, prepared)
    assert isinstance(outcome, CasSuccess)
    verification = store.verify_publication(
        outcome.new_state, "M-ms-1", sequence=1
    )
    assert verification.verified is True
    assert store.find_by_message_id(outcome.new_state, "M-ms-1")["sequence"] == 1


def test_cas_conflict_on_stale_head():
    store = InMemoryMessageStore()
    state = store.read_canonical_state()
    store.force_commit_for_tests(
        {
            "message_id": "M-peer",
            "sequence": 1,
            "conversation_id": "C",
            "stream_id": "S",
            "payload": {},
        }
    )
    prepared = store.prepare_publication(
        state, {"message_id": "M-stale", "sequence": 1, "payload": {}}
    )
    outcome = store.publish_cas(state, prepared)
    assert isinstance(outcome, CasConflict)


def test_cas_rejects_duplicate_sequence_without_force():
    store = InMemoryMessageStore()
    store.force_commit_for_tests({"message_id": "M-1", "sequence": 1, "payload": {}})
    state = store.read_canonical_state()
    prepared = store.prepare_publication(
        state, {"message_id": "M-2", "sequence": 1, "payload": {}}
    )
    outcome = store.publish_cas(state, prepared)
    assert isinstance(outcome, CasConflict)
    assert outcome.reason == "sequence_taken"


def test_hook_uncertain_applied_and_not_applied():
    applied = {"flag": True}

    def hook(expected, publication, current):
        return HookDecision(
            outcome="uncertain",
            reason="test",
            apply_write=applied["flag"],
        )

    store = InMemoryMessageStore(cas_hook=hook)
    state = store.read_canonical_state()
    prepared = store.prepare_publication(
        state, {"message_id": "M-u", "sequence": 1, "payload": {}}
    )
    outcome = store.publish_cas(state, prepared)
    assert isinstance(outcome, CasUncertain)
    assert store.find_by_message_id(store.read_canonical_state(), "M-u") is not None

    store2 = InMemoryMessageStore(
        cas_hook=lambda *_: HookDecision(
            outcome="uncertain", reason="test", apply_write=False
        )
    )
    state2 = store2.read_canonical_state()
    prepared2 = store2.prepare_publication(
        state2, {"message_id": "M-u2", "sequence": 1, "payload": {}}
    )
    outcome2 = store2.publish_cas(state2, prepared2)
    assert isinstance(outcome2, CasUncertain)
    assert store2.find_by_message_id(store2.read_canonical_state(), "M-u2") is None
