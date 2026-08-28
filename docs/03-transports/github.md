# AACP GitHub Transport 1.0

This document defines the GitHub-specific profile for AACP. It is not part of AACP Core semantics.

## Repository layout

Recommended layout:

```text
.aacp/
├── protocol.yaml
├── tasks/
├── messages/
└── results/
```

`protocol.yaml` declares the project profile and protocol version. Task, message and result records are durable protocol state.

## Publication

For Git-backed implementations the minimum publication sequence is:

```text
write valid records
  ↓
create commit
  ↓
push to remote ref
  ↓
verify remote ref/commit
  ↓
publication.status = PUBLISHED
```

A local commit is not publication. A successful local `git push` SHOULD be followed by verification when the transport can perform it.

## Atomicity

When practical, related task/result/publication records SHOULD be committed together. Git commit history then provides a durable recovery point without requiring a separate event store.

## Concurrency

Implementations SHOULD use compare-and-swap semantics based on the current remote file/blob/tree version, or an equivalent Git reference update strategy. A stale writer MUST NOT silently overwrite newer protocol state.

## Recovery

After restart or transport interruption, the implementation MUST inspect durable records and reconcile unacknowledged messages, pending messages, in-progress tasks, completed results with pending publication, and publication claims against the remote ref.

## Separation from execution

GitHub transport does not execute tasks. Cursor ACP, MCP, shell commands, LLM calls, and application logic remain outside this transport profile.
