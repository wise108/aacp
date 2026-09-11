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

There is exactly one canonical Message Store per target binding (one canonical ref + conversation message directory as defined by the transport profile).

## 2. Required semantics

Any conforming Message Store backend MUST provide:

| Semantic | Requirement |
|---|---|
| Canonical remote state | Reads and CAS are relative to the authoritative remote/store head for the target ref |
| Immutable published messages | After verified publication, message artifacts MUST NOT be edited, deleted, or renumbered |
| CAS | Publication succeeds only if the store version/token still equals the version observed before allocation |
| No force push / force update | Canonical ref MUST NOT be force-updated to publish a stale allocation |
| Concurrent writers | Multiple writers MAY race; exactly one CAS wins per head; losers reread and retry |
| Reread after conflict | On CAS failure, discard stale candidate state and reread canonical state |
| Publication verification | After CAS success, verify the message is discoverable with expected `message_id` / `sequence` |

## 3. Abstract API

Names MAY vary by language. Semantics MUST match.

```text
read_canonical_state() -> CanonicalState
list_messages(state) -> Message[]
prepare_publication(state, message) -> PreparedPublication
publish_cas(expected_state, publication) -> CasResult
verify_publication(state, message_id, sequence?) -> VerificationResult
```

### 3.1 `read_canonical_state()`

Returns a concurrency token for the target canonical ref/head (for Git-backed stores: commit SHA of the canonical branch tip) plus enough addressing information to list messages.

### 3.2 `list_messages(state)`

Returns published message envelopes visible at `state` for the target conversation/stream ordering domain.

Authority for ordered-stream uniqueness is `envelope.sequence` content, not filename prefixes. Filenames are storage layout.

### 3.3 `prepare_publication(state, message)`

Builds the immutable artifact(s) to publish (path, body, commit metadata) against `state`. Preparation alone MUST NOT consume a sequence in canonical history.

### 3.4 `publish_cas(expected_state, publication)`

Attempts to advance the canonical store from `expected_state` to a new state containing the publication.

- Success only if current canonical state still equals `expected_state`.
- Failure modes include `head_moved` / conflict; these are retryable after reread.
- MUST NOT force-update past concurrent writers.

### 3.5 `verify_publication(...)`

Confirms the published message is present in canonical state after CAS. Verification failure after a possibly-successful write MUST trigger reconciliation, not blind reallocation.

## 4. Ordering domain

When the transport profile enables ordered streams, the ordering domain is:

```text
(conversation_id, stream_id)
```

as defined by GitHub Transport / ordered-stream semantics.

Sequence allocation (`max(sequence)+1`) is performed by the Publisher using `list_messages`, not by the backend inventing policy.

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
verify remote tip + envelope
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
verify tip + envelope
```

GitHub Contents API `createOrUpdateFileContents` that invents `sequence` is **not** a conforming Publication path for ordered streams under this contract.

## 7. Test-only backends

In-memory or fake CAS stores are permitted for conformance/unit tests if they preserve CAS, immutability, and verification semantics. They MUST NOT be used as production canonical stores.

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
