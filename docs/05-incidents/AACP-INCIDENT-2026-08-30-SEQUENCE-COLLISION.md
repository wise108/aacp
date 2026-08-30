# AACP Incident: Sequence Collision 2026-08-30

## Status

Protocol change required. Application repositories are not modified by this incident record.

## Incident

In conversation/stream `C-agent-dialogue`, two immutable messages were assigned `sequence = 35`:

- Cursor RESULT: `M-05b678fe51d152deb6ad43dc03323134`, task `T-s5-audit-20260830`;
- ChatGPT COMMAND: `M-8f31c6a9e2b547d0a1f8c3e9b6d20574`, task `T-s5-implementation-20260830`.

The message IDs, task IDs and payloads differ.

## Root cause

The GitHub transport was used as a multi-writer ordered append-only store, but sequence allocation was not explicitly serialized against canonical remote state. The consumer also treated sequence as a sufficient discovery cursor without an explicit transport-level uniqueness contract.

The Core protocol intentionally leaves sequence semantics to the transport profile. The gap was therefore at the Core/transport boundary, with an implementation/adoption assumption stronger than the published contract.

## Classification

**Specification gap + implementation/adoption error.**

This is not a reason to make sequence globally mandatory in AACP Core.

## Required invariants for ordered Git streams

For a GitHub transport ordered stream:

1. `stream_id` is required.
2. Ordering domain is `(conversation_id, stream_id)`.
3. Sequence is a positive integer.
4. Sequence values are unique within the ordering domain.
5. Allocation is strictly increasing.
6. Gaps are allowed.
7. Retransmission reuses the original sequence.
8. A different `message_id` occupying an allocated sequence is `ORDERING_CONFLICT`.
9. Allocation is serialized against canonical remote state using CAS or equivalent Git reference protection.
10. A stale writer MUST reread state and allocate a new sequence; it MUST NOT publish its stale allocation.
11. Consumers use `message_id` for identity/deduplication and sequence only for ordering/discovery.

## Consumer conflict handling

If two different message IDs occupy the same sequence in one ordering domain, the consumer MUST:

- preserve both immutable records;
- raise `ORDERING_CONFLICT`;
- stop advancing the affected sequence cursor beyond the ambiguity;
- reconcile the transport state before continuing ordered processing.

A sequence gap is distinct from a collision. For example, `34 → 36` is `SEQUENCE_GAP`, not an ordering collision.

## Remediation of this incident

The two historical messages MUST remain immutable. They MUST NOT be renumbered, edited or deleted merely to make the sequence unique.

The collision is recorded as a protocol incident. Future messages in the affected ordered stream must use the corrected allocation policy. Migration MUST establish the next safe sequence from canonical state rather than rewriting historical messages.

## Backward compatibility

AACP Core remains backward-compatible because `sequence` remains optional and transport-owned. Existing unordered messages are unaffected. Existing Git ordered streams require the new Git profile allocation and consumer rules.

## Conformance additions

The GitHub transport conformance suite must cover:

1. sequential multi-writer allocation;
2. concurrent allocation against the same remote state;
3. duplicate message retransmission;
4. same sequence with different message IDs;
5. sequence gaps;
6. out-of-order discovery;
7. rediscovery after restart;
8. retransmission with the original message ID and sequence;
9. ACK/RESULT correlation;
10. preservation of immutable historical messages after an ordering conflict.
