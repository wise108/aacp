# AACP 1.0 Conformance Checklist

An implementation is **AACP 1.0 CONFORMANT** only when every mandatory item below is verified by executable tests or an equivalent auditable test record.

## Identity and envelope

- [ ] Uses AACP protocol/version declaration.
- [ ] Every logical message has a unique immutable `message_id`.
- [ ] Every message is bound to `conversation_id` and `task_id`.
- [ ] Sender and recipient are explicit.
- [ ] Ordered streams use a monotonic sequence starting at 1.
- [ ] Message type and required payload fields are schema-valid.

## Delivery semantics

- [ ] Duplicate delivery is detected by message identity.
- [ ] Duplicate delivery does not repeat a non-idempotent side effect.
- [ ] Retries reuse the original logical `message_id`.
- [ ] Lost ACK does not cause duplicate execution.
- [ ] Ordered streams detect sequence gaps.
- [ ] Unordered streams do not incorrectly block on unrelated sequence gaps.

## State and concurrency

- [ ] Task transitions are validated against the AACP state machine.
- [ ] Mutable state carries `state_version`.
- [ ] Stale writes produce `STATE_CONFLICT`.
- [ ] Concurrent completion/cancellation cannot silently overwrite a newer state.
- [ ] Completion is derived from authoritative task state and required result semantics, not transport success.

## Results and errors

- [ ] Required tasks produce an independently identifiable result.
- [ ] Result publication is retry-safe.
- [ ] Protocol errors have stable machine-readable categories.
- [ ] Transport diagnostics do not redefine logical protocol error codes.

## Recovery

- [ ] Restart reconstructs pending work from durable state.
- [ ] Remote artifacts are reconciled before retrying execution.
- [ ] Crash after remote publication does not cause duplicate execution.
- [ ] Crash before publication permits safe retry.
- [ ] Recovery detects malformed or conflicting artifacts.

## Transport

- [ ] A transport profile is explicitly selected.
- [ ] Message publication is deterministic and idempotent.
- [ ] Transport metadata is not used as logical message identity.
- [ ] Transport outages are retryable where specified.
- [ ] The transport cannot silently overwrite an immutable message.

## Adoption and cutover

- [ ] Existing IPC was inventoried before migration.
- [ ] Legacy IPC was frozen before destructive migration steps.
- [ ] Existing pending/in-flight work was migrated with provenance.
- [ ] Migration was verified for zero loss and duplicate safety.
- [ ] AACP cutover was recorded.
- [ ] Obsolete IPC was removed only after successful verification.
- [ ] No parallel project-specific inter-agent protocol remains after cutover.

## Final gate

```text
AACP 1.0 CONFORMANCE
--------------------
Envelope       [ ]
Delivery       [ ]
State          [ ]
Results        [ ]
Errors         [ ]
Recovery       [ ]
Transport     [ ]
Adoption       [ ]

RESULT: NOT CONFORMANT
```

The final result MUST NOT be changed to `CONFORMANT` until all mandatory boxes are verified.
