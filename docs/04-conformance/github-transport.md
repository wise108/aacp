# AACP GitHub Transport Conformance 1.0

This document defines conformance requirements for an implementation that claims support for the AACP GitHub Transport 1.0 profile.

It does not add requirements to AACP Core implementations that do not use this transport profile.

## Profile selection

An implementation using the GitHub Transport profile MUST satisfy every normative `MUST` and `MUST NOT` in `docs/03-transports/github.md`.

If sequence-based ordering is enabled, the implementation MUST additionally demonstrate the ordered-stream requirements below.

## Ordered-stream requirements

The implementation MUST demonstrate all of the following:

1. **Canonical allocation** — sequence allocation is based on authoritative canonical remote state, not local state alone.
2. **Concurrency protection** — publication is bound to the canonical state observed during allocation and uses compare-and-swap or an equivalent non-force mechanism.
3. **Stale-writer rejection** — a writer whose canonical state is stale cannot publish its allocation; it must rediscover state and retry with a new sequence.
4. **Sequence uniqueness** — a new `message_id` cannot reuse an already allocated sequence within the same `(conversation_id, stream_id)` ordering domain.
5. **Identity separation** — `message_id` remains the message identity; sequence is ordering metadata only.
6. **Duplicate handling** — retransmission of the same message preserves both `message_id` and sequence.
7. **Conflict detection** — different message IDs occupying one sequence are detected as `ORDERING_CONFLICT` and are not silently collapsed.
8. **Gap handling** — a missing expected sequence is distinguished from a collision and is rediscovered against canonical state before being accepted as a real gap.
9. **Immutable recovery** — recovery never edits, deletes, or renumbers historical messages.
10. **Reconciliation** — a true collision is frozen, inventoried, classified, durably recorded, and only then allowed to resume.
11. **Safe continuation** — after reconciliation, the next allocation is strictly above every allocated sequence discovered in canonical state.
12. **Restart recovery** — after restart or interruption, durable canonical state is rediscovered before ordered processing resumes.
13. **Publication verification** — successful publication is verified against the canonical remote ref when the implementation can perform that verification.
14. **No force-push recovery** — force-push is never used to bypass stale-writer protection on a canonical ordered stream.

## Required evidence

A conformant implementation SHOULD provide deterministic evidence for each requirement, including:

- canonical commit/ref before allocation;
- canonical commit/ref observed at publication;
- allocated sequence and message ID;
- writer/version token;
- publication result;
- stale-writer rejection where applicable;
- conflict classification where applicable;
- reconciliation record identifier;
- next safe sequence;
- proof that historical message records were unchanged.

## Mandatory scenarios

At minimum, an ordered GitHub implementation MUST exercise these scenarios:

### G1 — Sequential allocation

Two sequential writers allocate distinct increasing sequences from canonical state.

### G2 — Concurrent stale writer

Two writers allocate from the same canonical state. The first publishes successfully. The second publication is rejected as stale, rereads canonical state, and allocates a new sequence.

### G3 — Historical collision

Two immutable records with different message IDs occupy the same sequence. The implementation detects `ORDERING_CONFLICT`, preserves both records, freezes the affected stream, and does not execute either command merely because it was discovered during recovery.

### G4 — Collision reconciliation

After G3, the implementation publishes an auditable reconciliation record, computes the next sequence as `max(canonical allocated sequence) + 1`, rereads canonical state, and resumes safely.

### G5 — Real gap

A missing sequence is rediscovered against canonical state. The implementation distinguishes the gap from an ordering collision and does not fabricate a message or compact the sequence.

### G6 — Restart during uncertainty

After restart, the implementation reconstructs state from canonical durable records and does not re-execute a command solely because ACK/RESULT state is missing.

## Relationship to Core conformance

Passing these scenarios demonstrates conformance to the GitHub Transport profile only. Core conformance remains governed by `docs/04-conformance/requirements.md` and `docs/02-core/specification.md`.
