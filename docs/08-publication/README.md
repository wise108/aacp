# AACP Publication & Bridge Layer

**Status:** Normative specification (Phase 1)  
**Distribution context:** AACP 1.1.0-rc.3 / Core 1.0  
**Scope:** Publication mechanics and external publication bridges over an already-selected transport profile

## Purpose

This directory defines the **Publication & Bridge Layer**: how an AACP participant or external caller durably publishes a validated envelope into the canonical Message Store without inventing a second protocol, transport, or store.

It does **not** redefine:

- AACP Core (`docs/02-core/`)
- GitHub Transport / Message Store layout (`docs/03-transports/`, `docs/05-transports/`)
- Agent Runtime execution semantics (`docs/07-agent-adoption/`)
- Conformance matrices (`docs/04-conformance/`)

## Documents

| Document | Normative subject |
|---|---|
| [publisher.md](publisher.md) | Publisher contract, sequence allocation, CAS loop, `PublicationReceipt` |
| [message-store-contract.md](message-store-contract.md) | Abstract Message Store API; Git and GitHub API as backends |
| [bridge.md](bridge.md) | Bridge request contract between external callers and Publisher |
| [github-issue-bridge.md](github-issue-bridge.md) | GitHub Issue as control-plane trigger (not a Message Store) |

## Layering

```text
AACP Core
  ↓
Transport profile (e.g. GitHub Transport 1.0 / github-message-store-1.0)
  ↓
Publication & Bridge Layer  ← this directory
  ↓
Message Store backends (Git CLI, Git Data API, …)
```

```text
External caller (ChatGPT connector, CI, human tool, …)
  ↓
Bridge (optional)
  ↓
Publisher
  ↓
Message Store
```

## Non-goals (Phase 1 normative docs)

- Changing Core or transport semantics
- Creating a second Message Store
- Making Registry/orchestration stores authoritative for AACP messages
- Allowing callers to supply an authoritative `sequence`
- Deleting project-local legacy publishers

## Implementation status

- **Phase 2A (skeleton):** `src/aacp/publisher/` + `src/aacp/message_store/` with in-memory test store and tests under `tests/publisher/` and `tests/message_store/`.
- **Phase 2B (not started):** Git / GitHub API production adapters.
- **Bridge production:** not started.

## Authority

Where this layer and Core/Transport overlap, Core and the applicable transport profile remain authoritative for message semantics and ordered-stream rules. This layer specifies **how** publication is performed safely.

## Numbering note

`docs/08-publication/` coexists with `docs/08-release/`. The `08-` prefix is documentary grouping only and does not imply release packaging of this layer.
