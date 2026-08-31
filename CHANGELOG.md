# Changelog

## 1.1.0 — 2026-08-31

### Protocol / transport

- Hardened GitHub ordered-stream sequence allocation and canonical-state protection.
- Formalized stale-writer handling and distinction between `ORDERING_CONFLICT` and `SEQUENCE_GAP`.
- Formalized the publication boundary between local preparation and durable remote publication.
- Clarified that durable publication, orderability, and execution are separate states.
- Strengthened immutable-history and reconciliation requirements for published ordering conflicts.
- Added restart/rediscovery requirements for unresolved ordered-stream ambiguity.

### Conformance

- Added executable GitHub ordered-stream scenarios G1–G6.
- Added coverage for publication/execution separation and collision recovery.
- Added recovery and reconciliation requirements to the conformance checklist.

### Adoption

- Added a transport-independent agent adoption/recovery prompt.
- Kept project/repository identifiers out of the normative protocol documentation.

### Compatibility

- AACP Core remains **1.0**. This release is the AACP protocol distribution **1.1.0** and strengthens the GitHub transport/recovery profile without redefining Core message semantics.

## Unreleased — post-1.1.0 hardening

### GitHub Transport

- Normatively distinguish local-only preparation from durably published transport records.
- Clarify that published, orderable, and executed are independent states.
- Define operational states for recovery: `LOCAL_ONLY`, `PUBLISHED`, `ORDERABLE`, `NON_ORDERABLE`, `EXECUTED`, `NOT_EXECUTED`, and `UNKNOWN`.
- Prevent an unresolved cursor from crossing an ordering ambiguity merely because its numeric sequence is higher.
- Clarify recovery handling of stale unpublished allocations.

These changes are intended for the next protocol distribution release after conformance validation.
