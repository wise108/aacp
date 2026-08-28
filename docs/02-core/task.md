# AACP Task 1.0

A Task is the durable unit of work coordinated between agents.

Core statuses are `PENDING`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `FAILED`, and `CANCELLED`. `STALE` is a recovery condition, not a Task status.

A Task has `task_id`, `conversation_id`, `created_by`, `status`, `state_version`, `created_at`, and `updated_at`. `assigned_to`, `heartbeat_at`, and `command_message_id` are lifecycle-dependent fields.

## Cancellation

Cancellation is a state mutation and MUST use optimistic concurrency with the current `state_version`.

If a cancellation request is based on version N and another valid mutation changes the task to version N+1 before the cancellation is committed, the cancellation MUST fail with `STATE_CONFLICT`. It MUST NOT overwrite the newer state.

If a task is already terminal (`COMPLETED`, `FAILED`, or `CANCELLED`), a cancellation request MUST NOT change its state. The implementation SHOULD return the current terminal state as the authoritative outcome.

This creates a deterministic rule for completion/cancellation races: the first successfully committed state transition wins; a stale concurrent operation loses with `STATE_CONFLICT`.

## Ownership and recovery

`assigned_to` identifies the current execution owner. An implementation MUST NOT claim a task owned by another active worker without a valid recovery/reassignment operation.

Long-running tasks SHOULD update `heartbeat_at`. A stale heartbeat indicates a recovery candidate; it does not itself constitute a state transition.
