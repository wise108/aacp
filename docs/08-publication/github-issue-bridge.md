# AACP GitHub Issue Bridge Profile 1.0

**Status:** Normative profile proposal (specification only; production workflows not required by this document)  
**Layer:** Publication & Bridge  
**Depends on:** [bridge.md](bridge.md), [publisher.md](publisher.md), [message-store-contract.md](message-store-contract.md)

## 1. Purpose

Define how a GitHub Issue can act as a **control-plane trigger** for AACP publication when an external caller (notably ChatGPT GitHub connector) can create Issues but cannot reliably invoke `workflow_dispatch` or run `tools/aacp` locally.

```text
ChatGPT (or other authorized actor)
  ↓
GitHub Issue
  ↓
issues.opened  (GitHub Actions / project-local bridge workflow)
  ↓
project-local bridge adapter
  ↓
AACP reusable Publisher
  ↓
canonical Message Store
```

## 2. Critical boundary

```text
GitHub Issue  ≠  AACP Message Store
Issue body    ≠  durable ordered-stream history
Issue closed  ≠  command accepted / executed / completed
```

The Issue is only a trigger + audit surface for the Bridge request. Authoritative AACP history remains the transport Message Store (`.aacp/conversations/.../messages/` on the canonical ref).

## 3. Exact trigger

Recommended trigger:

```text
on:
  issues:
    types: [opened]
```

Optional hardening (profile MAY require):

- label gate (e.g. `aacp-publish`) present at open time, or added later via `labeled` with the same validation path;
- title prefix gate (e.g. `AACP_PUBLISH:`);
- ignore edits that attempt to change an already-accepted bridge payload after `PUBLISHING` started (treat as new request only if policy explicitly allows and a new `bridge_request_id` is minted).

`issue_comment` MAY be used for operator commands (`/aacp reconcile`) but SHOULD NOT be the primary publish trigger unless the profile defines equivalent validation.

## 4. Actor authorization

The bridge workflow MUST authorize the Issue author (GitHub actor) against an allowlist or policy binding, for example:

- specific GitHub users/apps permitted to submit AACP publish Issues;
- membership in a configured team;
- GitHub App installation identity.

Unauthorized actors → mark Issue `INVALID` and close (see lifecycle). Do not publish.

Authorization of the GitHub actor is **not** AACP identity. AACP `sender` / `recipient` come from the envelope + project binding, not from the GitHub login alone.

## 5. Repository authorization

The workflow MUST run only in the repository that owns the target project binding (or a explicitly delegated bridge repository configured to publish into that binding).

The Issue MUST NOT be allowed to select an arbitrary destination repository/ref. Destination is fixed by project binding / workflow configuration.

## 6. Title / label validation

Before parsing the envelope, validate control-plane markers:

| Check | Failure |
|---|---|
| Required title pattern / prefix | `INVALID` |
| Required label(s) | `INVALID` |
| Missing/malformed payload section | `INVALID` |
| Envelope not JSON / schema fail | `INVALID` |

## 7. Envelope validation

Extract envelope from a dedicated Issue section (fenced JSON or attached artifact). Validate:

- Core required fields present;
- `message_id` present and well-formed;
- no authoritative caller `sequence` (strip/reject if present);
- `conversation_id` / `stream_id` / identities match target binding;
- payload size within configured limits.

## 8. Target binding validation

Resolve the project binding (from workflow config / `.aacp/protocol.json` on the canonical ref, depending on adoption). Confirm:

- protocol/version/distribution;
- transport profile;
- canonical ref;
- conversation/stream;
- that this bridge profile is enabled.

Mismatch → `INVALID`.

## 9. Replay / idempotency protection

Use at least one of:

- `bridge_request_id` embedded in the Issue (recommended: hash of normalized envelope + binding, or explicit field);
- GitHub `issue.id` / `issue.node_id` as bridge submission id when one Issue maps to one publish attempt;
- Publisher-level `message_id` idempotency as the ultimate store guard.

Re-running the workflow for the same Issue MUST NOT create a second message with a new `message_id`/`sequence` if publication already succeeded.

Recommended durable mapping:

```text
issue_id → bridge_request_id → message_id → PublicationReceipt
```

## 10. No caller-controlled sequence

The Issue payload MUST NOT control authoritative `sequence`. Sequence allocation happens only inside the Publisher CAS loop.

## 11. Publication verification

After Publisher returns, the bridge MUST require `PublicationReceipt.verified == true` and SHOULD comment the receipt summary on the Issue (`message_id`, `sequence`, `publication_commit`, `target_ref`).

## 12. CAS conflict handling

```text
PUBLISHING
  → RECONCILE
  → RETRY
```

CAS/`head_moved` conflicts are normal under multi-writer conditions. The bridge MUST allow Publisher retry/reread behavior and MUST NOT force-push.

## 13. Uncertain publication handling

```text
PUBLISHING
  → RECONCILE
  → PUBLISHED | RETRY
```

If the Publisher/store outcome is unknown:

1. Reconcile canonical Message Store by `message_id`.
2. If present → `PUBLISHED` with existing receipt.
3. If proven absent → `RETRY` publish with same `message_id`.
4. Never mint a new `message_id` solely due to uncertainty.

## 14. Issue lifecycle model

### Happy path

```text
OPEN
→ VALIDATING
→ PUBLISHING
→ PUBLISHED
→ CLOSED
```

### Invalid request

```text
OPEN
→ INVALID
→ CLOSED
```

### CAS conflict / contention

```text
PUBLISHING
→ RECONCILE
→ RETRY
→ PUBLISHING | PUBLISHED
```

### Uncertain publication

```text
PUBLISHING
→ RECONCILE
→ PUBLISHED | RETRY
```

Lifecycle labels/comments are **bridge control-plane state**. They are not AACP Core task states and MUST NOT replace ACK/result messages.

## 15. Closing an Issue

Closing after `PUBLISHED` means only: the bridge finished the publication attempt successfully.

Closing MUST NOT be treated as evidence that:

- a peer accepted the command;
- execution occurred;
- a result exists;
- the AACP task is `COMPLETED`.

## 16. Failure mapping (informative)

| Condition | Issue state | Publish? |
|---|---|---|
| Unauthorized actor | `INVALID` → `CLOSED` | No |
| Bad title/label/JSON | `INVALID` → `CLOSED` | No |
| Binding mismatch | `INVALID` → `CLOSED` | No |
| CAS conflict | `RECONCILE`/`RETRY` | Retry via Publisher |
| Uncertain write | `RECONCILE` | Reconcile first |
| Verified publish | `PUBLISHED` → `CLOSED` | Done |

## 17. Non-goals of this profile

- Replacing `workflow_dispatch` Bridges where they are available
- Storing authoritative envelopes only in Issues
- Implementing production workflows in the AACP canonical repo as part of this specification phase
- Changing GitHub Transport or Core

## 18. Implementation note (non-normative)

Project-local workflow code may live in adopting repositories. Canonical reusable Publisher/Message Store implementations belong to later AACP implementation phases. This document freezes the **contract**, not the workflow YAML.
