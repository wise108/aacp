# AACP Core 1.0 — Implementation Ambiguity Review

This review asks whether two independent implementations can derive materially different behavior from the Core specification.

## Findings and resolutions

### 1. ACK boundary

**Risk:** implementations could acknowledge a command before its processing state is durable.

**Resolution:** `ack:received` is explicitly defined as durable acceptance. A crash-safe implementation must persist sufficient processing state before the ACK, unless the command side effect is independently idempotent.

### 2. Execution boundary

**Risk:** implementations could disagree about whether an operation that started but crashed is considered executed.

**Resolution:** Core does not define an atomic boundary around arbitrary external side effects. If execution may have happened without durable processing state, recovery MUST treat it as potentially executed and reconcile idempotently rather than blindly rerun.

### 3. Retransmission sequence

**Risk:** a retry could accidentally become a new message.

**Resolution:** retransmission reuses the original `message_id` and sequence and consumes no new sequence number.

### 4. Sequence scope

**Risk:** implementations could maintain one global counter or one counter per task.

**Resolution:** ordered stream identity is exactly `(conversation_id, sender, recipient)`.

### 5. Timestamp format

**Risk:** incompatible timestamp parsing.

**Resolution:** `created_at` is RFC 3339 UTC and malformed timestamps are rejected.

### 6. Completion versus publication

**Risk:** implementations could equate task completion with remote availability.

**Resolution:** Task completion and Result publication are independent state facts. Publication recovery never re-executes the task.

### 7. Completion versus cancellation

**Risk:** race resolution could depend on wall-clock time or message arrival order.

**Resolution:** state_version/CAS decides. The first successful state mutation wins; a stale concurrent mutation fails with `STATE_CONFLICT`.

### 8. Version increments

**Risk:** implementations could increment versions by arbitrary amounts or only on some transitions.

**Resolution:** each accepted task state mutation advances `state_version` exactly `N → N+1`.

### 9. Ordered versus unordered streams

**Risk:** implementations could disagree whether sequence gaps always block processing.

**Resolution:** strict ordering is the default reliability interpretation for ordered streams; unordered behavior is allowed only when explicitly declared by the implementation/profile.

### 10. Exactly-once terminology

**Risk:** implementations could interpret AACP as guaranteeing exactly-once delivery.

**Resolution:** AACP explicitly provides at-least-once delivery. Effectively-once execution is an implementation property achieved through idempotency, not a network-delivery guarantee.

## Review conclusion

No unresolved ambiguity has been identified that requires adding a new Core mechanism. Remaining implementation choices are intentionally delegated to transport profiles or implementations and MUST NOT alter Core semantics.

**Gate result: PASS for AACP Core 1.0-rc1.**
