# AACP Core 1.0 Specification

**Status:** Normative

This is the authoritative Core 1.0 specification.

## 1. Purpose

AACP provides a minimal, reliable contract for collaboration between autonomous software agents. It is designed for environments where messages and state may be duplicated, reordered, delayed, partially published, or interrupted by process failure.

## 2. Non-goals

AACP Core does not define model selection or prompting, agent internals, Cursor ACP, MCP, Telegram/UI protocols, a message broker, distributed locking, event sourcing, or a mandatory transport.

## 3. Core objects

AACP 1.0 defines six normative objects: Envelope, Task, Message, Result, Publication, and Error.

## 4. Identity

Identifiers use prefixes `C-`, `T-`, and `M-` followed by a globally unique identifier such as a ULID. `conversation_id` identifies a logical collaboration conversation; `task_id` identifies a unit of work; `message_id` identifies one message and is also its idempotency key.

## 5. Envelope

Every AACP message MUST contain `protocol`, `version`, `message_id`, `task_id`, `conversation_id`, `sender`, `recipient`, `sequence`, `type`, `created_at`, and `payload`. Message types are `command`, `ack`, `result`, `error`, `cancel`, and `event`. `correlation_id` and `causation_id` MAY be supplied as optional metadata.

## 6. Ordering

Messages belonging to an ordered stream MUST carry a monotonically increasing sequence number. A receiver detecting a missing sequence MUST NOT silently process a later message when strict ordering is required. It SHOULD retain the later message and report `SEQUENCE_GAP`. Sequence numbers are scoped to a stream and MUST NOT be used as globally unique identifiers.

## 7. Idempotency

A receiver MUST treat `message_id` as an idempotency key. Re-delivery of a previously processed message MUST NOT cause the underlying command to execute more than once. The receiver SHOULD return the prior acknowledgement or result reference.

## 8. Task lifecycle

Task statuses are `PENDING`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `FAILED`, and `CANCELLED`. Implementations MUST enforce valid state transitions and MUST reject invalid transitions.

## 9. Optimistic concurrency

A Task MUST contain `state_version`. State mutation MUST use an expected version (CAS semantics or an equivalent atomic mechanism). If the expected version differs from the stored version, the mutation MUST fail with `STATE_CONFLICT` and MUST NOT overwrite newer state.

## 10. Acknowledgement

A receiver SHOULD acknowledge a successfully received and syntactically valid message with an `ack` containing `status: received`. Completion is normally represented by a `result` message. Implementations MAY use a completed acknowledgement where a separate result message is not required. ACK delivery itself is not assumed reliable; senders MUST tolerate retry and receivers MUST be idempotent.

## 11. Result

A Result records the outcome of task execution. A completed task SHOULD include a concise summary and MAY include evidence such as commit references, test commands and exit codes, changed files, or other transport-neutral evidence. A Result MUST NOT be interpreted as proof that it is remotely available.

## 12. Publication

Publication describes whether a Result is available to the remote participant through the selected transport. Publication status is one of `PENDING`, `PUBLISHED`, `FAILED`. `task.status: COMPLETED` and `publication.status: PUBLISHED` are independent facts. For a transport that supports remote verification, `PUBLISHED` MUST only be set after the transport confirms that the referenced result is available remotely.

## 13. Failure and recovery

Agents MUST persist enough durable state to recover after restart. On recovery, an implementation MUST reconcile pending messages, unacknowledged messages, in-progress tasks, completed results with pending publication, and transport publication state. An implementation MUST NOT re-execute a task solely because an acknowledgement or result message was lost.

## 14. Heartbeat

Long-running `IN_PROGRESS` tasks SHOULD update `heartbeat_at`. A stale heartbeat MAY trigger recovery. `STALE` is a diagnostic/recovery condition, not a Core Task status. Recovery MAY return a stale task to `PENDING` or otherwise reassign it, subject to implementation ownership rules.

## 15. Cancellation

A `cancel` message requests cancellation of a task. Cancellation MUST respect the current task version and MUST NOT silently change a terminal task (`COMPLETED`, `FAILED`, `CANCELLED`).

## 16. Errors

Errors use a stable `code`, human-readable `message`, `retryable` boolean, and optional structured `details`. See [errors.md](errors.md).

## 17. Atomic publication

Where the transport supports atomic commits, task state, result records and publication metadata SHOULD be published in one transaction/commit boundary. This is a transport profile recommendation, not a Core requirement.

## 18. Trust and evidence

Agent prose such as “done” or “pushed” is not protocol evidence. AACP state MUST be based on durable protocol records and, where applicable, independently verified transport evidence.

## 19. Extensions

Implementations MAY add project-specific fields and error codes, provided they do not redefine Core semantics or make a valid Core object invalid. Extensions SHOULD be namespaced.

## 20. Conformance

An implementation claiming AACP Core 1.0 compatibility MUST satisfy the normative requirements in this specification and pass the mandatory scenarios in [../04-conformance/scenarios.md](../04-conformance/scenarios.md).

## Modular documents

The companion documents in this directory explain individual Core objects. They MUST remain consistent with this specification.
