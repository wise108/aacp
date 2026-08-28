"""Minimal transport-neutral model used by the AACP conformance harness."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class State(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Message:
    message_id: str
    task_id: str
    type: str
    sequence: int
    payload: dict[str, Any] = field(default_factory=dict)
    causation_id: str | None = None
    correlation_id: str | None = None


@dataclass
class Task:
    task_id: str
    state: State = State.PENDING
    state_version: int = 0
    execution_attempts: int = 0
    side_effects: int = 0
    result_message_id: str | None = None


class StateConflict(Exception):
    pass


class InvalidTransition(Exception):
    pass


class Store:
    """Tiny deterministic durable-state stand-in for reference tests."""

    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.processed_messages: set[str] = set()
        self.messages: dict[str, Message] = {}
        self.publication: dict[str, str] = {}

    def transition(self, task_id: str, expected: int, new_state: State) -> Task:
        task = self.tasks[task_id]
        if task.state_version != expected:
            raise StateConflict(task_id)
        allowed = {
            State.PENDING: {State.ACCEPTED, State.CANCELLED},
            State.ACCEPTED: {State.IN_PROGRESS, State.CANCELLED},
            State.IN_PROGRESS: {State.COMPLETED, State.FAILED, State.CANCELLED, State.BLOCKED},
            State.BLOCKED: {State.IN_PROGRESS, State.CANCELLED},
            State.FAILED: {State.IN_PROGRESS},
            State.COMPLETED: set(),
            State.CANCELLED: set(),
        }
        if new_state not in allowed[task.state]:
            raise InvalidTransition(f"{task.state} -> {new_state}")
        task.state = new_state
        task.state_version += 1
        return task

    def accept(self, message: Message) -> str:
        if message.message_id in self.processed_messages:
            return "duplicate"
        task = self.tasks.setdefault(message.task_id, Task(message.task_id))
        if task.state != State.PENDING:
            self.processed_messages.add(message.message_id)
            return "duplicate"
        self.transition(message.task_id, task.state_version, State.ACCEPTED)
        self.processed_messages.add(message.message_id)
        self.messages[message.message_id] = message
        return "accepted"

    def execute(self, task_id: str, perform_side_effect: bool = True) -> None:
        task = self.tasks[task_id]
        self.transition(task_id, task.state_version, State.IN_PROGRESS)
        task.execution_attempts += 1
        if perform_side_effect:
            task.side_effects += 1

    def complete(self, task_id: str, result: Message) -> None:
        task = self.tasks[task_id]
        self.transition(task_id, task.state_version, State.COMPLETED)
        task.result_message_id = result.message_id
        self.messages[result.message_id] = result

    def publish(self, message_id: str) -> None:
        self.publication[message_id] = "PUBLISHED"
