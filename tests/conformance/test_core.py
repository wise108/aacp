"""Transport-neutral AACP Core 1.0 conformance test skeleton.

The tests intentionally target an adapter contract instead of a concrete
implementation. A project integrating AACP supplies an adapter fixture.
"""

import pytest


@pytest.fixture
def aacp():
    """Return a project-supplied AACP adapter.

    Integrations should override this fixture from their adapter module.
    """
    pytest.skip("AACP implementation adapter is not installed")


def test_c01_duplicate_delivery(aacp):
    task_id = aacp.new_task()
    command = aacp.command(task_id, message_id="M-c01", sequence=1)
    aacp.deliver(command)
    aacp.deliver(command)
    assert aacp.side_effect_count(task_id) == 1


def test_c02_sequence_gap(aacp):
    task_id = aacp.new_task()
    aacp.deliver(aacp.command(task_id, message_id="M-c02-1", sequence=1))
    response = aacp.deliver(aacp.command(task_id, message_id="M-c02-3", sequence=3))
    assert response.error_code == "SEQUENCE_GAP"


def test_c03_state_conflict(aacp):
    task_id = aacp.new_task()
    version = aacp.state(task_id).state_version
    first = aacp.mutate(task_id, expected_version=version)
    second = aacp.mutate(task_id, expected_version=version)
    assert first.ok
    assert second.error_code == "STATE_CONFLICT"


def test_c05_crash_after_remote_push(aacp):
    task_id = aacp.complete_task_and_push_then_crash()
    aacp.restart()
    state = aacp.state(task_id)
    assert state.publication_status == "PUBLISHED"
    assert aacp.side_effect_count(task_id) == 1


def test_c06_lost_ack(aacp):
    task_id = aacp.new_task()
    command = aacp.command(task_id, message_id="M-c06", sequence=1)
    aacp.deliver_without_returning_ack(command)
    aacp.deliver(command)
    assert aacp.side_effect_count(task_id) == 1


def test_c08_invalid_transition(aacp):
    task_id = aacp.new_task(status="COMPLETED")
    response = aacp.transition(task_id, "IN_PROGRESS")
    assert response.error_code == "INVALID_STATE_TRANSITION"
    assert aacp.state(task_id).status == "COMPLETED"


def test_c11_cancel_race(aacp):
    task_id = aacp.new_task()
    version = aacp.state(task_id).state_version
    completion = aacp.complete(task_id, expected_version=version)
    cancellation = aacp.cancel(task_id, expected_version=version)
    assert completion.ok
    assert cancellation.error_code == "STATE_CONFLICT"


def test_c13_version_increment(aacp):
    task_id = aacp.new_task()
    before = aacp.state(task_id).state_version
    aacp.mutate(task_id, expected_version=before)
    after = aacp.state(task_id).state_version
    assert after == before + 1


def test_c14_unordered_stream(aacp):
    task_id = aacp.new_task(unordered=True)
    first = aacp.command(task_id, message_id="M-c14-1", sequence=1)
    second = aacp.command(task_id, message_id="M-c14-2", sequence=2)
    aacp.deliver(second)
    response = aacp.deliver(first)
    assert response.ok
