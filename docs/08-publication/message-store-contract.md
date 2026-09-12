# AACP Message Store Contract 1.0

**Status:** Normative  
**Layer:** Publication & Bridge  
**Depends on:** Applicable transport profile message layout and ordered-stream rules

## 1. Purpose

The Message Store contract is the abstract storage boundary used by the Publisher.

For the GitHub transport profile, **Git CLI** and **GitHub Git Data API** are two **backends of one Message Store contract**. They are not two AACP transports and MUST NOT become two authoritative stores.

```text
Publisher
  ↓
Message Store contract
  ├── Git backend
  └── GitHub API backend
       (and future backends that preserve the same semantics)
```

There is exactly one canonical Message Store per target binding. A conforming ordered-stream store instance represents one canonical ref and one `stream_id` ordering domain; `conversation_id` remains part of the Publisher target binding and message identity semantics.

## 2. Required semantics

Any conforming Message Store backend MUST provide:

| Semantic | Requirement |
|---|---|
| Canonical remote state | Reads and CAS are relative to the authoritative remote/store head for the target ref and stream domain |
| Immutable published messages | After verified publication, message artifacts MUST NOT be edited, deleted, or renumbered |
| CAS | Publication succeeds only if the store version/token still equals the version observed before allocation |
| No force push / force update | Canonical ref MUST NOT be force-updated to publish a stale allocation |
| Concurrent writers | Multiple writers MAY race; exactly one CAS wins per head; losers reread and retry |
| Reread after conflict | On CAS failure, discard stale candidate state and reread canonical state |
| Publication provenance | Successful publication and later idempotent reconciliation MUST expose the exact commit/version that introduced the message |
| Publication verification | After CAS success, verify the message is discoverable with expected `message_id` / `sequence` and publication provenance |

## 3. Abstract API

Names MAY vary by language. Semantics MUST match.

```text
read_canonical_state() -> CanonicalState
list_messages(state) -> Message[]
find_by_message_id(state, message_id) -> Message | None
find_publication_evidence(state, message_id) -> PublicationEvidence | None
prepare_publication(state, message) -> PreparedPublication
publish_cas(expected_state, publication) -> CasResult
verify_publication(state, message_id, sequence?) -> VerificationResult
```

### 3.1 `CanonicalState`

`CanonicalState` contains:

- `token` — authoritative store tip/concurrency token;
- `target_ref` — canonical transport ref represented by the store;
- `stream_id` — the single ordered-stream domain represented by the store.

The Publisher MUST validate that the requested `TargetBinding.target_ref` and `TargetBinding.stream_id` match the canonical state before checking idempotency or allocating a sequence.

### 3.2 `list_messages(state)`

Returns published message envelopes visible at `state` **for that state's single `stream_id` ordering domain**.

Sequence allocation MUST never be influenced by messages from another stream domain. Authority for ordered-stream uniqueness is `envelope.sequence` content, not filename prefixes. Filenames are storage layout.

### 3.3 `find_publication_evidence(state, message_id)`

Returns the published envelope plus the **exact canonical commit/version that introduced that message**. A current-head token MUST NOT be substituted merely because it is convenient: if later messages advanced the store, reconciliation still returns the original publication version.

### 3.4 `prepare_publication(state, message)`

Builds the immutable artifact(s) to publish (path, body, commit metadata) against `state`. Preparation alone MUST NOT consume a sequence in canonical history.

### 3.5 `publish_cas(expected_state, publication)`

Attempts to advance the canonical store from `expected_state` to a new state containing the publication.

- Success only if current canonical state still equals `expected_state`.
- `CasSuccess` MUST expose the exact publication commit/version.
- Failure modes include `head_moved` / conflict; these are retryable after reread.
- MUST NOT force-update past concurrent writers.

### 3.6 `verify_publication(...)`

Confirms the published message is present in canonical state after CAS and returns its exact publication commit/version when verified. Verification failure after a possibly-successful write MUST trigger reconciliation, not blind reallocation.

## 4. Ordering domain

For this Publication Layer contract, one Message Store target represents one ordered stream domain:

```text
(target_ref, stream_id)
```

The Publisher also binds the message to its `conversation_id`; transport-specific conversation layout remains governed by the applicable transport profile.

Sequence allocation (`max(sequence)+1`) is performed by the Publisher using `list_messages` from the matching canonical state, not by the backend inventing policy.

## 5. Git backend

Uses local git fetch / commit / push where non-fast-forward rejection of the canonical ref provides compare-and-swap.

```text
fetch canonical tip
  ↓
list envelopes at tip
  ↓
commit message artifact on that tip
  ↓
push without force
  ↓
verify remote tip + envelope + publication commit
```

A local commit without verified remote publication is not authoritative history.

## 6. GitHub API backend

Uses Git Data API (blobs/trees/commits) and updates `refs/heads/<canonical-branch>` with `force=false` (or equivalent CAS).

```text
GET ref tip
  ↓
list message blobs at tip
  ↓
create blob/tree/commit
  ↓
PATCH ref with force=false
  ↓
verify tip + envelope + publication commit
```

GitHub Contents API `createOrUpdateFileContents` that invents `sequence` is **not** a conforming Publication path for ordered streams under this contract.

## 7. Test-only backends

In-memory or fake CAS stores are permitted for conformance/unit tests if they preserve CAS, immutability, provenance, and verification semantics. They MUST NOT be used as production canonical stores.

## 8. What is not a Message Store

The following MUST NOT be treated as authoritative AACP Message Stores:

- GitHub Issues / comments
- Pull requests
- Actions run metadata
- Orchestration registries / projections
- Chat transcripts
- Local unpublished working trees
- Search indexes

They MAY act as Bridge control-plane triggers or caches only.

## 9. Relation to existing transport docs

Layout, filename conventions, and consumer discovery remain defined by:

- `docs/03-transports/github.md`
- `docs/03-transports/github-ordered-stream-semantics.md`
- `docs/05-transports/github-message-store.md`

This contract does not replace those documents. It defines the Publisher-facing storage operations required for race-safe publication.
