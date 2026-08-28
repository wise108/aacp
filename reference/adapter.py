"""Adapter exposing the reference Core model to the conformance harness."""

from __future__ import annotations

from .aacp_core import ReferenceCore


class ReferenceAdapter:
    def __init__(self) -> None:
        self.core = ReferenceCore()
        self._counter = 0

    def reset(self) -> None:
        self.core = ReferenceCore()
        self._counter = 0

    def new_task(self, *, status: str = "PENDING", unordered: bool = False) -> str:
        self._counter += 1
        task_id = f"T-ref-{self._counter}"
        self.core.new_task(task_id, status=status)
        return task_id

    def command(self, task_id: str, *, message_id: str, sequence: int) -> dict:
        return self.core.command(message_id, task_id, sequence)

    def deliver(self, message: dict):
        return _Response(self.core.deliver(message))

    def deliver_without_returning_ack(self, message: dict) -> None:
        self.core.deliver(message)

    def restart(self) -> None:
        self.core.restart()

    def state(self, task_id: str):
        return self.core.state(task_id)

    def side_effect_count(self, key: str) -> int:
        return self.core.side_effect_count(key)

    def mutate(self, task_id: str, *, expected_version: int):
        return _Response(self.core.mutate(task_id, expected_version))

    def transition(self, task_id: str, status: str, *, expected_version: int | None = None):
        return _Response(self.core.transition(task_id, status, expected_version))

    def complete(self, task_id: str, *, expected_version: int):
        return _Response(self.core.complete(task_id, expected_version))

    def cancel(self, task_id: str, *, expected_version: int):
        return _Response(self.core.cancel(task_id, expected_version))

    def complete_task_and_push_then_crash(self) -> str:
        task_id = self.new_task()
        version = self.state(task_id).state_version
        self.complete(task_id, expected_version=version)
        artifact = f"artifact-{task_id}"
        self.core.publish(task_id, artifact)
        return task_id

    def remote_artifact(self, artifact_id: str) -> bool:
        return self.core.remote_artifact(artifact_id)


class _Response:
    def __init__(self, data: dict):
        self.__dict__.update(data)
