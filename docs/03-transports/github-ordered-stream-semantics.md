# AACP GitHub Ordered-Stream Semantics 1.1

This document is a normative clarification of the GitHub ordered-stream profile. It does not add a new transport mechanism and does not change AACP Core 1.0.

## 1. Allocation and publication

For an ordered stream, the writer MUST determine the next sequence from canonical remote state and protect publication against a stale canonical ref using compare-and-swap or an equivalent mechanism.

A sequence is considered **allocated** for protocol purposes only when the corresponding message is durably published and the canonical publication has been verified, or when the transport has durable evidence that the allocation was published. A local preparation, local commit, or failed/unverified push is not authoritative history.

If publication is rejected because the canonical state advanced, the writer MUST reread canonical state before retrying. The retry of the same logical message MUST retain its `message_id`; it MUST NOT become a new logical command. Its original sequence MUST be retained if the original publication may have succeeded. A new sequence MAY be allocated only after rediscovery establishes that the original message was not published, or when the operation is explicitly a new logical message.

If the outcome of a publication attempt is unknown, the implementation MUST treat the message as potentially published until canonical rediscovery establishes whether it was published. It MUST NOT allocate a replacement sequence on the assumption that the original message was not published.

An allocation that is proven never to have been published does not permanently consume a sequence. An allocation that was durably published MUST never be reused, even if the corresponding record is later classified as non-orderable or otherwise ineligible for ordered processing.

## 2. Collision

If two different `message_id` values occupy the same sequence in one `(conversation_id, stream_id)`, the condition is `ORDERING_CONFLICT`.

All durably published conflicting records MUST remain immutable and MUST remain in canonical history. They MUST NOT be edited, deleted, or renumbered.

A conflicting sequence is **non-orderable** until reconciliation is durably recorded and verified. Neither conflicting message may be selected as the ordered message by the transport.

The transport does not choose an application-level winner.

## 3. Minimal recovery state

Implementations only need to distinguish these ordered-stream conditions:

- `last_processed` — the latest sequence known to have completed ordered processing;
- `unresolved_sequence` — the first sequence whose ambiguity blocks ordered processing, when one exists.

Discovery may observe higher sequences, but `last_processed` MUST NOT cross `unresolved_sequence`.

After restart, the implementation MUST reconstruct these values from canonical remote state and durable recovery records. Local cursor state is a cache, not authoritative history.

`last_processed` MUST advance only over positions that are known to have completed ordered processing or that have been explicitly resolved by a durable reconciliation. A restart MUST NOT cause the cursor to cross an unresolved sequence merely because higher sequence values are present in canonical history.

## 4. Reconciliation

A reconciliation record MUST have a unique `message_id` and MUST contain at least:

- ordering domain;
- conflicting sequence;
- conflicting message IDs;
- canonical ref/commit observed;
- classification;
- next safe sequence.

Publishing the same reconciliation record more than once MUST be idempotent by `message_id`.

After reconciliation is durably published and verified, the affected sequence remains historical but is no longer an unresolved ordered position. New allocation MUST use a sequence greater than every allocated sequence in the canonical ordering domain.

A verified durable reconciliation record is authoritative recovery evidence after restart. An implementation MUST use such a record when reconstructing whether the corresponding ordering ambiguity remains unresolved.

## 5. Publication and execution

Publication state and execution state are independent.

The minimum execution states needed for recovery are:

- `EXECUTED` — execution is positively established;
- `NOT_EXECUTED` — non-execution is positively established;
- `UNKNOWN` — execution outcome cannot be established.

A published message MUST NOT be assumed executed. An `UNKNOWN` command MUST NOT be automatically executed again merely because its ACK or RESULT is missing. Recovery MUST establish a safe idempotent retry or reconcile the external task state before another side effect.

## 6. Observable invariants

A conformant implementation MUST satisfy:

1. no two different published messages in one ordering domain have the same sequence without being detected as `ORDERING_CONFLICT`;
2. a stale writer cannot overwrite newer canonical state;
3. immutable published records are never removed or rewritten for reconciliation;
4. ordered processing cannot cross an unresolved sequence;
5. the same message retry retains `message_id` and, when already published, its original sequence;
6. publication alone does not establish execution.
