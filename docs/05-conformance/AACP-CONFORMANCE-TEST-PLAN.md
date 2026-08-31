# AACP Conformance Test Plan

## Purpose

This plan defines the observable behaviors required to validate the AACP GitHub ordered-stream profile. Tests MUST validate normative protocol invariants rather than a particular implementation mechanism.

## G1 — Sequential allocation

Verify that successfully published messages in one `(conversation_id, stream_id)` have unique, strictly increasing sequences. A durably published sequence MUST NOT be reused.

## G2 — Stale writer

Create two writers from the same canonical state. After one writer advances canonical state, the stale writer MUST NOT overwrite or publish against the stale state. It MUST rediscover canonical state before retrying.

## G3 — Historical collision

Create two durable records with the same sequence and different `message_id` values. The collision MUST be detected. Conflicting published records MUST remain immutable and preserved.

## G4 — Collision reconciliation

Verify that a detected collision is frozen, inventoried, classified, preserved, reconciled with durable evidence, and only then permits ordered continuation. Reconciliation MUST be idempotent.

## G5 — Sequence gap

Present a stream with a missing sequence. A gap MUST NOT be treated as an ordering collision. Canonical rediscovery MUST occur before recovery proceeds.

## G6 — Restart / rediscovery

Restart from canonical state. Verify that local cache is not authoritative and that unresolved ordering ambiguity survives restart. Cursor MUST NOT cross an unresolved sequence.

## G7 — Local vs published

Verify that local preparation or a local commit is not treated as durable publication. Publication requires remote publication and verification.

## G8 — Published collision

Verify that durable conflicting records are `PUBLISHED` but `NON_ORDERABLE`, and are not executed while the collision remains unresolved.

## G9 — Published vs executed

Verify that publication and execution are separate states. Missing ACK or RESULT MUST NOT be interpreted as proof that execution did not occur.

## G10 — Unresolved cursor

For `N`, `N+1/A`, `N+1/B`, `N+2`, verify that `last_processed` MUST NOT cross unresolved `N+1`; `N+2` MUST NOT be processed until reconciliation has resolved the ambiguity.

## Retry after unknown publication

When publication outcome is unknown, the implementation MUST rediscover canonical state before deciding whether a new sequence is required. If the original message is found, its existing `message_id` and sequence remain authoritative. If authoritative rediscovery establishes that it was not published, retrying the same logical message MUST preserve its `message_id` and may allocate a new sequence.

## Evidence and classification

Each scenario records Given / When / Then / Forbidden / Evidence. A conformance failure is valid only when the tested behavior is normatively required and observable. Tests MUST NOT require a particular internal CAS, storage, or state-machine implementation when the specification permits equivalent mechanisms.
