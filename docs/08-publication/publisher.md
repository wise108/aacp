# AACP Publisher Contract 1.0

**Status:** Normative  
**Layer:** Publication & Bridge  
**Depends on:** AACP Core 1.0; applicable transport profile (for GitHub ordered streams: GitHub Transport 1.0 + ordered-stream semantics)

## 1. Purpose

The Publisher is the only component authorized to allocate ordered-stream `sequence` values and to commit a message into the canonical Message Store.

External callers, Bridges, agents, and humans MUST treat the Publisher as the sole owner of sequence allocation for publication.

## 2. API

```text
publish(envelope, target) -> PublicationReceipt
```

### 2.1 Inputs

- `envelope` — AACP message envelope **without** an authoritative `sequence`. If `sequence` is present, the Publisher MUST strip/ignore it; it MUST NOT treat a caller-supplied value as the authoritative allocated sequence.
- `target` — publication target binding resolved by policy (repository/ref/conversation/stream/profile). Callers MUST NOT freely invent arbitrary targets outside an authorized binding.

### 2.2 Output

`PublicationReceipt` — evidence that the message is durably published and verified in the canonical Message Store. See §7.

## 3. Mandatory algorithm

The Publisher MUST:

1. **Validate envelope** against AACP Core required fields and schema constraints applicable to the message type.
2. **Read and validate canonical state** — confirm that the requested target ref and stream match the authoritative Message Store state before idempotency lookup or allocation.
3. **Check idempotency** — if `message_id` is already present in the canonical Message Store with matching semantic content, return a receipt for the existing publication (idempotent success), including its original publication commit/version. If the same `message_id` exists with conflicting content, fail with `PUBLICATION_CONFLICT`; do not overwrite.
4. **Calculate candidate sequence** for the target's single ordered-stream domain:
   - candidate = `max(existing envelope.sequence values in the domain) + 1`
   - gaps from historical conflicts remain; do not renumber history
   - filenames are **not** authoritative for uniqueness or ordering
5. **Perform CAS publication** via the Message Store contract (`publish_cas` / equivalent) against the exact state token read in step 2.
6. **On CAS conflict** — reread canonical state and retry from step 2. Do not force-update the canonical ref. Do not keep a stale candidate sequence after the ref advanced.
7. **Verify publication** — confirm the message is discoverable at the new canonical head with the expected `message_id`, allocated `sequence`, and exact publication provenance.
8. **Return `PublicationReceipt`**.

## 4. Sequence ownership (critical)

```text
Caller / Bridge  ≠  owner of authoritative sequence
Publisher        =  owner of candidate allocation inside the CAS loop
Successful CAS + verify = moment the sequence is occupied
```

### MUST

- Caller MUST NOT supply an authoritative `sequence`.
- Publisher MUST allocate sequence only from canonical remote/store state for the target's ordering domain.
- Retransmission of the **same** logical message MUST reuse the same `message_id`.
- A sequence value is occupied only after durable verified publication (or durable evidence of publication per transport ordered-stream rules).

### MUST NOT

- Reintroduce caller-controlled `fixed_sequence` as a public Publisher API.
- Treat local preparation or unverified local commit as allocated history.
- Force-push / force-update the canonical ref to publish a stale allocation.
- Create a new `message_id` merely because a receipt/ACK was lost.
- Create a new sequence merely because a receipt/ACK was lost while publication outcome is uncertain.

### Uncertain publication

If the outcome of a CAS attempt is unknown (timeout, crash after write, ambiguous verify):

1. Treat the message as **potentially published**.
2. Reconcile against the canonical Message Store by `message_id`.
3. If found → return receipt for the existing publication, with the original publication commit/version and no new sequence.
4. If proven absent → retry with a fresh candidate allocation for the same `message_id`.
5. MUST NOT assume absence without rediscovery.

## 5. Idempotency

| Situation | Required behavior |
|---|---|
| Same `message_id`, same semantic content, already published | Idempotent success; return existing receipt and original publication version; no new message artifact |
| Same `message_id`, different content | Conflict; do not overwrite immutable history |
| Retransmission | Same `message_id`; do not mint a new logical message |
| Duplicate command delivery after accept | Receiver/runtime concern; Publisher still must not create duplicate artifacts for the same `message_id` |
| Lost ACK/receipt after successful publish | Reconcile by `message_id`; do not allocate a new sequence “to be safe” |

`message_id` is the immutable identity and idempotency key of one published message (Core).

## 6. Relation to execution

Publication is transport durability only:

```text
published ≠ accepted ≠ executed ≠ completed
```

A successful `publish` does **not** imply:

- command accepted by an agent;
- command executed;
- result produced;
- task completed.

Those are Agent Runtime / Core lifecycle concerns.

## 7. PublicationReceipt

Normative receipt fields:

| Field | Meaning |
|---|---|
| `message_id` | Published message identity |
| `conversation_id` | Conversation of the published message |
| `stream_id` | Stream (when ordering applies) |
| `sequence` | Allocated and verified sequence (when ordering applies) |
| `target_ref` | Canonical transport ref (e.g. `refs/heads/…`) |
| `publication_commit` | **Exact** commit/SHA or equivalent store version that introduced the published message |
| `published_at` | Publisher-observed publication timestamp (transport evidence; not Core identity) |
| `verified` | Boolean; MUST be `true` for a successful receipt |

`publication_commit` MUST remain the original publication version when a later duplicate or uncertain reconciliation observes the message at a newer canonical head.

Optional diagnostic metadata MAY be attached but MUST NOT replace these fields.

### Receipt meaning

`PublicationReceipt` means **only**:

> The message is confirmed published in the canonical Message Store.

It MUST NOT be interpreted as ACK acceptance, execution start, execution success, or task completion.

## 8. Errors (logical categories)

Implementations SHOULD map failures into stable categories, for example:

- `PROTOCOL_INVALID` — envelope/schema/type invalid
- `TARGET_UNAUTHORIZED` / `TARGET_INVALID` — binding/policy rejection
- `PUBLICATION_CONFLICT` — same path/`message_id` with different content, or immutable overwrite attempt
- `ORDERING_CONFLICT` — observed when canonical history already contains conflicting sequence occupancy (Publisher must not create a new one deliberately)
- `TRANSPORT_CONFLICT` — CAS lost; retryable after reread
- `TRANSPORT_UNAVAILABLE` — transient network/API failure
- `PUBLICATION_UNVERIFIED` — write may have occurred; reconcile required

Exact HTTP/Git diagnostics remain diagnostic detail.

## 9. Non-goals

- Replacing Core message types or task state machine
- Defining agent discovery/polling algorithms beyond verification needs
- Defining Bridge trigger surfaces (see `bridge.md`, `github-issue-bridge.md`)
- Mandating a particular programming language or package layout
