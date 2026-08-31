# Decision: Ordered Git Stream Recovery

Date: 2026-08-31

## Context

The 2026-08-30 `C-agent-dialogue` incident produced two immutable messages with sequence `35` in the same ordering domain. The incident exposed that a Git-backed ordered stream needs an explicit canonical-state allocation and reconciliation procedure.

## Decision

AACP Core remains transport-independent. Sequence remains optional Core metadata.

The GitHub transport profile is authoritative for ordered Git stream semantics. A writer MUST allocate against canonical remote state and publish using compare-and-swap or an equivalent non-force ref update. A stale writer MUST reread and allocate again.

A true collision is represented by different immutable `message_id` values occupying the same sequence in one ordering domain. The records are preserved and quarantined as a non-orderable historical position. The transport MUST NOT choose an application-level winner.

Recovery chooses the next allocatable sequence from canonical remote state and records reconciliation metadata before ordered processing resumes.

## Consequences

- Historical sequence values are never rewritten to repair ordering.
- Sequence is never used as message identity.
- Local state cannot authorize a publication against stale canonical state.
- Recovery is deterministic and auditable.
- Project-specific execution semantics remain outside the transport profile.

## Verification

The conformance harness now includes a deterministic model/test for collision reconciliation and preservation of conflicting message IDs. The full CI conformance suite remains the final executable verification gate.

## Cross-repository handoff

A ready-to-use recovery prompt for `wise108/cursor-remote-agent` is maintained at:

`docs/07-agent-adoption/AACP-GITHUB-ORDERED-STREAM-RECOVERY.md`

This repository does not modify `wise108/cursor-remote-agent` or any application repository as part of this decision.
