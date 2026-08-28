# AACP Message & Identity Model 1.0

## 1. Scope

This document defines identity, causality, correlation, ordering, task binding, retries, acknowledgements, and results for AACP 1.0.

## 2. Objects

AACP distinguishes five concepts:

- **Conversation** — a durable logical context containing one or more streams and tasks.
- **Stream** — an ordered or unordered sequence of messages within a conversation.
- **Task** — the unit of requested work and lifecycle state.
- **Message** — an immutable protocol envelope carrying a command, acknowledgement, result, progress event, or protocol error.
- **Attempt** — an execution/publication attempt. An attempt is not a new logical task or message.

## 3. Identifiers

`conversation_id` identifies the conversation context and remains stable across messages belonging to it.

`task_id` identifies one logical unit of work. A retry does not create a new task.

`message_id` identifies one immutable protocol message. Every message, including ACK and RESULT, has its own message ID.

`correlation_id` identifies the logical exchange to which a message belongs. For a command and its direct lifecycle messages, it SHOULD normally equal the command's `message_id`.

`causation_id` identifies the immediate message that caused the current message. For an ACK, this is the accepted command message ID. For a RESULT, this is normally the command or the latest progress/processing message that directly caused the result.

These fields MUST NOT be treated as interchangeable.

## 4. Sequence

`sequence` belongs to a **stream**, not to a task and not to a message lifecycle.

For an ordered stream, each message published into that stream receives exactly one monotonically increasing sequence number. ACK and RESULT messages therefore consume sequence numbers when they are members of that ordered stream.

A receiver MUST use `(conversation_id, stream_id, sequence)` as the ordering coordinate. `message_id` remains the identity coordinate.

A task MAY span multiple streams. A single stream MAY contain messages for multiple tasks.

An unordered stream MAY omit meaningful ordering semantics; implementations SHOULD still retain a transport-local publication position where useful, but it MUST NOT be interpreted as AACP sequence.

## 5. Why sequence is separate from identity

Sequence answers **where a message sits in an ordered stream**.

Message ID answers **which immutable message this is**.

Task ID answers **which unit of work this message concerns**.

Correlation ID answers **which logical exchange this message belongs to**.

Causation ID answers **which prior message directly caused it**.

No implementation may substitute one for another.

## 6. Command

A command creates or addresses a task. A command is itself an immutable message. The command's `message_id` is the canonical identity of that particular command request.

A task MAY have multiple commands only when the command contract explicitly permits follow-up, resume, or control commands. A retry of the same command MUST reuse the same `message_id`.

## 7. ACK

An ACK is a new message with a new `message_id` and `causation_id` pointing to the accepted message. Its `correlation_id` points to the command exchange.

ACK states are:

- `accepted` — this message is accepted for processing;
- `duplicate` — this message was already accepted and will not create another logical execution.

ACK does not mean execution has completed.

## 8. Result

A RESULT is a new immutable message with a new `message_id`. It references the originating task and exchange through `task_id`, `correlation_id`, and `causation_id`.

A task normally has one terminal result for a given logical execution contract. A protocol MAY allow multiple non-terminal results or partial results only when explicitly declared by the task contract.

A result publication retry MUST reuse the same result message ID.

## 9. Progress

PROGRESS messages are new messages and SHOULD carry the same `correlation_id` as the task exchange. They do not change command identity and MUST NOT be interpreted as terminal completion.

Progress delivery is at-least-once unless a transport profile explicitly provides stronger semantics.

## 10. Error

An ERROR is a new message describing a protocol or task failure. Transport errors that prevent message publication may exist without an AACP message; once publication is possible, protocol-visible failures SHOULD be represented as AACP ERROR messages.

## 11. Retry and attempts

Retries are operational attempts, not protocol identities.

If publication of message `M-123` fails after an unknown outcome, retry publication using exactly `M-123` and the same semantic payload. If the receiver has already accepted `M-123`, it returns/recognizes duplicate acceptance rather than executing it again.

If execution itself fails and the task contract permits retry, the implementation MAY create a new execution attempt while retaining the same `task_id`. Whether a new command message is required depends on the command contract; an automatic retry MUST NOT invent a new logical request merely to avoid deduplication.

## 12. Ordering and gaps

For an ordered stream, a receiver records the highest durably accepted sequence. If sequence `N+1` is discovered before `N`, the receiver reports a gap and MUST NOT silently reinterpret discovery order as protocol order.

A receiver MAY process independent unordered streams concurrently.

## 13. State transitions

Task lifecycle state is separate from message sequence. A RESULT may cause a task transition to a terminal state, but sequence number itself never determines state.

State changes use `state_version` and optimistic concurrency. Message receipt MUST NOT imply a state transition unless the message type and task contract authorize it.

## 14. Identity invariants

The following invariants are mandatory:

1. No two different semantic messages share a `message_id`.
2. One logical retry does not create a new `message_id`.
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
Stream S-commands (ordered)

seq 1  COMMAND  M-100  task T-10
             |
             +------> ACK M-101
             |        causation=M-100
             |
             +------> PROGRESS M-102
             |        causation=M-100
             |
             +------> RESULT M-103
                      causation=M-102
                      correlation=M-100
```

A lost ACK does not justify a second `COMMAND M-104`. The sender retries publication of `M-100`.
