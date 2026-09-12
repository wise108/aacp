# Changelog

## [Unreleased]

### Publication & Bridge Layer

- Added normative Publication & Bridge Layer under `docs/08-publication/`:
  - Publisher contract (`publish(envelope, target) -> PublicationReceipt`)
  - Message Store contract (Git and GitHub API as backends of one store)
  - Bridge contract
  - GitHub Issue Bridge profile (Issue as control-plane trigger, not Message Store)
- Explicitly forbids caller-controlled authoritative `sequence` and second authoritative Message Stores.
- **Phase 2A:** added canonical Publisher + Message Store skeleton under `src/aacp/` with in-memory test store and contract tests (uncertain publication reconcile-by-`message_id`, idempotency, CAS concurrency). No Git/GitHub production adapters yet.
- Post-2A hardening: public API is only `Publisher(store).publish(envelope, target)`; `InMemoryMessageStore` moved to test-only `aacp.testing`; packaging version remains distribution `1.1.0rc3` with no separate Publication API version.

### Protocol / transport

- Hardened GitHub ordered-stream sequence allocation and canonical-state protection.
- Formalized stale-writer handling and distinction between `ORDERING_CONFLICT` and `SEQUENCE_GAP`.
- Formalized the publication boundary between local preparation and durable remote publication.
- Clarified that durable publication, orderability, and execution are separate states.
- Added minimal normative semantics for allocation/publication lifecycle, retry identity, collision handling, cursor recovery, reconciliation idempotency, and execution uncertainty.
- Strengthened immutable-history and reconciliation requirements for published ordering conflicts.
- Added restart/rediscovery requirements for unresolved ordered-stream ambiguity.
- Clarified that an unresolved consumer cursor cannot cross an ordering ambiguity.
- Clarified unknown publication outcomes, durable reconciliation evidence after restart, and the cursor advancement boundary.

### Conformance

- Added executable GitHub ordered-stream scenarios G1–G6.
- Added executable coverage G7–G10 for publication/execution separation and unresolved collision state.
- Added recovery and reconciliation requirements to the conformance checklist.
- Defined observable invariants for concurrent allocation, stale writers, collision preservation, cursor blocking, retry identity, and publication/execution separation.

### Adoption

- Added a universal project-adoption prompt as the single canonical invocation point in the repository root `README.md`.
- Removed duplicate ready-to-use adoption prompts from protocol documentation.
- Kept project/repository identifiers out of the normative protocol documentation.

### Documentation consistency

- Aligned the README with the actual repository version `1.1.0-rc.3` from `VERSION`.
- Removed obsolete competing adoption-prompt entry points.

## 1.1.0-rc.3 — 2026-08-31

Release candidate clarifying unknown publication outcomes, durable reconciliation evidence after restart, and the ordered cursor advancement boundary. No new transport mechanism or Core semantics were introduced.

## 1.1.0-rc.2 — 2026-08-31

Release candidate adding minimal normative clarifications for ordered-stream allocation, retry identity, collision recovery, cursor semantics, reconciliation idempotency, and execution uncertainty. Final 1.1.0 release requires conformance validation and a Git tag/release artifact.

## 1.1.0-rc.1 — 2026-08-31

Release candidate for the transport/recovery hardening described above.
