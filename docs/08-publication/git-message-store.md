# Git Message Store Backend

**Status:** Phase 2B.1 implementation

`GitMessageStore` is the Git CLI implementation of the transport-neutral `MessageStore` contract. It is a backend, not a second AACP transport and not a second canonical store.

## Binding

A store instance is bound to:

- `target_ref` — a canonical `refs/heads/<branch>` ref;
- `conversation_id` — the message directory owner;
- `stream_id` — the single ordered-stream domain;
- `remote` — normally `origin`.

The binding is checked against every supplied `CanonicalState` and publication message.

## CAS publication

The backend uses the canonical commit SHA as the concurrency token:

```text
fetch canonical branch
  ↓
read canonical tip
  ↓
prepare immutable message artifact
  ↓
create child commit from expected tip
  ↓
push <commit>:<canonical-ref> without force
  ↓
fetch + verify canonical tip
  ↓
verify message + original publication commit
```

A non-fast-forward/rejected push is `CasConflict("head_moved")`. Other ambiguous push failures are `CasUncertain`; the Publisher must reconcile by `message_id` before allocating again.

## Local concurrency

Publication uses a temporary `GIT_INDEX_FILE` while constructing the candidate tree. The backend therefore does not require checkout/reset of the caller's working tree and does not share the normal index between concurrent publication attempts.

The canonical ref is never force-updated.

## Provenance

`publication_commit` is the exact commit that introduced the message artifact, discovered from immutable Git history. If later messages advance the branch, reconciliation of the earlier `message_id` still returns its original publication commit rather than the current branch tip.

## Message layout

The backend follows the GitHub transport profile layout:

```text
.aacp/conversations/<conversation_id>/messages/<sequence:06d>-<message_id>.json
```

The filename is storage layout only. Ordering authority remains the `sequence` field in the envelope.

## Scope

This backend intentionally does not implement:

- GitHub Git Data API publication;
- Issue Bridge;
- project-specific bindings;
- orchestration registry state;
- runtime AACP dependencies.

Those are separate Phase 2B stages.
