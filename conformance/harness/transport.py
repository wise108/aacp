"""Deterministic transport for AACP conformance tests."""
from dataclasses import dataclass
from enum import Enum

from .model import Message


class FaultKind(str, Enum):
    DROP = "drop"
    DUPLICATE = "duplicate"
    DELAY = "delay"
    CRASH = "crash"


class CrashInjected(RuntimeError):
    pass


@dataclass(frozen=True)
class Fault:
    point: str
    kind: FaultKind
    message_id: str | None = None
    count: int = 1


class DeterministicTransport:
    """FIFO transport whose faults are explicit and reproducible."""

    def __init__(self, faults: list[Fault] | None = None) -> None:
        self.queue: list[Message] = []
        self.faults = list(faults or [])
        self.delivered: list[str] = []
        self._hits: dict[tuple[str, str | None, FaultKind], int] = {}

    def _fault(self, point: str, message: Message) -> Fault | None:
        for fault in self.faults:
            if fault.point != point:
                continue
            if fault.message_id is not None and fault.message_id != message.message_id:
                continue
            key = (fault.point, fault.message_id, fault.kind)
            hits = self._hits.get(key, 0)
            if hits < fault.count:
                self._hits[key] = hits + 1
                return fault
        return None

    def send(self, message: Message) -> None:
        fault = self._fault("SEND_BEFORE", message)
        if fault and fault.kind is FaultKind.CRASH:
            raise CrashInjected("SEND_BEFORE")
        if fault and fault.kind is FaultKind.DROP:
            return
        self.queue.append(message)
        fault = self._fault("SEND_AFTER", message)
        if fault and fault.kind is FaultKind.CRASH:
            raise CrashInjected("SEND_AFTER")
        if fault and fault.kind is FaultKind.DUPLICATE:
            self.queue.append(message)

    def receive(self) -> Message | None:
        if not self.queue:
            return None
        message = self.queue.pop(0)
        fault = self._fault("RECEIVE_BEFORE", message)
        if fault and fault.kind is FaultKind.CRASH:
            raise CrashInjected("RECEIVE_BEFORE")
        if fault and fault.kind is FaultKind.DROP:
            return self.receive()
        self.delivered.append(message.message_id)
        fault = self._fault("RECEIVE_AFTER", message)
        if fault and fault.kind is FaultKind.CRASH:
            raise CrashInjected("RECEIVE_AFTER")
        return message

    def reorder(self, index: int, message_index: int = 0) -> None:
        if not self.queue:
            return
        item = self.queue.pop(message_index)
        self.queue.insert(index, item)
