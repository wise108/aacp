# AACP Core 1.0

AACP is a small, transport-independent contract for reliable collaboration between software agents.

## Scope

Core defines only conversation, task, message, result, identity, delivery, acknowledgement, lifecycle, recovery, cancellation, and optional ordering.

Core does not define LLMs, prompts, agent runtimes, Cursor ACP, MCP, Telegram, databases, brokers, or a mandatory transport.

## Message envelope

Required fields:

`protocol`, `version`, `message_id`, `conversation_id`, `task_id`, `type`, `sender`, `recipient`, `created_at`, `payload`.

Message types are: `command`, `ack`, `result`, `error`, `cancel`, `event`.

Optional fields are `correlation_id`, `causation_id`, `sequence`, and `stream_id`.

`sequence` and `stream_id` are transport-profile metadata used only when ordering is required. Core does not define their allocation, uniqueness, monotonicity, gap handling, or concurrency semantics. A transport profile that uses sequence for ordered discovery MUST define those semantics explicitly.

When a transport profile defines sequence ordering, retransmission of the same message MUST reuse the original sequence, when present. A consumer MUST NOT use sequence as a message identity unless the applicable transport profile explicitly guarantees that property.

## Identity and delivery

`message_id` is the immutable identity and idempotency key of one message.

`task_id` identifies one logical unit of work.

AACP uses at-least-once delivery semantics. A retry of the same message MUST reuse its `message_id` and MUST NOT create a new logical command.

Duplicate command delivery MUST NOT cause duplicate logical execution when AACP idempotency rules are implemented.

AACP does not promise exactly-once network delivery.

## ACK

A receiver SHOULD acknowledge a command. ACK status MUST distinguish:

- `accepted` — durably accepted for processing;
- `rejected` — will not be processed;
- `duplicate` — already accepted or processed.

`accepted` does not mean completed.

If an ACK is lost, the sender MAY retransmit the original command. The receiver MUST NOT execute it twice.

## Task lifecycle

Core states are:

`PENDING → ACCEPTED → IN_PROGRESS → COMPLETED`

`IN_PROGRESS → FAILED | CANCELLED | BLOCKED`

`BLOCKED → IN_PROGRESS`

`PENDING → CANCELLED`

`ACCEPTED → CANCELLED`

`FAILED → IN_PROGRESS` only when an explicit retry policy exists.

`COMPLETED` and `CANCELLED` are terminal. Invalid transitions MUST be rejected.

## Concurrency

An implementation storing mutable task state MUST prevent stale updates from overwriting newer state. `state_version` with compare-and-set semantics is RECOMMENDED.

If `state_version` is used, a stale mutation MUST fail with `STATE_CONFLICT`.

## Results and errors

A successful task produces a `result` message. A failed task produces an `error` message.

Result and error messages are immutable and have their own `message_id`.

## Recovery

Crash-safe implementations MUST persist enough information to distinguish accepted work, started execution, completed execution, and known results.

After restart, an agent MUST NOT execute a command again merely because an ACK or result was lost.

If execution outcome is unknown, the implementation MUST reconcile it or use an idempotent operation before retrying.

## Cancellation

`cancel` requests cancellation. Cancellation MUST NOT overwrite newer task state. A running operation MAY refuse cancellation when safe cancellation is impossible.

## Events

`event` carries non-terminal information such as progress. An event is not completion unless its contract explicitly says so.

## Extensions

Implementations MAY add fields and project-specific codes, but MUST NOT change Core semantics.

## Minimal conformance

A Core 1.0 implementation MUST demonstrate:

1. immutable unique message identity;
2. safe duplicate command handling;
3. accepted/rejected/duplicate ACK semantics;
4. valid task lifecycle enforcement;
5. protection against stale state overwrite;
6. safe restart behavior for uncertain execution.

Advanced fault-injection scenarios are test-harness features, not additional protocol requirements.
