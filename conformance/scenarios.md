# AACP 1.0 Conformance Scenarios

An implementation claiming Core 1.0 compatibility MUST handle the following scenarios.

## C-01 — Duplicate delivery

Deliver the same command twice with the same `message_id`.

Expected: the command executes at most once; the second delivery returns the prior processing outcome or an equivalent idempotent acknowledgement.

## C-02 — Sequence gap

Deliver sequence N+1 before N on a strict ordered stream.

Expected: `SEQUENCE_GAP`; N+1 is not silently processed.

## C-03 — State conflict

Have two workers mutate the same task using the same expected `state_version`.

Expected: exactly one mutation succeeds; the other receives `STATE_CONFLICT` and does not overwrite state.

## C-04 — Crash before publication

Complete a task and create a result, then interrupt the agent before transport publication.

Expected after recovery: task remains completed, result remains available locally, publication is retried; task is not re-executed.

## C-05 — Crash after remote push

Push a result, then interrupt the agent before it records/announces publication completion.

Expected after recovery: verify the remote ref/commit and mark publication `PUBLISHED` without re-executing the task.

## C-06 — Lost ACK

Drop an ACK and retransmit the original command.

Expected: duplicate delivery does not execute the command twice.

## C-07 — Worker crash during execution

Leave a task `IN_PROGRESS`, stop the worker, and let heartbeat become stale.

Expected: recovery detects the stale task and can safely recover/reassign it according to implementation policy.

## C-08 — Invalid transition

Attempt a transition not allowed by the state machine.

Expected: `INVALID_STATE_TRANSITION`; stored state remains unchanged.

## C-09 — Transport outage

Make the transport unavailable after local task completion.

Expected: task remains `COMPLETED`, publication becomes/remains `PENDING` or `FAILED`; retry occurs when transport recovers.

## C-10 — Restart recovery

Restart an agent with pending messages, unacknowledged messages, in-progress tasks and unpublished results.

Expected: durable state is reconstructed and work is resumed/reconciled without duplicate execution.

## C-11 — Cancel race

Issue cancellation concurrently with completion.

Expected: optimistic concurrency determines one valid outcome; the loser observes `STATE_CONFLICT` and does not silently overwrite terminal state.

## C-12 — False completion claim

An agent reports “done/pushed” without a verifiable publication record.

Expected: prose is not treated as protocol evidence; publication remains unverified until the transport confirms it.
