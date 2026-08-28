# AACP 1.0 Task State Machine

This document is a detailed explanation of the task lifecycle defined by AACP Core 1.0. The normative source is `docs/02-core/specification.md`.

## States

- `PENDING` — task exists but has not been accepted.
- `ACCEPTED` — command has been accepted for processing.
- `IN_PROGRESS` — execution has started.
- `BLOCKED` — execution cannot continue until an explicit condition is resolved.
- `COMPLETED` — successful terminal state.
- `FAILED` — unsuccessful terminal state.
- `CANCELLED` — cancellation terminal state.

## Valid transitions

```text
PENDING ── accept ──► ACCEPTED
PENDING ── cancel ──► CANCELLED

ACCEPTED ── start ──► IN_PROGRESS
ACCEPTED ── cancel ──► CANCELLED

IN_PROGRESS ── success ──► COMPLETED
IN_PROGRESS ── failure ──► FAILED
IN_PROGRESS ── cancel ──► CANCELLED
IN_PROGRESS ── blocker ──► BLOCKED

BLOCKED ── resolve ──► IN_PROGRESS
BLOCKED ── cancel ──► CANCELLED

FAILED ── explicit retry ──► IN_PROGRESS
```

`COMPLETED` and `CANCELLED` are terminal. `FAILED` is terminal unless an explicit retry policy exists.

## ACK boundary

A successful `accepted` ACK establishes the `PENDING → ACCEPTED` boundary. ACK does not mean completion.

A duplicate command returns duplicate acknowledgement semantics and does not create another logical execution.

## Retry

There are two different concepts:

1. **Message retry** — retransmission of the same message. It keeps the same `message_id` and does not create a new task.
2. **Execution retry** — a new execution attempt permitted by an explicit task retry policy. It keeps the same logical `task_id` but must not repeat an uncertain side effect without reconciliation.

## Timeout and crash

Timeout is not a Core task state. If execution outcome is uncertain, the agent must reconcile before retrying. A missing ACK or result is not evidence that execution did not happen.

After restart, the implementation must reconstruct enough durable state to avoid blindly repeating uncertain work.

## Concurrency

Mutable state changes should use `state_version` compare-and-set semantics. A stale mutation must fail with `STATE_CONFLICT` instead of overwriting newer state.

## Invariants

- terminal state cannot be silently overwritten;
- ACK never means completion;
- duplicate command never means second execution;
- lost result never implies lost execution;
- transport success never implies task completion;
- uncertain execution is reconciled before retry;
- recovery is idempotent.
