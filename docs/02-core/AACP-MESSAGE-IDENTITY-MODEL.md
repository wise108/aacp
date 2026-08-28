# AACP 1.0 Message Identity Model

## Scope

This document explains identity and relationships between AACP messages. The normative source is `docs/02-core/specification.md`.

## Identifiers

- `conversation_id` identifies a collaboration context.
- `task_id` identifies one logical unit of work.
- `message_id` identifies one immutable protocol message.
- `correlation_id` MAY link related messages.
- `causation_id` MAY identify the immediate message that caused another message.

These identifiers are not interchangeable.

## Message identity

Every AACP message has an immutable `message_id`. Retransmission of the same message MUST reuse that ID. A retry MUST NOT create a new message merely because delivery was attempted again.

Every ACK and RESULT is itself a new message and therefore has its own `message_id`.

## Task identity

Task-related messages carry `task_id`. A logical task may have multiple messages over its lifecycle. An explicit execution retry MAY retain the same `task_id` while remaining subject to the task's retry policy.

## Correlation and causation

`correlation_id` and `causation_id` provide optional trace relationships. They never replace `message_id` or `task_id`.

## Ordering

`sequence` and `stream_id` are optional Core metadata. AACP Core does not require ordered delivery. If a transport profile defines ordering, that profile defines the scope and processing rules for these fields.

## Internal implementation identifiers

An implementation MAY maintain internal execution IDs, delivery IDs, storage IDs, attempt counters or similar metadata. These are not AACP identities and MUST NOT change Core message or task semantics.

## Identity invariants

1. Different semantic messages MUST NOT share a `message_id`.
2. Retransmission MUST reuse the original `message_id`.
3. Duplicate command delivery MUST NOT create duplicate logical execution.
4. `task_id` identifies logical work; `message_id` identifies one protocol message.
5. Ordering metadata, where used, MUST NOT be treated as message identity.
6. Immutable messages MUST NOT be edited in place.
