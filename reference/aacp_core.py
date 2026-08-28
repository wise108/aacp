"""Minimal in-memory reference model for AACP Core 1.0.

This is a semantic reference, not a production transport or persistence layer.
Its purpose is to make Core behavior executable and deterministic.
"""

from dataclasses import dataclass, field
from typing import Any

STATUSES = {"PENDING", "IN_PROGRESS", "BLOCKED", "COMPLETED", "FAILED", "CANCELLED"}
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}

VALID_TRANSITIONS = {
    "PENDING": {"IN_PROGRESS", "BLOCKED", "CANCELLED"},
    "IN_PROGRESS": {"BLOCKED", "COMPLETED", "FAILED", "CANCELLED"},
    "BLOCKED": {"PENDING", "IN_PROGRESS", "CANCELLED"},
    "COMPLETED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}


@dataclass
class Task:
    task_id: str
    status: str = "PENDING"
    state_version: int = 1
    result: Any = None
    publication_status: str = "PENDING"


@dataclass
class CommandRecord:
    message_id: str
    status: str = "accepted"
    side_effect_count: int = 0


@dataclass
class ReferenceCore:
    tasks: dict[str, Task] = field(default_factory=dict)
    messages: dict[str, CommandRecord] = field(default_factory=dict)
    side_effects: dict[str, int] = field(default_factory=dict)
    remote_artifacts: set[str] = field(default_factory=set)

    def new_task(self, task_id: str, status: str = "PENDING") -> str:
        if status not in STATUSES:
            raise ValueError("invalid status")
        self.tasks[task_id] = Task(task_id=task_id, status=status)
        return task_id

    def command(self, message_id: str, task_id: str, sequence: int = 1, unordered: bool = False) -> dict:
        return {
            "protocol": "AACP",
            "version": "1.0",
            "message_id": message_id,
            "task_id": task_id,
            "conversation_id": "C-test",
            "sender": "agent-a",
            "recipient": "agent-b",
            "sequence": sequence,
            "type": "command",
            "created_at": "2026-01-01T00:00:00Z",
            "payload": {"unordered": unordered},
        }

    def deliver(self, message: dict) -> dict:
        mid = message["message_id"]
        if mid in self.messages:
            return {"ok": True, "status": "duplicate"}
        self.messages[mid] = CommandRecord(message_id=mid)
        task = self.tasks[message["task_id"]]
        key = task.task_id
        self.side_effects[key] = self.side_effects.get(key, 0) + 1
        self.messages[mid].side_effect_count = 1
        return {"ok": True, "status": "received"}

    def side_effect_count(self, key: str) -> int:
        return self.side_effects.get(key, 0)

    def state(self, task_id: str) -> Task:
        return self.tasks[task_id]

    def mutate(self, task_id: str, expected_version: int) -> dict:
        task = self.tasks[task_id]
        if expected_version != task.state_version:
            return {"ok": False, "error_code": "STATE_CONFLICT"}
        task.state_version += 1
        return {"ok": True}

    def transition(self, task_id: str, status: str, expected_version: int | None = None) -> dict:
        task = self.tasks[task_id]
        if status not in VALID_TRANSITIONS[task.status]:
            return {"ok": False, "error_code": "INVALID_STATE_TRANSITION"}
        if expected_version is not None and expected_version != task.state_version:
            return {"ok": False, "error_code": "STATE_CONFLICT"}
        task.status = status
        task.state_version += 1
        return {"ok": True}

    def complete(self, task_id: str, expected_version: int) -> dict:
        return self.transition(task_id, "COMPLETED", expected_version)

    def cancel(self, task_id: str, expected_version: int) -> dict:
        return self.transition(task_id, "CANCELLED", expected_version)

    def publish(self, task_id: str, artifact_id: str) -> None:
        self.remote_artifacts.add(artifact_id)
        self.tasks[task_id].publication_status = "PUBLISHED"

    def restart(self) -> None:
        # In-memory reference has no process boundary; production adapters
        # must persist/reload equivalent state.
        for task in self.tasks.values():
            if task.publication_status == "PENDING" and task.result is not None:
                task.publication_status = "PENDING"

    def remote_artifact(self, artifact_id: str) -> bool:
        return artifact_id in self.remote_artifacts
