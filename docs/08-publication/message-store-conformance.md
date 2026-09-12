# Message Store Backend Conformance

**Status:** Phase 2B.2 audit

This document defines the conformance boundary between the production Git CLI
backend and the GitHub Git Data API backend. The implementations may use
different storage mechanisms, but they implement one transport-neutral
`MessageStore` contract.

## Semantic matrix

| Contract property | Git CLI | GitHub Git Data API |
|---|---|---|
| Canonical state | canonical remote Git ref tip | canonical GitHub ref tip |
| Ordering domain | `(target_ref, stream_id)` | `(target_ref, stream_id)` |
| Message layout | `.aacp/conversations/<conversation_id>/messages/` | same |
| Sequence allocation | caller-owned; store never allocates | caller-owned; store never allocates |
| Publication preparation | immutable `PreparedPublication` | same |
| CAS precondition | expected canonical tip | expected canonical tip |
| Concurrent writer | non-fast-forward push → `CasConflict` | ref update HTTP 409 → `CasConflict` |
| Ambiguous write | `CasUncertain` | `CasUncertain` |
| Successful publication | canonical ref advances to publication commit | canonical ref advances to publication commit |
| Verification | canonical tip + publication evidence | canonical tip + publication evidence |
| Provenance | commit that introduced message path | newest commit returned for the immutable message path |

## Error classification

The GitHub adapter does not classify HTTP errors globally as CAS conflicts.
Only the canonical ref update interprets HTTP 409 as `CasConflict("head_moved")`.
Other API failures, including HTTP 422 validation failures, remain ordinary API
errors and are treated as uncertain when they occur during publication.

This distinction is important: a failure while creating a blob, tree, or commit
is not evidence that another writer advanced the canonical state.

## Publication invariants

1. `force=false` is mandatory for the GitHub ref update.
2. The publication commit has the expected canonical tip as its parent.
3. The canonical ref is the only authoritative publication pointer.
4. Unreachable Git objects created before a lost CAS are not a second Message
   Store and do not become publication state.
5. A successful publish is not accepted until the canonical ref is reread and
   the message's publication provenance is discoverable.
6. A `CasUncertain` outcome must be reconciled by `message_id` before a caller
   allocates another candidate publication.

## Current test coverage

The GitHub backend tests cover:

- successful Git Data API publication;
- stale canonical state detected before object creation;
- HTTP 422 remaining a non-CAS API error;
- HTTP 409 on the canonical ref update becoming `CasConflict`;
- publication provenance remaining the original path-introduction commit even
  when a later commit also touches the queried path history.

The test file imports the backend from the production package export, so a
missing public export is also detected by the test collection/import path.

## Scope boundary

This conformance layer does not introduce a second transport, registry, or
orchestration state store. Registry state remains derived/orchestration state;
the Message Store remains the authoritative ordered publication stream.
