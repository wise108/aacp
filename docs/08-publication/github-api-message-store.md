# GitHub Git Data API Message Store Backend

**Status:** Phase 2B.2 implementation

`GitHubMessageStore` implements the same transport-neutral `MessageStore` contract as `GitMessageStore`. It uses GitHub's Git Data API; it does not introduce a second Message Store or a second publication model.

## Binding

The instance is bound to `owner`, `repo`, `target_ref`, `conversation_id`, and `stream_id`. The GitHub access token is an adapter credential and is never part of the AACP envelope.

## CAS semantics

Publication follows:

```text
GET canonical ref
  ↓
read commit/tree
  ↓
create blob
  ↓
create tree from expected base tree
  ↓
create commit with expected tip as parent
  ↓
PATCH canonical ref with force=false
  ↓
GET ref and verify
```

A ref update conflict is mapped to `CasConflict("head_moved")`. An ambiguous ref-update result is `CasUncertain`; the Publisher must reconcile by `message_id` before allocating again.

The object-creation operations may leave unreachable Git objects after a CAS conflict. That is harmless and does not change the canonical Message Store. Only the canonical ref determines publication.

## Provenance

After successful ref publication, verification resolves the original commit associated with the message path. The receipt therefore contains publication provenance rather than merely the current branch tip.

## Equivalence requirement

The Git CLI and GitHub Git Data API implementations MUST preserve the same abstract semantics:

- same canonical state model;
- same `(target_ref, stream_id)` ordering domain;
- same message layout;
- same caller prohibition on authoritative sequence allocation;
- same CAS conflict meaning;
- same uncertain-publication reconciliation rule;
- same publication verification requirement.

Implementation mechanism may differ; contract semantics may not.

## Scope

This backend does not implement Issues, project bindings, orchestration state, or runtime AACP integration. Those remain separate layers.
