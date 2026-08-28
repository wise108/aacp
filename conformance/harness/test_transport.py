import pytest

from .model import Message
from .transport import CrashInjected, DeterministicTransport, Fault, FaultKind


def msg(mid="M-1"):
    return Message(mid, "T-1", "command")


def test_drop_is_deterministic():
    t = DeterministicTransport([Fault("SEND_BEFORE", FaultKind.DROP, "M-1")])
    t.send(msg())
    assert t.receive() is None


def test_duplicate_preserves_identity():
    t = DeterministicTransport([Fault("SEND_AFTER", FaultKind.DUPLICATE, "M-1")])
    t.send(msg())
    assert [t.receive().message_id, t.receive().message_id] == ["M-1", "M-1"]


def test_crash_point_is_reproducible():
    t = DeterministicTransport([Fault("SEND_AFTER", FaultKind.CRASH, "M-1")])
    with pytest.raises(CrashInjected):
        t.send(msg())
    assert t.receive().message_id == "M-1"


def test_receive_drop_does_not_change_message_identity():
    t = DeterministicTransport([Fault("RECEIVE_BEFORE", FaultKind.DROP, "M-1")])
    t.send(msg())
    assert t.receive() is None
