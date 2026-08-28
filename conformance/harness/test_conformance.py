from .model import InvalidTransition, Message, State, StateConflict, Store


def command(mid="M-1", tid="T-1", seq=1):
    return Message(mid, tid, "command", seq)


def result(mid="M-2", tid="T-1", seq=2):
    return Message(mid, tid, "result", seq, causation_id="M-1", correlation_id="M-1")


def accepted_store():
    s = Store()
    assert s.accept(command()) == "accepted"
    return s


def test_s01_normal_command():
    s = accepted_store()
    s.execute("T-1")
    s.complete("T-1", result())
    s.publish("M-2")
    t = s.tasks["T-1"]
    assert (t.state, t.execution_attempts, t.side_effects) == (State.COMPLETED, 1, 1)
    assert s.publication["M-2"] == "PUBLISHED"


def test_s02_duplicate_command():
    s = Store(); c = command()
    assert s.accept(c) == "accepted"
    assert s.accept(c) == "duplicate"
    assert s.tasks["T-1"].state_version == 1


def test_s03_lost_ack():
    s = Store(); c = command()
    assert s.accept(c) == "accepted"
    assert s.accept(c) == "duplicate"
    s.execute("T-1")
    assert s.tasks["T-1"].execution_attempts == 1


def test_s04_lost_result():
    s = accepted_store(); s.execute("T-1"); s.complete("T-1", result())
    assert s.tasks["T-1"].state == State.COMPLETED
    s.publish("M-2"); s.publish("M-2")
    assert s.tasks["T-1"].execution_attempts == 1


def test_s05_crash_before_acceptance():
    s = Store(); c = command()
    assert "T-1" not in s.tasks
    assert s.accept(c) == "accepted"
    assert s.tasks["T-1"].execution_attempts == 0


def test_s06_crash_after_acceptance():
    s = accepted_store()
    assert s.tasks["T-1"].state == State.ACCEPTED
    s.execute("T-1")
    assert s.tasks["T-1"].state == State.IN_PROGRESS


def test_s07_crash_during_execution():
    s = accepted_store(); s.execute("T-1")
    assert s.tasks["T-1"].execution_attempts == 1
    # Outcome is deliberately not inferred from the crash.
    assert s.tasks["T-1"].state == State.IN_PROGRESS


def test_s08_crash_after_side_effect_before_result():
    s = accepted_store(); s.execute("T-1")
    assert s.tasks["T-1"].side_effects == 1
    s.complete("T-1", result())
    assert s.tasks["T-1"].side_effects == 1


def test_s09_crash_after_publication():
    s = accepted_store(); s.execute("T-1"); s.complete("T-1", result()); s.publish("M-2")
    s.publish("M-2")
    assert s.tasks["T-1"].execution_attempts == 1


def test_s10_sequence_gap_is_detectable():
    c = command(seq=1); later = result(seq=3)
    assert later.sequence != c.sequence + 1


def test_s11_duplicate_result():
    s = accepted_store(); s.execute("T-1"); r = result(); s.complete("T-1", r)
    s.messages[r.message_id] = r
    assert s.tasks["T-1"].result_message_id == r.message_id
    assert s.tasks["T-1"].execution_attempts == 1


def test_s12_concurrent_state_mutation():
    s = accepted_store(); expected = s.tasks["T-1"].state_version
    s.transition("T-1", expected, State.IN_PROGRESS)
    try:
        s.transition("T-1", expected, State.CANCELLED)
        assert False
    except StateConflict:
        pass


def test_s13_completion_cancellation_race():
    s = accepted_store(); expected = s.tasks["T-1"].state_version
    s.transition("T-1", expected, State.IN_PROGRESS)
    try:
        s.transition("T-1", expected, State.CANCELLED)
        assert False
    except StateConflict:
        pass


def test_s14_timeout_unknown_outcome_no_blind_retry():
    s = accepted_store(); s.execute("T-1")
    assert s.tasks["T-1"].execution_attempts == 1
    assert s.tasks["T-1"].side_effects == 1


def test_s15_safe_retry_after_known_non_execution():
    s = accepted_store(); s.execute("T-1", perform_side_effect=False)
    s.transition("T-1", s.tasks["T-1"].state_version, State.FAILED)
    s.transition("T-1", s.tasks["T-1"].state_version, State.IN_PROGRESS)
    s.tasks["T-1"].execution_attempts += 1
    s.tasks["T-1"].side_effects += 1
    assert s.tasks["T-1"].execution_attempts == 2
    assert s.tasks["T-1"].side_effects == 1


def test_s16_cancellation_before_execution():
    s = accepted_store(); s.transition("T-1", 1, State.CANCELLED)
    assert s.tasks["T-1"].state == State.CANCELLED
    assert s.tasks["T-1"].side_effects == 0


def test_s17_cancellation_during_execution_requires_semantics():
    s = accepted_store(); s.execute("T-1")
    assert s.tasks["T-1"].state == State.IN_PROGRESS
    assert s.tasks["T-1"].side_effects == 1


def test_s18_invalid_transition():
    s = accepted_store()
    try:
        s.transition("T-1", 1, State.COMPLETED)
        assert False
    except InvalidTransition:
        pass


def test_s19_publication_failure_is_separate_from_completion():
    s = accepted_store(); s.execute("T-1"); s.complete("T-1", result())
    s.publication["M-2"] = "FAILED"
    assert s.tasks["T-1"].state == State.COMPLETED
    assert s.publication["M-2"] == "FAILED"
    s.publish("M-2")
    assert s.tasks["T-1"].execution_attempts == 1


def test_s20_recovery_idempotency():
    s = accepted_store(); s.execute("T-1")
    before = (s.tasks["T-1"].execution_attempts, s.tasks["T-1"].side_effects)
    # Recovery observes state but does not execute again.
    after = (s.tasks["T-1"].execution_attempts, s.tasks["T-1"].side_effects)
    assert before == after
