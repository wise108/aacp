# AACP GitHub Message Store 1.0

This document defines the concrete repository layout and algorithms used by the GitHub Transport Profile.

## 1. Repository layout

```text
.aacp/
  protocol.json
  conversations/
    <conversation_id>/
      messages/
        000001-M-<id>.json
        000002-M-<id>.json
      state/
        <task_id>.json
      publications/
        <result_id>.json
```

The `.aacp/` namespace is reserved for protocol artifacts.

## 2. Immutable messages

A message file is immutable after publication. Its filename contains the stream sequence and `message_id`. The JSON body MUST contain the same sequence and message ID. A receiver MUST reject an artifact whose filename and body disagree.

A message MUST NOT be edited in place. Corrections or follow-up information are new AACP messages with new message IDs.

## 3. Protocol discovery

`.aacp/protocol.json` identifies the repository as an AACP transport endpoint and declares the supported Core/profile version. Receivers SHOULD first read this small deterministic artifact, then enumerate the conversation message directory rather than relying on repository-wide search.

## 4. Atomic publication

GitHub Contents API writes are not treated as a distributed transaction. The publisher first prepares the exact immutable message content, then attempts to create the deterministic path.

If creation succeeds, the resulting commit SHA is transport evidence. If creation reports that the path already exists, the publisher MUST read the existing artifact and compare its canonical semantic content with the intended message. Equal content means idempotent success; different content means `PUBLICATION_CONFLICT`.

## 5. Concurrent writers

Two writers MAY race to publish different messages. They MUST use different deterministic paths because message identity is part of the path. A writer MUST NOT solve a collision by overwriting another message.

State snapshots are different: they are mutable materializations and MUST be guarded by AACP `state_version`. A stale snapshot MUST NOT overwrite a newer version.

## 6. Indexing

An implementation MAY maintain an index for efficient polling, but the index is a cache/materialization. Loss or staleness of the index MUST NOT make published immutable messages unreachable to a recovery procedure.

The canonical recovery source is the deterministic message directory.

## 7. Polling

A receiver maintains its last durably processed sequence per ordered stream. On each poll it reads messages after that sequence, validates each artifact, detects gaps, and processes them according to Core ordering semantics.

Polling MUST be safe to repeat. A previously seen message ID is handled as a duplicate according to Core semantics.

## 8. Commit grouping

An implementation MAY publish several independent messages in one Git commit using the Git Data API. Each message remains individually identifiable by its immutable path and `message_id`.

The commit is not the logical transaction boundary of AACP. Partial visibility or retry MUST be handled at the message-artifact level.

## 9. State CAS

A state materialization contains at least `task_id` and `state_version`. Before replacing it, the publisher MUST have validated that the expected version is still current. Implementations using the GitHub Contents API SHOULD use the current blob SHA as an additional write guard. A failed SHA update is a transport conflict and MUST trigger re-read/reconciliation rather than blind overwrite.

## 10. Publication records

A publication record SHOULD contain `result_id`, target artifact path, publication status, and transport evidence such as commit SHA. If the process crashes after the remote write, recovery searches for the deterministic artifact and verifies its content before marking publication `PUBLISHED`.

## 11. Recovery algorithm

On startup:

1. Load durable local publication/processing state.
2. Discover configured conversations.
3. Re-read deterministic message paths relevant to unacknowledged or pending work.
4. Reconcile duplicate messages by `message_id`.
5. Detect and report sequence gaps.
6. Reconcile completed results with remote publication artifacts.
7. Resume retryable publication failures.
8. Never re-execute a task merely because a transport response was lost.

## 12. GitHub-specific failure mapping

The transport SHOULD normalize failures into stable categories:

- authentication/authorization → `TRANSPORT_AUTH`
- rate limit → `TRANSPORT_RATE_LIMIT` (retryable)
- timeout/network failure → `TRANSPORT_UNAVAILABLE` (retryable)
- branch/rules conflict → `TRANSPORT_CONFLICT`
- existing path with different content → `PUBLICATION_CONFLICT`
- malformed remote artifact → `PROTOCOL_INVALID`

The exact GitHub HTTP status or API message MUST remain diagnostic detail, not the application's logical error code.
