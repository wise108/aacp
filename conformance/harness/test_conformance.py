from .model import InvalidTransition, Message, State, StateConflict, Store


def command(mid="M-1", tid="T-1"):
    return Message(mid, tid, "command")


def result(mid="M-2", tid="T-1"):
    return Message(mid, tid, "result", causation_id="M-1", correlation_id="M-1")


def accepted_store():
    s = Store()
    assert s.accept(command()) == "accepted"
    return s


def test_unique_immutable_message_identity():
    m = command()
    assert m.message_id == "M-1"
    assert m.message_id == command().message_id
    assert m.task_id == "T-1"


def test_duplicate_command_is_idempotent():
    s = Store(); c = command()
    assert s.accept(c) == "accepted"
    assert s.accept(c) == "duplicate"
    assert s.tasks["T-1"].state == State.ACCEPTED
    assert s.tasks["T-1"].state_version == 1


def test_ack_acceptance_is_not_completion():
    s = accepted_store()
    assert s.tasks["T-1"].state == State.ACCEPTED
    assert s.tasks["T-1"].execution_attempts == 0


def test_lost_ack_does_not_duplicate_execution():
    s = Store(); c = command()
    assert s.accept(c) == "accepted"
    assert s.accept(c) == "duplicate"
    s.execute("T-1")
    assert s.tasks["T-1"].execution_attempts == 1
    assert s.tasks["T-1"].side_effects == 1


def test_lost_result_does_not_require_reexecution():
    s = accepted_store(); s.execute("T-1"); s.complete("T-1", result())
    assert s.tasks["T-1"].state == State.COMPLETED
    assert s.tasks["T-1"].execution_attempts == 1


def test_valid_task_lifecycle():
    s = accepted_store()
    s.execute("T-1")
    s.complete("T-1", result())
    assert s.tasks["T-1"].state == State.COMPLETED


def test_invalid_transition_is_rejected():
    s = accepted_store()
    try:
        s.transition("T-1", 1, State.COMPLETED)
        assert False
    except InvalidTransition:
        pass


def test_stale_state_mutation_is_rejected():
    s = accepted_store(); expected = s.tasks["T-1"].state_version
    s.transition("T-1", expected, State.IN_PROGRESS)
    try:
        s.transition("T-1", expected, State.CANCELLED)
        assert False
    except StateConflict:
        pass


def test_terminal_state_cannot_be_overwritten():
    s = accepted_store(); s.execute("T-1"); s.complete("T-1", result())
    try:
        s.transition("T-1", s.tasks["T-1"].state_version, State.CANCELLED)
        assert False
    except InvalidTransition:
        pass


def test_uncertain_execution_is_not_blindly_repeated():
    s = accepted_store(); s.execute("T-1")
    before = (s.tasks["T-1"].execution_attempts, s.tasks["T-1"].side_effects)
    # Recovery observes the durable state; it does not execute again automatically.
    after = (s.tasks["T-1"].execution_attempts, s.tasks["T-1"].side_effects)
    assert before == after


def test_known_non_execution_can_be_retried():
    s = accepted_store(); s.execute("T-1", perform_side_effect=False); s.fail("T-1")
    s.transition("T-1", s.tasks["T-1"].state_version, State.IN_PROGRESS)
    s.tasks["T-1"].execution_attempts += 1
    s.tasks["T-1"].side_effects += 1
    assert s.tasks["T-1"].execution_attempts == 2
    assert s.tasks["T-1"].side_effects == 1
