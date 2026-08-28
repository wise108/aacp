# AACP Task State Machine 1.0

## 1. Purpose

This document defines the normative lifecycle of an AACP task and the behavior required for acknowledgement, execution, retry, timeout, cancellation, crash recovery, and concurrent state updates.

## 2. States

### PENDING

The task has been created by a valid command but execution has not been durably accepted.

### ACCEPTED

The command has been durably accepted for processing. A successful ACK establishes this boundary.

### IN_PROGRESS

Execution has begun.

### COMPLETED

The task reached its successful terminal state and its required result was durably recorded. Remote publication of that result is a separate Publication state.

### FAILED

The task reached a terminal unsuccessful state and its required failure result/error was durably recorded.

### CANCELLED

The task was intentionally terminated without successful completion and the cancellation state/result was durably recorded.

### BLOCKED

Execution cannot proceed because an explicit blocking condition exists. BLOCKED is non-terminal and MUST include a recoverable reason.

## 3. Normative transitions

| Current | Event | Next | Notes |
|---|---|---|---|
| PENDING | valid acceptance | ACCEPTED | ACK acceptance boundary |
| ACCEPTED | execution starts | IN_PROGRESS | execution may be immediate |
| ACCEPTED | cancel accepted before start | CANCELLED | no execution side effect |
| IN_PROGRESS | successful completion | COMPLETED | terminal |
| IN_PROGRESS | unrecoverable task failure | FAILED | terminal |
| IN_PROGRESS | cancellation safely accepted | CANCELLED | task-specific semantics apply |
| IN_PROGRESS | explicit blocker | BLOCKED | non-terminal |
| BLOCKED | blocker resolved | IN_PROGRESS | resume/retry semantics apply |
| BLOCKED | cancellation | CANCELLED | terminal |
| FAILED | explicit retry allowed | IN_PROGRESS | same task, new execution attempt |
| PENDING | explicit cancellation | CANCELLED | no execution side effect |

A malformed or rejected command is normally rejected before a Task enters the lifecycle. If a Task has already been created and its command is subsequently determined invalid, its handling MUST be explicitly defined by the command contract; implementations MUST NOT invent an implicit transition.

Terminal states (`COMPLETED`, `FAILED`, `CANCELLED`) MUST NOT transition to another state. A new logical operation requires a new task.

## 4. ACK semantics

ACK establishes acceptance, not completion. An accepted command causes:

`PENDING → ACCEPTED`

A duplicate command MUST return duplicate acknowledgement semantics and MUST NOT repeat logical acceptance or execution.

If the receiver cannot durably accept the command, it MUST NOT emit a successful `accepted` ACK.

## 5. Execution and result boundary

`IN_PROGRESS → COMPLETED` is valid only when the task's success criteria are satisfied and the required result can be durably reconstructed.

`IN_PROGRESS → FAILED` is valid when the failure is terminal under the task contract.

`IN_PROGRESS → CANCELLED` is valid only when cancellation semantics permit the operation to stop safely. Receiving a cancellation request is not proof that an already-running side effect has been undone.

## 6. Retry

A transport retry of an unconfirmed message is a retry of **publication**, not execution. It keeps the original `message_id` and sequence.

A task execution retry after a recoverable failure is a new **attempt** on the same `task_id`. The implementation MUST persist enough attempt information to determine whether a side effect may already have occurred.

A retry MUST NOT be used to bypass terminal state rules. Retry from `FAILED` requires an explicit retry policy and creates a new attempt.

## 7. Timeouts

Timeout is an event, not a task state.

When an execution timeout occurs, the agent MUST determine whether execution may still be running or whether its outcome is known.

If outcome is unknown, the task MUST NOT be blindly retried. It SHOULD enter `BLOCKED` or remain `IN_PROGRESS` with an explicit timeout condition until reconciliation establishes a safe outcome.

Only after the implementation establishes that the prior attempt cannot still produce the side effect may a new attempt transition to `IN_PROGRESS`.

## 8. Crash recovery

### Crash before acceptance

If no durable acceptance exists, the command may be safely retried using the original command `message_id`.

### Crash after acceptance but before execution

Recovery reconstructs `ACCEPTED`. The task may proceed to `IN_PROGRESS`.

### Crash during execution

Recovery MUST treat the execution outcome as potentially unknown. It MUST reconcile durable execution evidence and relevant external side effects before starting another attempt.

### Crash after side effect but before result publication

Recovery MUST NOT repeat the side effect merely because the result is absent. It must reconstruct and publish the result if the outcome can be established.

### Crash after result publication

Recovery recognizes the existing result and MUST NOT create a second logical terminal result for the same execution contract.

## 9. Cancellation

Cancellation is a message and MUST obey identity, ordering, and deduplication rules.

Cancellation of `PENDING` or `ACCEPTED` work can normally transition directly to `CANCELLED`.

Cancellation of `IN_PROGRESS` work requires task-specific cancellation semantics. If the external operation cannot be safely stopped, the task MUST NOT claim `CANCELLED` merely because a cancellation request was received.

## 10. Concurrency and state_version

Every mutable task state carries `state_version`.

A state transition MUST use compare-and-set semantics equivalent to:

```text
UPDATE task
SET state = NEXT, state_version = state_version + 1
WHERE task_id = T
  AND state_version = EXPECTED
```

If zero rows are updated because the expected version is stale, the operation fails with `STATE_CONFLICT`. The agent MUST reload authoritative state and reconcile; it MUST NOT overwrite newer state.

## 11. Duplicate messages

Duplicate commands, ACKs, events, cancellation requests, and results are detected by immutable message identity and relevant correlation/task constraints.

A duplicate command MUST NOT start a second logical execution.

A duplicate cancellation MUST NOT move a terminal task to another state.

A duplicate result with the same message identity is already published/known and MUST NOT create another logical terminal result.

## 12. State invariants

1. Terminal states are immutable.
2. Every state transition is attributable to an AACP message/event or explicitly recorded internal execution event.
3. `state_version` increases exactly once per successful mutable state transition.
4. A stale writer cannot overwrite newer state.
5. ACK never means completion.
6. Transport success never means task completion.
7. Unknown execution outcome is never treated as safe-to-retry without reconciliation.
8. A missing result does not imply missing execution.
9. A duplicate command does not imply a second execution.
10. Recovery is idempotent.
11. Task state and result Publication state are independent.

## 13. Canonical lifecycle

```text
PENDING
   │ accept
   ▼
ACCEPTED
   │ start
   ▼
IN_PROGRESS
   ├── success ──► COMPLETED
   ├── failure ──► FAILED ── retry policy ──► IN_PROGRESS
   ├── cancel ───► CANCELLED
   └── blocker ──► BLOCKED ── resolve ──► IN_PROGRESS

PENDING ── cancel ──► CANCELLED
ACCEPTED ─ cancel ──► CANCELLED
```
