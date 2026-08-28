# AACP Core 1.0

This document is the normative Core specification.

## 1. Purpose

AACP provides a minimal, reliable contract for collaboration between autonomous software agents in environments where messages and state may be duplicated, reordered, delayed, partially published, or interrupted by process failure.

## 2. Non-goals

AACP Core does not define model selection or prompting, agent internals, Cursor ACP, MCP, Telegram/UI protocols, a message broker, distributed locking, event sourcing, or a mandatory transport.

## 3. Core objects

AACP 1.0 defines six normative objects: Envelope, Task, Message, Result, Publication, and Error.

## 4. Identity

Identifiers use prefixes `C-`, `T-`, and `M-` followed by a globally unique identifier such as a ULID. `conversation_id` identifies a logical collaboration conversation; `task_id` identifies a unit of work; `message_id` identifies one message and is its idempotency key.

## 5. Envelope

Every AACP message MUST contain `protocol`, `version`, `message_id`, `task_id`, `conversation_id`, `sender`, `recipient`, `sequence`, `type`, `created_at`, and `payload`. Message types are `command`, `ack`, `result`, `error`, `cancel`, and `event`.

`correlation_id` and `causation_id` MAY be supplied as optional metadata.

## 6. Streams and ordering

An ordered message stream is identified by `(conversation_id, sender, recipient)`. Sequence numbers are scoped to that stream and start at 1. Within a stream they MUST increase by exactly 1 for each message.

A receiver MUST detect a missing sequence. Under strict ordering it MUST NOT silently process a later message while an earlier sequence is missing. It SHOULD retain the later message and report `SEQUENCE_GAP`.

A receiver MAY support unordered processing for explicitly declared streams. In that case sequence numbers remain evidence of sender ordering but do not impose a processing barrier.

## 7. Delivery and idempotency

AACP Core uses **at-least-once delivery semantics**. A sender MAY retransmit a message when delivery or acknowledgement is uncertain. Receivers MUST therefore support idempotent command processing.

`message_id` is the idempotency key. A receiver claiming crash-safe duplicate suppression MUST durably record sufficient processing state before acknowledging a command, or use a command handler whose side effect is independently idempotent.

A duplicate command MUST NOT execute its side effect more than once when the implementation claims AACP command idempotency. An implementation MUST NOT claim effectively-once command execution unless it has a durable processing record or independently idempotent side effect.

AACP does NOT provide exactly-once network delivery. The combination of at-least-once delivery and idempotent command processing is the Core reliability model.

## 8. Task lifecycle

Task statuses are `PENDING`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `FAILED`, and `CANCELLED`. Implementations MUST enforce valid state transitions and MUST reject invalid transitions.

## 9. Optimistic concurrency

A Task MUST contain `state_version`. State mutation MUST use an expected version (CAS semantics or an equivalent atomic mechanism). If the expected version differs from the stored version, the mutation MUST fail with `STATE_CONFLICT` and MUST NOT overwrite newer state.

## 10. Acknowledgement

A receiver MUST send an `ack` for a received `command` unless the transport profile explicitly defines an equivalent reliable receipt mechanism. ACK status MUST distinguish at least `received`, `rejected`, and `duplicate`.

`received` means the message passed protocol validation and has been durably accepted for processing; it does NOT mean the task completed.

`rejected` means the message will not be processed. The receiver SHOULD provide an error code/reason.

`duplicate` means the message was already durably accepted or processed; the receiver MUST NOT execute it again.

Completion is represented by a `result` or `error` message. ACK delivery itself is not assumed reliable; senders MUST tolerate retry.

## 11. Result

A Result records the outcome of task execution. A completed task SHOULD include a concise summary and MAY include evidence such as commit references, test commands and exit codes, changed files, or other transport-neutral evidence.

A Result MUST NOT be interpreted as proof that it is remotely available.

## 12. Publication

Publication describes whether a Result is available to the remote participant through the selected transport. Publication status is `PENDING`, `PUBLISHED`, or `FAILED`.

`task.status: COMPLETED` and `publication.status: PUBLISHED` are independent facts. For a transport that supports remote verification, `PUBLISHED` MUST only be set after the transport confirms that the referenced Result is available remotely.

If publication succeeds remotely but the process crashes before local publication state is persisted, recovery MUST verify the remote artifact and reconcile local state to `PUBLISHED`. Publication reconciliation MUST NOT re-execute the Task.

## 13. Failure and recovery

Agents MUST persist enough durable state to recover after restart. On recovery, an implementation MUST reconcile pending messages, unacknowledged messages, in-progress tasks, completed results with pending publication, and transport publication state.

An implementation MUST NOT re-execute a command solely because an ACK or RESULT was lost. If execution may have happened without a durable processing record, recovery MUST treat the operation as potentially executed and use idempotent reconciliation rather than blindly re-running it.

## 14. Heartbeat

Long-running `IN_PROGRESS` tasks SHOULD update `heartbeat_at`. A stale heartbeat MAY trigger recovery. `STALE` is a diagnostic/recovery condition, not a Core Task status. Recovery MAY return a stale task to `PENDING` or otherwise reassign it, subject to implementation ownership rules.

## 15. Cancellation

A `cancel` message requests cancellation of a task. Cancellation MUST use optimistic concurrency with the current `state_version`.

If a cancellation request is based on version N and another valid mutation changes the task to version N+1 before cancellation commits, cancellation MUST fail with `STATE_CONFLICT` and MUST NOT overwrite the newer state.

If the task is already terminal (`COMPLETED`, `FAILED`, or `CANCELLED`), cancellation MUST NOT change its state. The implementation SHOULD return the current terminal state as the authoritative outcome.

Therefore, in a completion/cancellation race, the first successfully committed state transition wins; a stale concurrent operation loses with `STATE_CONFLICT`.

## 16. Errors

Errors use a stable `code`, human-readable `message`, `retryable` boolean, and optional structured `details`. See [errors.md](errors.md).

## 17. Atomicity

Where transport and storage support atomic transactions, task state, processing records, result records and publication metadata SHOULD be committed atomically where doing so prevents inconsistent recovery states. Core does not require a distributed transaction.

## 18. Trust and evidence

Agent prose such as “done” or “pushed” is not protocol evidence. AACP state MUST be based on durable protocol records and, where applicable, independently verified transport evidence.

## 19. Extensions

Implementations MAY add project-specific fields and error codes, provided they do not redefine Core semantics or make a valid Core object invalid. Extensions SHOULD be namespaced.

## 20. Conformance

An implementation claiming AACP Core 1.0 compatibility MUST satisfy the normative requirements in this specification and pass the mandatory scenarios in [../04-conformance/scenarios.md](../04-conformance/scenarios.md).

The companion documents in this directory explain individual Core objects and MUST remain consistent with this specification.
