# AACP 1.0 Consistency Review

## Scope

The normative Core specification, schemas, state machine, identity model, result/error semantics, adoption contract and conformance requirements are reviewed as one protocol.

## Canonical decisions

1. `ACCEPTED` is the durable acknowledgement boundary between `PENDING` and execution.
2. ACK vocabulary is `accepted`, `rejected`, `duplicate`.
3. `message_id` is immutable message identity and the idempotency key for retransmission.
4. `task_id` identifies the logical unit of work and may remain stable across an explicit execution retry.
5. `sequence` is optional Core metadata. Ordered delivery is a transport/profile concern.
6. `stream_id` is optional Core metadata and is not required for every AACP message.
7. Progress information is represented by `event`; Core does not define a separate `progress` message type.
8. `publication` is not an AACP Core concept. Transport-specific delivery, artifact publication and verification belong outside Core.
9. Core does not require brokers, distributed transactions, heartbeats, attempt ledgers or other infrastructure machinery.
10. Uncertain execution must be reconciled before retry; missing ACK or result is not evidence that execution did not happen.
11. Mutable task state uses optimistic concurrency; stale mutations must not overwrite newer state.

## Consistency result

The documents and schemas must express only the decisions above. Any transport-specific or project-specific behavior must be documented outside Core and must not redefine these semantics.

**DOCUMENT CONSISTENCY: PASS**
