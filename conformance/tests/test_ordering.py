"""Conformance tests for AACP ordered multi-writer semantics."""
import pytest

from conformance.harness.ordering import (
    OrderedConsumer,
    OrderedMessage,
    OrderingConflict,
    SequenceAllocator,
    SequenceGap,
    StaleAllocation,
    reconcile_collision,
)


def msg(message_id: str, sequence: int) -> OrderedMessage:
    return OrderedMessage(message_id, "C-test", "S-test", sequence)


def test_sequential_multi_writer_allocation() -> None:
    allocator = SequenceAllocator(initial_sequence=35)
    a = allocator.read()
    seq_a, _ = allocator.allocate(a.version)
    b = allocator.read()
    seq_b, _ = allocator.allocate(b.version)
    assert (seq_a, seq_b) == (35, 36)


def test_concurrent_sequence_allocation_requires_retry() -> None:
    allocator = SequenceAllocator(initial_sequence=35)
    a = allocator.read()
    b = allocator.read()
    seq_a, _ = allocator.allocate(a.version)
    assert seq_a == 35
    with pytest.raises(StaleAllocation):
        allocator.allocate(b.version)
    seq_b, _ = allocator.allocate(allocator.read().version)
    assert seq_b == 36


def test_duplicate_message_is_idempotent() -> None:
    consumer = OrderedConsumer()
    assert consumer.observe(msg("M1", 1)) == "new"
    assert consumer.observe(msg("M1", 1)) == "duplicate"
    assert consumer.cursor_sequence == 1


def test_same_sequence_different_message_is_ordering_conflict() -> None:
    consumer = OrderedConsumer()
    assert consumer.observe(msg("M1", 1)) == "new"
    with pytest.raises(OrderingConflict):
        consumer.observe(msg("M2", 1))
    assert consumer.cursor_sequence == 1
    assert "M2" not in consumer.seen


def test_gap_is_not_silently_accepted() -> None:
    consumer = OrderedConsumer()
    assert consumer.observe(msg("M1", 1)) == "new"
    with pytest.raises(SequenceGap):
        consumer.observe(msg("M3", 3))
    assert consumer.cursor_sequence == 1


def test_out_of_order_message_does_not_move_cursor_backward() -> None:
    consumer = OrderedConsumer()
    assert consumer.observe(msg("M1", 1)) == "new"
    assert consumer.observe(msg("M2", 2)) == "new"
    assert consumer.observe(msg("M-late", 1)) == "late"
    assert consumer.cursor_sequence == 2
    assert consumer.cursor_message_id == "M2"


def test_rediscovery_after_restart_uses_message_identity() -> None:
    consumer = OrderedConsumer()
    assert consumer.observe(msg("M1", 1)) == "new"
    assert consumer.observe(msg("M2", 2)) == "new"
    restarted = OrderedConsumer()
    restarted.cursor_sequence = 2
    restarted.cursor_message_id = "M2"
    assert restarted.observe(msg("M1", 1)) == "late"
    assert restarted.observe(msg("M2", 2)) == "late"
    assert restarted.cursor_sequence == 2


def test_retransmit_preserves_sequence_and_identity() -> None:
    original = msg("M1", 7)
    retransmit = msg("M1", 7)
    assert original == retransmit


def test_ack_result_are_distinct_messages_but_can_share_causation() -> None:
    command = msg("CMD", 10)
    ack = msg("ACK", 11)
    result = msg("RESULT", 12)
    assert len({command.message_id, ack.message_id, result.message_id}) == 3
    assert command.sequence < ack.sequence < result.sequence


def test_historical_collision_is_immutable_and_detectable() -> None:
    records = [msg("M1", 35), msg("M2", 35)]
    assert records[0].sequence == records[1].sequence == 35
    assert records[0].message_id != records[1].message_id
    consumer = OrderedConsumer()
    consumer.observe(msg("M-before", 34))
    with pytest.raises(OrderingConflict):
        consumer.observe(records[0])
    assert records == [msg("M1", 35), msg("M2", 35)]


def test_collision_reconciliation_preserves_ids_and_allocates_after_canonical_max() -> None:
    records = [msg("M1", 35), msg("M2", 35)]
    result = reconcile_collision(records, canonical_max_sequence=37)
    assert result.conflict_sequence == 35
    assert result.message_ids == ("M1", "M2")
    assert result.next_sequence == 38
    assert records == [msg("M1", 35), msg("M2", 35)]
