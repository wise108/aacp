"""Executable conformance scenarios for the AACP GitHub ordered-stream profile."""

import pytest

from conformance.harness.ordering import (
    OrderedConsumer,
    OrderedMessage,
    OrderingConflict,
    SequenceGap,
    SequenceAllocator,
    StaleAllocation,
    reconcile_collision,
)


def msg(message_id: str, sequence: int) -> OrderedMessage:
    return OrderedMessage(message_id, "C-github", "S-dialogue", sequence)


def test_g1_sequential_allocation_is_strictly_increasing() -> None:
    allocator = SequenceAllocator(initial_sequence=35)
    first = allocator.read()
    seq1, _ = allocator.allocate(first.version)
    second = allocator.read()
    seq2, _ = allocator.allocate(second.version)
    assert (seq1, seq2) == (35, 36)


def test_g2_stale_writer_must_reread_before_retry() -> None:
    allocator = SequenceAllocator(initial_sequence=35)
    writer_a = allocator.read()
    writer_b = allocator.read()
    assert allocator.allocate(writer_a.version)[0] == 35
    with pytest.raises(StaleAllocation):
        allocator.allocate(writer_b.version)
    refreshed = allocator.read()
    assert allocator.allocate(refreshed.version)[0] == 36


def test_g3_historical_collision_is_detected_and_preserved() -> None:
    records = [msg("M-A", 35), msg("M-B", 35)]
    consumer = OrderedConsumer()
    consumer.observe(msg("M-34", 34))
    assert consumer.observe(records[0]) == "new"
    with pytest.raises(OrderingConflict):
        consumer.observe(records[1])
    assert records == [msg("M-A", 35), msg("M-B", 35)]
    assert consumer.cursor_sequence == 35
    assert consumer.cursor_message_id == "M-A"


def test_g4_collision_reconciliation_preserves_history_and_selects_next_sequence() -> None:
    records = [msg("M-A", 35), msg("M-B", 35)]
    result = reconcile_collision(records, canonical_max_sequence=37)
    assert result.conflict_sequence == 35
    assert result.message_ids == ("M-A", "M-B")
    assert result.next_sequence == 38
    assert records == [msg("M-A", 35), msg("M-B", 35)]


def test_g5_real_gap_is_distinct_from_collision() -> None:
    consumer = OrderedConsumer()
    consumer.observe(msg("M-34", 34))
    with pytest.raises(SequenceGap):
        consumer.observe(msg("M-36", 36))
    assert consumer.cursor_sequence == 34


def test_g6_restart_rediscovery_does_not_cross_unresolved_collision() -> None:
    durable = [msg("M-34", 34), msg("M-A", 35), msg("M-B", 35)]
    restarted = OrderedConsumer()
    restarted.cursor_sequence = 34
    restarted.cursor_message_id = "M-34"
    assert restarted.observe(durable[0]) == "late"
    assert restarted.observe(durable[1]) == "new"
    with pytest.raises(OrderingConflict):
        restarted.observe(durable[2])
    assert restarted.cursor_sequence == 35
    assert restarted.cursor_message_id == "M-A"
    assert durable[1:] == [msg("M-A", 35), msg("M-B", 35)]
