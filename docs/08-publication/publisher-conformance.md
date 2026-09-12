# Publisher → MessageStore conformance

**Status:** Phase 2B.3 audit

This document records the boundary between the canonical Publisher and the
transport-neutral `MessageStore` contract. The Publisher owns retry/reconcile
policy; MessageStore implementations own canonical state and CAS publication.

## Contract matrix

| Concern | Publisher guarantee | MessageStore guarantee |
|---|---|---|
| Target binding | Validates `target_ref`, `stream_id`, `conversation_id`, protocol and version | Validates canonical state against its bound target/stream |
| Sequence | Ignores caller-supplied `sequence`; allocates a candidate from the current visible stream | Never allocates sequence; accepts a positive candidate in `PreparedPublication` |
| Idempotency | Checks `message_id` before allocation and after uncertain publication | Returns publication evidence for an existing `message_id` |
| CAS conflict | Re-reads canonical state and retries with a fresh candidate | Returns `CasConflict` when the canonical head moved |
| Uncertain outcome | Reconciles by `message_id` before another candidate is allocated | Returns `CasUncertain` when publication outcome cannot be established |
| Successful CAS | Requires post-publication verification before returning a receipt | Advances canonical state and exposes exact publication evidence |
| Duplicate different content | Raises `PublicationConflict` | Provides the existing message needed to detect the conflict |
| Execution state | Does not infer execution/completion from publication receipt | Does not own execution state |

## Uncertain reconciliation rule

`CasUncertain` is deliberately different from `CasConflict`:

1. The Publisher must inspect the current canonical state.
2. It must search for the same `message_id` and reconcile publication evidence.
3. If the message is found, return the existing publication receipt.
4. If it is not found, only then may the outer CAS loop allocate a new candidate.
5. If the reconciliation read itself fails, no candidate is allocated from that
   failed observation; the Publisher retries the whole CAS cycle.

This prevents an ambiguous write from being treated as a normal conflict and
prevents blind `N+1` sequence allocation.

## Backend neutrality

The Publisher imports only the `MessageStore` protocol and result models. It
does not inspect Git CLI errors, GitHub HTTP status codes, refs, trees, blobs,
or transport details. Therefore the same retry/reconciliation semantics apply
to the Git CLI backend and the GitHub Git Data API backend.

Backend-specific classification remains inside the backend:

- Git CLI non-fast-forward push → `CasConflict("head_moved")`.
- GitHub canonical ref update HTTP 409 → `CasConflict("head_moved")`.
- Other ambiguous publication failures → `CasUncertain(...)`.

## Current verification

Publisher tests cover:

- normal publication and verified receipt;
- duplicate `message_id` idempotency;
- duplicate `message_id` with different content;
- CAS conflict retry;
- concurrent sequence ownership;
- uncertain publication followed by reconciliation;
- lost-response idempotency;
- transient reconciliation-read failure without blind sequence allocation;
- target and stream-domain validation.

MessageStore backend tests separately cover the Git CLI and GitHub Git Data API
CAS/provenance behavior. No additional transport or Registry state is introduced
by the Publisher.

## Scope boundary

The Publisher is the policy layer between AACP/Core envelopes and the
MessageStore. It does not become a transport, Message Store, Registry, or
execution-state store. Published messages remain immutable.
