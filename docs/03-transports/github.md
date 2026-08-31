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
read canonical remote state
  ↓
write valid records against that state
  ↓
create commit
  ↓
push to canonical remote ref
  ↓
verify remote ref/commit
```

A local commit is not publication. A successful local `git push` SHOULD be followed by verification when the transport can perform it.

The publication attempt MUST be bound to the canonical state that was read before allocation. If the remote ref has advanced, the writer MUST treat the attempt as stale and retry from fresh canonical state. It MUST NOT force-update the canonical ref merely to publish a stale allocation.

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

1. read the canonical remote ref and the complete authoritative ordered-stream state needed to determine the next sequence;
2. determine the next sequence in the applicable ordering domain;
3. record the exact remote commit/ref state used for allocation as the writer's concurrency token;
4. create the message using that sequence;
5. publish only if the canonical ref still equals the concurrency token, using compare-and-swap or an equivalent non-force update;
6. verify the resulting canonical remote ref/commit.

If the canonical remote state has advanced before publication, the writer MUST treat the allocation as stale. It MUST NOT publish the same sequence against the newer state. It MUST reread canonical state, allocate a new sequence, recreate the message if necessary, and retry.

A failed push caused by a non-fast-forward or equivalent stale-ref condition is a stale allocation, not an `ORDERING_CONFLICT` in the message stream.

The exact Git primitive used to serialize writers MAY be implementation-specific, but it MUST provide compare-and-swap or equivalent protection against stale concurrent writers. A Git commit SHA may be used as the concurrency/version token; it is not the AACP sequence itself. A transport implementation MUST NOT use force-push to bypass this protection on a canonical ordered stream.

Example race:

```text
A reads 34 / commit X
B reads 34 / commit X

A publishes 35 → success, remote becomes Y
B publishes against X → rejected as stale
B rereads Y
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

## Deterministic conflict reconciliation

`ORDERING_CONFLICT` is a durable transport-state condition, not permission to repair history by editing records.

A consumer or recovery agent MUST perform reconciliation in this order:

1. **Freeze:** stop ordered processing for the affected `(conversation_id, stream_id)` beyond the conflicting sequence. Unrelated conversations/streams MAY continue.
2. **Inventory:** identify every immutable message at the conflicting sequence and record each `message_id`, task, type, and publication commit/ref.
3. **Canonicalize:** reread the canonical remote ref and rediscover the affected stream from durable remote records. Local indexes, caches, or stale worktrees MUST NOT be treated as authoritative.
4. **Classify:** determine whether the condition is a duplicate retransmission, a true collision (different message IDs at one sequence), a gap, or late/out-of-order discovery.
5. **Preserve:** never delete, edit, or renumber an immutable message to repair ordering.
6. **Quarantine:** a true collision makes that sequence position non-orderable. Conflicting records MUST be retained as historical records but MUST NOT be treated as one ordered message merely because they share a sequence.
7. **Advance safely:** choose the next allocatable sequence as `max(allocated sequence values in the canonical ordering domain) + 1`. Never reuse the conflicting value for a new message.
8. **Record reconciliation:** persist an auditable transport reconciliation record containing the ordering domain, conflicting sequence, involved message IDs, canonical ref observed, classification, and chosen next sequence. This record is transport metadata; it does not alter the AACP message envelopes.
9. **Resume:** ordered processing MAY resume only after the reconciliation record is durably published and canonical remote state has been re-read successfully. New messages MUST start at or above the chosen next sequence.

A reconciliation MUST NOT silently select one conflicting message as the winner unless an external, authoritative application rule explicitly identifies that message as superseding the other. The transport itself does not decide application semantics.

A reconciliation record is not a replacement message and MUST NOT be used as a substitute for either conflicting message.

## Gaps and recovery

A `SEQUENCE_GAP` is not an `ORDERING_CONFLICT`. A gap means that no discovered record currently occupies an expected sequence. The consumer MUST rediscover canonical state before deciding that a sequence was never published.

If a gap remains after canonical rediscovery, the consumer MUST NOT fabricate a message or silently compact the sequence. Because gaps are allowed by this profile, the implementation MAY continue according to its ordered-stream policy once it has established that the gap is real and not a publication race.

If a message arrives with a lower sequence than the highest observed sequence, the consumer MUST NOT rewrite its cursor backward. It MUST determine whether the message is a late delivery, rediscovered historical message, or evidence of an ordering violation.

After restart or transport interruption, the consumer MUST rediscover durable records from canonical remote state. Rediscovery MUST use message identity for deduplication and sequence only for ordering/discovery where the profile guarantees apply.

Missing ACK or RESULT MUST NOT be interpreted as proof that execution did not happen. Execution recovery remains governed by AACP Core.

## Atomicity

Related records MAY be committed together when practical. This does not create a Core-level transaction guarantee.

## Separation from execution

GitHub transport does not execute tasks. Cursor ACP, MCP, shell commands, LLM calls, and application logic remain outside this transport profile.
