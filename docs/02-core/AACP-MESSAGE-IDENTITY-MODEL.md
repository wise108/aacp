# AACP Message & Identity Model 1.0

## 1. Scope

This document defines identity, causality, correlation, ordering, task binding, retries, acknowledgements, and results for AACP 1.0.

## 2. Objects

AACP distinguishes five concepts:

- **Conversation** — a durable logical context containing one or more streams and tasks.
- **Stream** — an ordered or unordered sequence of messages within a conversation.
- **Task** — the unit of requested work and lifecycle state.
- **Message** — an immutable protocol envelope carrying a command, acknowledgement, result, error, cancellation, or event.
- **Attempt** — an execution/publication attempt. An attempt is not a new logical task or message.

## 3. Identifiers

`conversation_id` identifies the conversation context and remains stable across messages belonging to it.

`task_id` identifies one logical unit of work. A retry of the same execution does not create a new task.

`message_id` identifies one immutable protocol message. Every message, including ACK and RESULT, has its own message ID.

`stream_id` identifies the logical ordering stream inside a conversation. Ordering is scoped to `(conversation_id, stream_id)`.

`correlation_id` identifies the logical exchange to which a message belongs. For a command and its direct lifecycle messages, it SHOULD normally equal the command's `message_id`.

`causation_id` identifies the immediate message that caused the current message. For an ACK, this is the accepted command message ID. For a RESULT, it is the command or the processing message that directly caused the result.

These fields MUST NOT be treated as interchangeable.

## 4. Sequence

`sequence` belongs to a **stream**, not to a task and not to a message lifecycle.

For an ordered stream, each newly created message published into that stream receives exactly one monotonically increasing sequence number. Retransmission of an existing message reuses its original sequence.

A receiver MUST use `(conversation_id, stream_id, sequence)` as the ordering coordinate. `message_id` remains the identity coordinate.

A task MAY span multiple streams. A single stream MAY contain messages for multiple tasks.

For an unordered stream, sequence MUST NOT impose a processing barrier.

## 5. Why sequence is separate from identity

Sequence answers **where a message sits in an ordered stream**.

Message ID answers **which immutable message this is**.

Task ID answers **which unit of work this message concerns**.

Correlation ID answers **which logical exchange this message belongs to**.

Causation ID answers **which prior message directly caused it**.

## 6. Command

A command creates or addresses a task. A command is itself an immutable message. Its `message_id` is the canonical identity of that particular command request.

A task MAY have multiple commands only when the command contract explicitly permits follow-up, resume, or control commands. A retry of the same command MUST reuse the same `message_id` and sequence.

## 7. ACK

An ACK is a new message with a new `message_id` and `causation_id` pointing to the accepted command. Its `correlation_id` points to the command exchange.

ACK statuses are `accepted`, `rejected`, and `duplicate`.

- `accepted` means durable acceptance for processing;
- `rejected` means the command will not be processed;
- `duplicate` means the command was already accepted or processed and MUST NOT execute again.

ACK does not mean execution has completed.

## 8. Result

A RESULT is a new immutable message with a new `message_id`. It references the originating task and exchange through `task_id`, `correlation_id`, and `causation_id`.

A task normally has one terminal result for a given execution contract. Multiple results are permitted only when explicitly defined by the task contract.

A result publication retry MUST reuse the same result message ID and sequence.

## 9. Progress and events

AACP 1.0 represents progress or other non-terminal notifications as `event` messages unless a future extension defines a dedicated message type. Such events SHOULD carry the same `correlation_id` as the task exchange and MUST NOT be interpreted as terminal completion.

## 10. Error and cancellation

An `error` message reports a protocol-visible or task-level failure. A `cancel` message requests cancellation of a task. Both are immutable messages subject to identity, ordering, and deduplication rules.

## 11. Retry and attempts

Retries are operational attempts, not protocol identities.

If publication of message `M-123` fails after an unknown outcome, retry publication using exactly `M-123`, the same sequence, and the same semantic payload. If the receiver has already accepted `M-123`, it recognizes duplicate acceptance rather than executing it again.

If execution fails and the task contract permits retry, the implementation MAY create a new execution attempt while retaining the same `task_id`. The retry policy MUST explicitly define whether a new control/command message is required.

## 12. Ordering and gaps

For an ordered stream, a receiver records the highest durably accepted sequence. If sequence `N+1` is discovered before `N`, the receiver reports a gap and MUST NOT silently reinterpret discovery order as protocol order.

## 13. State transitions

Task lifecycle state is separate from message sequence. A RESULT or other authorized event may cause a task transition, but sequence number itself never determines state.

State changes use `state_version` and optimistic concurrency. Message receipt MUST NOT imply a state transition unless the message type and task contract authorize it.

## 14. Identity invariants

1. No two different semantic messages share a `message_id`.
2. One logical publication retry does not create a new `message_id`.
3. Every ACK and RESULT has its own `message_id`.
4. `sequence` is unique within an ordered stream.
5. Sequence does not identify a task.
6. `correlation_id` does not replace message identity.
7. `causation_id` points to an existing or causally expected message.
8. A transport retry never creates a second logical execution.
9. Task completion is determined by task state/result semantics, not sequence or commit order.
10. Immutable messages are never edited in place.

## 15. Canonical example

```text
Conversation C-1
Stream S-1 (ordered)

seq 1  COMMAND  M-100  task T-10
             |
             +------> ACK M-101
             |        causation=M-100
             |
             +------> EVENT M-102  (progress)
             |        causation=M-100
             |
             +------> RESULT M-103
                      causation=M-102
                      correlation=M-100
```

A lost ACK does not justify a second command. The sender retries publication of `M-100`.
