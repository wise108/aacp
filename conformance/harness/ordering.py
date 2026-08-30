"""Deterministic ordered-stream model for AACP transport conformance."""
from dataclasses import dataclass


class OrderingConflict(Exception):
    pass


class SequenceGap(Exception):
    pass


class StaleAllocation(Exception):
    pass


@dataclass(frozen=True)
class OrderedMessage:
    message_id: str
    conversation_id: str
    stream_id: str
    sequence: int


@dataclass(frozen=True)
class AllocationState:
    version: int
    next_sequence: int


class SequenceAllocator:
    """CAS-protected deterministic sequence allocator."""

    def __init__(self, initial_sequence: int = 1) -> None:
        self.version = 0
        self.next_sequence = initial_sequence

    def read(self) -> AllocationState:
        return AllocationState(self.version, self.next_sequence)

    def allocate(self, expected_version: int) -> tuple[int, int]:
        if expected_version != self.version:
            raise StaleAllocation("canonical state advanced")
        sequence = self.next_sequence
        self.next_sequence += 1
        self.version += 1
        return sequence, self.version


class OrderedConsumer:
    """Consumer that separates sequence ordering from message identity."""

    def __init__(self) -> None:
        self.cursor_sequence = 0
        self.cursor_message_id: str | None = None
        self.seen: set[str] = set()
        self.by_sequence: dict[int, str] = {}

    def observe(self, message: OrderedMessage) -> str:
        if message.message_id in self.seen:
            return "duplicate"

        existing = self.by_sequence.get(message.sequence)
        if existing is not None and existing != message.message_id:
            raise OrderingConflict(message.sequence)

        if message.sequence > self.cursor_sequence + 1:
            raise SequenceGap((self.cursor_sequence, message.sequence))

        if message.sequence <= self.cursor_sequence:
            self.seen.add(message.message_id)
            self.by_sequence[message.sequence] = message.message_id
            return "late"

        self.seen.add(message.message_id)
        self.by_sequence[message.sequence] = message.message_id
        self.cursor_sequence = message.sequence
        self.cursor_message_id = message.message_id
        return "new"
