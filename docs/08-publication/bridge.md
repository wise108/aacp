# AACP Bridge Contract 1.0

**Status:** Normative  
**Layer:** Publication & Bridge  
**Depends on:** [publisher.md](publisher.md), [message-store-contract.md](message-store-contract.md), project binding / policy

## 1. Purpose

A Bridge adapts an **external caller** that cannot (or must not) run the Publisher directly into the Publisher → Message Store path.

```text
External caller
    ↓
Bridge
    ↓
Publisher
    ↓
Message Store
```

The Bridge is an integration/control-plane adapter. It is **not**:

- AACP Core;
- a transport profile;
- a Message Store;
- an Agent Runtime;
- proof of command acceptance or task completion.

## 2. When a Bridge is required

Use a Bridge when the caller:

- cannot execute the Publisher locally (example: ChatGPT GitHub connector without `workflow_dispatch` / without `tools/aacp`);
- must be constrained to a fixed target binding;
- must not invent `sequence` or write message files directly.

Direct Publisher use (CLI/library) is preferred when the environment can run it safely.

## 3. Bridge request

Minimal logical request:

```text
bridge_request_id
target_binding
envelope
metadata
```

| Field | Requirement |
|---|---|
| `bridge_request_id` | Stable idempotency key for **this bridge submission** (distinct from `message_id`, though they MAY be correlated). Retransmitted bridge submissions with the same id MUST not create duplicate logical publications. |
| `target_binding` | Reference to an authorized binding (project binding id / policy id / fixed configured target). MUST resolve to protocol, profile, canonical ref, conversation, stream, and identities. |
| `envelope` | AACP envelope without authoritative `sequence` |
| `metadata` | Optional non-authoritative diagnostics (actor, source system, correlation hints) |

## 4. Binding authority (critical)

The Bridge MUST derive from policy/binding — and MUST NOT allow the caller to freely set:

- authoritative `sequence`
- arbitrary repository
- arbitrary branch / canonical ref
- arbitrary `conversation_id`
- arbitrary `stream_id`

Callers MAY select among **pre-authorized** target bindings exposed by policy. They MUST NOT pass raw “publish anywhere” coordinates.

If the request attempts to override binding-controlled fields inside the envelope (`conversation_id` / `stream_id` inconsistent with binding), the Bridge MUST reject the request.

## 5. Bridge algorithm

1. Authenticate/authorize the external actor.
2. Validate `bridge_request_id` idempotency (replay protection).
3. Resolve and validate `target_binding`.
4. Validate envelope (schema/Core fields; strip/reject caller `sequence`).
5. Invoke `publish(envelope, target)`.
6. Persist/return `PublicationReceipt` to the caller surface as appropriate.
7. On CAS/transport conflict, rely on Publisher retry/reconcile; do not invent a new `message_id` or authoritative sequence in the Bridge.
8. On uncertain publication, ask Publisher/store reconciliation by `message_id` before retrying as a new attempt.

## 6. Idempotency and replay

| Event | Behavior |
|---|---|
| Same `bridge_request_id` replayed | Return prior outcome; do not create a second publication attempt that would mint a new message |
| Same `message_id` already published | Publisher idempotent success |
| New `bridge_request_id` with new `message_id` | New logical publication |
| New `bridge_request_id` with already-published `message_id` | Idempotent success via Publisher; Bridge SHOULD still record bridge-level replay metadata |

Bridge-level idempotency protects control-plane retries. Message-level idempotency remains keyed by `message_id`.

## 7. What Bridge success means

Bridge success + `PublicationReceipt.verified=true` means only that the AACP message is in the canonical Message Store.

It does **not** mean:

- peer agent discovered it;
- ACK `accepted`;
- execution started or finished;
- task `COMPLETED`.

## 8. Forbidden Bridge behaviors

- Writing directly into `.aacp/**/messages/` bypassing Publisher
- Inventing `envelope.sequence`
- Creating a second Message Store (issues, outbox-as-authority, registry-as-authority)
- Force-pushing canonical refs
- Treating workflow/issue closure as AACP task completion
- Widening target to caller-chosen repos/branches without policy

## 9. Concrete Bridge profiles

Profile documents MAY specialize this contract for a trigger surface, for example:

- GitHub Issue Bridge — [github-issue-bridge.md](github-issue-bridge.md)
- GitHub Actions `workflow_dispatch` Bridge (project-local; may remain an adoption profile)
- Future MCP/API Bridges

Each profile MUST preserve Publisher ownership of sequence and the single canonical Message Store.
