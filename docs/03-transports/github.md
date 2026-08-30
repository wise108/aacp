# AACP GitHub Transport 1.0

This document defines the GitHub-specific profile for AACP. It is not part of AACP Core semantics.

## Repository layout

Recommended layout:

```text
.aacp/
├── protocol.yaml
├── conversations/
│   └── <conversation_id>/
│       └── messages/
├── tasks/
└── results/
```

Protocol records are durable state. A Git commit is a transport publication mechanism, not an AACP message identity.

## Publication

For Git-backed implementations the minimum publication sequence is:

```text
write valid records
  ↓
create commit
  ↓
push to canonical remote ref
  ↓
verify remote ref/commit when supported
```

A local commit is not publication. A successful local `git push` SHOULD be followed by verification when the transport can perform it.

GitHub transport does not define a separate `publication.status` message field. Publication state is transport state.

## Ordered message streams

A GitHub implementation MAY use sequence-based ordering for a message stream.

When sequence-based ordering is enabled:

- `stream_id` MUST be present on ordered messages;
- the ordering domain is `(conversation_id, stream_id)`;
- `sequence` MUST be a positive integer;
- sequence values MUST be unique within the ordering domain;
- sequence allocation MUST be strictly increasing;
- gaps are allowed;
- retransmission of the same message MUST reuse its original `sequence`;
- a different `message_id` using an already allocated sequence is an `ORDERING_CONFLICT`.

A sequence value is an ordering position, not a message identity. Consumers MUST use `message_id` for message identity and deduplication.

## Sequence allocation and multi-writer concurrency

The GitHub transport supports multiple writers. Sequence allocation MUST therefore be serialized against canonical remote state.

A writer allocating a sequence MUST:

1. fetch or otherwise obtain the current canonical remote state;
2. determine the next sequence in the applicable ordering domain;
3. create the message using that sequence;
4. publish against the state from which the sequence was allocated;
5. verify that the remote update succeeded.

If the canonical remote state has advanced before publication, the writer MUST treat the allocation as stale. It MUST NOT publish the same sequence against the newer state. It MUST reread canonical state, allocate a new sequence, recreate the message if necessary, and retry.

The exact Git primitive used to serialize writers MAY be implementation-specific, but it MUST provide compare-and-swap or equivalent protection against stale concurrent writers. A Git commit SHA may be used as the concurrency/version token; it is not the AACP sequence itself.

Example race:

```text
A reads 34
B reads 34

A publishes 35 → success
B publishes 35 → conflict/rejected
B rereads state
B allocates 36 → success
```

## Consumer discovery

A consumer MAY use a persisted sequence cursor only when this profile's uniqueness and monotonicity guarantees are in force.

The consumer SHOULD persist both:

```text
last_seen_sequence
last_seen_message_id
```

Sequence is used for ordering/discovery; `message_id` is used for identity and deduplication.

A consumer MUST NOT treat sequence equality alone as evidence that a message was already processed.

Discovery rules:

- `sequence > cursor` → candidate new message;
- `sequence == cursor` with the same `message_id` → duplicate/retransmission;
- `sequence == cursor` with a different `message_id` → `ORDERING_CONFLICT`;
- a gap (for example 34 → 36) → `SEQUENCE_GAP`; do not silently assume the missing message is absent;
- a message older than the current cursor → inspect `message_id`; it is not automatically a duplicate;
- conflicting ordering records MUST NOT be silently discarded.

When an ordering conflict is detected, the consumer MUST preserve all immutable records, stop advancing the affected ordering cursor past the ambiguity, and surface the conflict for reconciliation.

## Out-of-order and recovery

If a message arrives with a lower sequence than the highest observed sequence, the consumer MUST NOT rewrite its cursor backward. It MUST determine whether the message is a late delivery, rediscovered historical message, or evidence of an ordering violation.

After restart or transport interruption, the consumer MUST rediscover durable records from canonical remote state. Rediscovery MUST use message identity for deduplication and sequence only for ordering/discovery where the profile guarantees apply.

Missing ACK or RESULT MUST NOT be interpreted as proof that execution did not happen. Execution recovery remains governed by AACP Core.

## Atomicity

Related records MAY be committed together when practical. This does not create a Core-level transaction guarantee.

## Separation from execution

GitHub transport does not execute tasks. Cursor ACP, MCP, shell commands, LLM calls, and application logic remain outside this transport profile.
