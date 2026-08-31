# Changelog

## [Unreleased]

### Protocol / transport

- Hardened GitHub ordered-stream sequence allocation and canonical-state protection.
- Formalized stale-writer handling and distinction between `ORDERING_CONFLICT` and `SEQUENCE_GAP`.
- Formalized the publication boundary between local preparation and durable remote publication.
- Clarified that durable publication, orderability, and execution are separate states.
- Added minimal normative semantics for allocation/publication lifecycle, retry identity, collision handling, cursor recovery, reconciliation idempotency, and execution uncertainty.
- Strengthened immutable-history and reconciliation requirements for published ordering conflicts.
- Added restart/rediscovery requirements for unresolved ordered-stream ambiguity.
- Clarified that an unresolved consumer cursor cannot cross an ordering ambiguity.

### Conformance

- Added executable GitHub ordered-stream scenarios G1–G6.
- Added executable coverage G7–G10 for publication/execution separation and unresolved collision state.
- Added recovery and reconciliation requirements to the conformance checklist.
- Defined observable invariants for concurrent allocation, stale writers, collision preservation, cursor blocking, retry identity, and publication/execution separation.

### Adoption

- Added a transport-independent agent adoption/recovery prompt.
- Kept project/repository identifiers out of the normative protocol documentation.

### Compatibility

- AACP Core remains **1.0**. The upcoming distribution release is **1.1.0** and strengthens the GitHub transport/recovery profile without redefining Core message semantics.

## 1.1.0-rc.2 — 2026-08-31

Release candidate adding minimal normative clarifications for ordered-stream allocation, retry identity, collision recovery, cursor semantics, reconciliation idempotency, and execution uncertainty. Final 1.1.0 release requires conformance validation and a Git tag/release artifact.

## 1.1.0-rc.1 — 2026-08-31

Release candidate for the transport/recovery hardening described above.
