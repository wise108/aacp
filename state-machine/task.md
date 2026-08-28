# AACP Task State Machine 1.0

## States

```text
PENDING
IN_PROGRESS
BLOCKED
COMPLETED
FAILED
CANCELLED
```

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

An implementation MUST reject transitions not listed above. Recovery/retry operations MAY introduce an explicit implementation-defined transition mechanism, but MUST preserve the meaning of terminal states and MUST NOT silently mutate history.

Every accepted transition MUST increment `state_version` exactly once.

## Claim

Claiming a `PENDING` task changes it to `IN_PROGRESS` and assigns an owner. The mutation MUST use optimistic concurrency. If another worker claims it first, the later claim MUST fail with `STATE_CONFLICT` rather than overwrite the owner.

## Heartbeat

Long-running tasks SHOULD update `heartbeat_at`. A stale heartbeat indicates a recovery candidate; it does not itself constitute a state transition.
