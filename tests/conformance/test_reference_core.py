from reference.adapter import ReferenceAdapter


def test_c01_duplicate_delivery():
    a = ReferenceAdapter(); t = a.new_task(); m = a.command(t, message_id="M-1", sequence=1)
    assert a.deliver(m).status == "received"
    assert a.deliver(m).status == "duplicate"
    assert a.side_effect_count(t) == 1


def test_c03_state_conflict():
    a = ReferenceAdapter(); t = a.new_task(); v = a.state(t).state_version
    assert a.mutate(t, expected_version=v).ok
    assert a.mutate(t, expected_version=v).error_code == "STATE_CONFLICT"


def test_c08_invalid_transition():
    a = ReferenceAdapter(); t = a.new_task(status="COMPLETED")
    assert a.transition(t, "IN_PROGRESS").error_code == "INVALID_STATE_TRANSITION"


def test_c11_cancel_race():
    a = ReferenceAdapter(); t = a.new_task(); v = a.state(t).state_version
    assert a.complete(t, expected_version=v).ok
    assert a.cancel(t, expected_version=v).error_code == "STATE_CONFLICT"


def test_c13_version_increment():
    a = ReferenceAdapter(); t = a.new_task(); v = a.state(t).state_version
    assert a.mutate(t, expected_version=v).ok
    assert a.state(t).state_version == v + 1
