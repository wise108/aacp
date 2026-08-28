# AACP Agent Runtime Contract 1.0

## Purpose

This document defines the mandatory behavior of an AI agent after AACP adoption. It is transport-neutral. The agent MUST follow the selected AACP transport profile for physical publication and discovery.

## 1. AACP is the sole inter-agent protocol

After successful cutover, all inter-agent commands, acknowledgements, results, progress notifications, and protocol errors MUST use AACP. Agents MUST NOT use ad-hoc markdown files, hidden conventions, commit messages, branch names, timestamps, or chat text as a parallel protocol.

Project documentation may describe work, but it is not an inter-agent message channel unless explicitly represented as an AACP artifact.

## 2. Roles

An agent MAY act as sender, receiver, or both. Role is determined per message and task; it is not permanently tied to a product identity.

## 3. Sending

For every new logical message the sender MUST create a globally unique `message_id`, associate it with a `task_id` and conversation/stream, assign the next sequence for an ordered stream, validate the envelope, and publish it through the active transport profile.

A retry of the same logical send MUST reuse the same `message_id` and semantic payload.

The sender MUST NOT treat local creation of a message as delivery. Delivery is established only by the transport/Core acceptance semantics defined by AACP.

## 4. Receiving

A receiver MUST validate protocol version, message identity, task/conversation binding, sequence rules, and required fields before processing a message.

The receiver MUST durably record acceptance before performing non-idempotent side effects when the implementation architecture permits a durable boundary. If that ordering is impossible, the side effect MUST itself be idempotent and recoverable.

## 5. ACK

ACK means acceptance of the message for processing; it does not mean that the requested work is complete.

A receiver MUST NOT send a successful completion result as a substitute for ACK semantics when the protocol requires both.

## 6. Execution

A task is executed only after valid acceptance. Duplicate delivery of an already accepted `message_id` MUST NOT cause the logical side effect to execute twice.

Task state transitions MUST follow the AACP state machine and optimistic concurrency rules. A stale `state_version` MUST produce `STATE_CONFLICT` rather than silently overwriting newer state.

## 7. Result

A completed, failed, or cancelled task MUST produce an AACP result when the command contract requires a result. The result references the originating `task_id` and, where applicable, the command `message_id`.

Results are messages/artifacts in their own right and MUST be independently identifiable and recoverable.

## 8. Progress

Progress notifications are optional unless required by the task contract. They MUST NOT be interpreted as completion. Progress events MUST be safe to duplicate.

## 9. Errors

Protocol errors are machine-readable AACP error categories. Transport-specific diagnostics MAY be attached as metadata. An agent MUST NOT encode protocol state only in prose such as "failed", "done", or "please retry".

## 10. Recovery

On restart an agent MUST reconstruct pending protocol work from durable AACP state and transport artifacts. It MUST reconcile remote publication before retrying execution.

A lost ACK MUST be treated as an acknowledgement-delivery problem, not as evidence that the original command never executed.

A transport retry MUST reuse message identity. A task MUST NOT be re-executed solely because a transport response was lost.

## 11. Ordering

For ordered streams, an agent MUST track the last durably accepted sequence and detect gaps. It MUST NOT infer logical order from Git commit order, file modification time, or discovery order.

For unordered streams, sequence gaps do not block independent messages.

## 12. Concurrency

Concurrent agents MUST use AACP state-version/CAS semantics for shared mutable state. A failed compare-and-swap is a conflict requiring reconciliation, not permission to overwrite.

## 13. Completion

A task is complete only when the AACP task state and required result/publication semantics indicate completion. A successful transport write alone does not imply task completion.

## 14. Human interaction

Human chat is an application/user interface, not an implicit AACP transport. If an agent receives an instruction through a human UI, it MUST convert it into an AACP command before treating another agent as the execution peer.

## 15. Protocol upgrades

An agent MUST read the active AACP protocol declaration and transport profile before operation. Unsupported protocol versions or incompatible required capabilities MUST fail explicitly rather than silently falling back to an older protocol.

## 16. Forbidden shortcuts

After cutover an agent MUST NOT:

- append commands to a legacy coordination file;
- edit an immutable AACP message;
- use commit SHA as a message ID;
- infer completion from a push;
- infer ordering from commit history;
- create a new message ID for a retry of the same logical command;
- delete protocol state merely because it has been processed;
- bypass `STATE_CONFLICT` by overwriting newer state;
- use a project-specific IPC convention in parallel with AACP.
