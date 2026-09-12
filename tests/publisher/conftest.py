"""Shared fixtures for Publication Layer tests."""

from __future__ import annotations

from typing import Any

from aacp.publisher import TargetBinding


TARGET = TargetBinding(
    target_ref="refs/heads/test",
    conversation_id="C-test",
    stream_id="S-test",
)


def envelope(
    message_id: str,
    *,
    sequence: int | None = None,
    payload: dict[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "protocol": "AACP",
        "version": "1.0",
        "message_id": message_id,
        "conversation_id": "C-test",
        "task_id": "T-test",
        "type": "event",
        "sender": "chatgpt",
        "recipient": "cursor",
        "created_at": "2026-09-12T00:00:00Z",
        "stream_id": "S-test",
        "payload": payload if payload is not None else {"n": message_id},
    }
    data.update(overrides)
    if sequence is not None:
        data["sequence"] = sequence
    return data
