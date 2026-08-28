# AACP Task State Machine 1.0

## States

`PENDING`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `FAILED`, `CANCELLED`.

## Valid transitions

```text
PENDING      → IN_PROGRESS
PENDING      → CANCELLED
IN_PROGRESS  → BLOCKED
IN_PROGRESS  → COMPLETED
IN_PROGRESS  → FAILED
IN_PROGRESS  → CANCELLED
BLOCKED      → IN_PROGRESS
BLOCKED      → CANCELLED
```

Terminal states are `COMPLETED`, `FAILED`, and `CANCELLED`.

Implementations MUST reject transitions not listed above. Every accepted transition MUST increment `state_version` exactly once.

Claiming a `PENDING` task changes it to `IN_PROGRESS` and assigns an owner using optimistic concurrency. A stale claim MUST fail with `STATE_CONFLICT`.

Long-running tasks SHOULD update `heartbeat_at`. A stale heartbeat is a recovery condition, not a Task state.
