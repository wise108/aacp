# AACP Errors 1.0

Every protocol error MUST provide a stable `code`, human-readable `message`, `retryable` boolean, and optional structured `details`.

Core codes include `INVALID_MESSAGE`, `UNSUPPORTED_VERSION`, `UNKNOWN_TASK`, `INVALID_STATE_TRANSITION`, `STATE_CONFLICT`, `SEQUENCE_GAP`, `DUPLICATE_MESSAGE`, `NOT_AUTHORIZED`, `TASK_BLOCKED`, `TASK_FAILED`, `TASK_CANCELLED`, `PUBLICATION_FAILED`, `TRANSPORT_UNAVAILABLE`, and `INTERNAL_ERROR`.

Implementations MAY define namespaced extension codes without changing Core semantics.

See [SPEC.md](../../SPEC.md) for the authoritative normative requirements.