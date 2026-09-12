"""Candidate sequence allocation from published envelopes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def sequences_from_messages(messages: Iterable[dict[str, Any]]) -> list[int]:
    values: list[int] = []
    for message in messages:
        if "sequence" not in message:
            raise ValueError("published message missing sequence")
        values.append(int(message["sequence"]))
    return values


def candidate_sequence(messages: Iterable[dict[str, Any]]) -> int:
    """Next candidate = max(sequence)+1. Gaps remain; filenames are not authority."""
    values = sequences_from_messages(messages)
    return (max(values) if values else 0) + 1


def semantic_fingerprint(message: dict[str, Any]) -> dict[str, Any]:
    """Compare logical message content ignoring publisher-owned sequence."""
    ignored = {"sequence"}
    return {key: value for key, value in message.items() if key not in ignored}
