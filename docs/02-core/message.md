# AACP Message 1.0

Messages are carried in the AACP Envelope. Core types are `command`, `ack`, `result`, `error`, `cancel`, and `event`.

`message_id` is the idempotency key. Receivers MUST prevent duplicate command execution.

Ordered streams use monotonic sequence numbers. Under strict ordering, a sequence gap MUST be detected and MUST NOT be silently ignored.

Typical flow:

```text
COMMAND → ACK(received) → RESULT
```

See [SPEC.md](../../SPEC.md) for the authoritative normative requirements.