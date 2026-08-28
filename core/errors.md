# AACP Errors 1.0

Every protocol error MUST provide:

```yaml
error:
  code: STATE_CONFLICT
  message: "Task state changed since it was read."
  retryable: true
  details: {}
```

## Core error registry

| Code | Retryable | Meaning |
|---|---:|---|
| `INVALID_MESSAGE` | no | Message is malformed or violates schema |
| `UNSUPPORTED_VERSION` | no | Protocol version is unsupported |
| `UNKNOWN_TASK` | no | Referenced task does not exist |
| `INVALID_STATE_TRANSITION` | no | Requested lifecycle transition is invalid |
| `STATE_CONFLICT` | yes | Optimistic version check failed |
| `SEQUENCE_GAP` | yes | Expected sequence has not arrived |
| `DUPLICATE_MESSAGE` | yes | Message was already processed; normally handled idempotently |
| `NOT_AUTHORIZED` | no | Sender is not permitted |
| `TASK_BLOCKED` | no | Task cannot currently execute |
| `TASK_FAILED` | depends | Execution failed |
| `TASK_CANCELLED` | no | Task was cancelled |
| `PUBLICATION_FAILED` | yes | Result publication failed |
| `TRANSPORT_UNAVAILABLE` | yes | Transport is temporarily unavailable |
| `INTERNAL_ERROR` | depends | Unexpected implementation failure |

Implementations MAY define extension codes without changing Core semantics.
