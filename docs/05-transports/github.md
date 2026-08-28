# AACP GitHub Transport Profile 1.0

## Status

This document defines the GitHub transport profile for AACP Core 1.0. GitHub is a publication and synchronization transport, not the source of protocol truth.

## 1. Principle

AACP messages and durable state are authoritative according to the AACP implementation. Git commits, branches, files, issues, and pull requests are transport artifacts and MUST NOT silently redefine AACP state.

## 2. Message publication

A message MUST be published as an immutable artifact identified by its `message_id`. A retry MUST NOT overwrite a different message or create a new identity for the same logical message.

The preferred representation is one file per message under a dedicated protocol namespace, for example:

`aapc/messages/<conversation_id>/<sequence>-<message_id>.json`

Implementations MAY use another layout, but the mapping from AACP message identity to GitHub artifact MUST be deterministic.

## 3. State publication

Current task state MAY be materialized in a separate state artifact. State artifacts are snapshots/materializations, not replacements for message identity. Concurrent state updates MUST use AACP `state_version` semantics before publication.

## 4. Polling and discovery

A receiver MUST NOT infer protocol completion merely from repository activity, commit count, branch movement, or the latest modified file. It MUST discover and validate AACP message artifacts.

The receiver SHOULD use an explicit protocol index or deterministic message path so that polling does not depend on GitHub search/indexing latency.

## 5. Push acknowledgement

A successful GitHub write is transport evidence that the artifact was accepted by GitHub. It is not by itself an AACP ACK unless the implementation has durably recorded the corresponding local processing/publication state according to Core semantics.

## 6. Idempotent publication

Publication MUST be safe to retry. If the target artifact already exists, the implementation MUST verify that its contents correspond to the same `message_id` and semantic payload before treating the operation as successful. A content mismatch MUST be a conflict, not an overwrite.

## 7. Commit semantics

A Git commit is a transport envelope for one or more artifacts. Commit SHA is evidence of a specific repository state, but it is not an AACP message ID. A commit MAY contain multiple AACP messages.

## 8. Ordering

Git commit order MUST NOT be used as the sole AACP sequence source. AACP sequence belongs to the logical stream defined by Core. A receiver MUST validate message sequence independently.

## 9. Repository failures

GitHub API errors, branch protection failures, rate limits, indexing delays, merge conflicts, and temporary unavailability MUST be represented as transport failures. They MUST NOT mutate the logical Task outcome unless the task itself explicitly concerns the failed transport operation.

## 10. Recovery

After restart, the implementation MUST reconcile local publication state against deterministic GitHub artifacts. If a remote artifact exists but local publication state is pending, the implementation MUST verify the artifact and reconcile to `PUBLISHED` without re-executing the task.

## 11. Security

Repositories used as AACP transport SHOULD be private when messages contain confidential project data. Tokens MUST NOT be stored in protocol artifacts, commits, logs, or message payloads.

## 12. Non-goals

This profile does not define a GitHub-specific task workflow, branch naming convention for source-code work, PR review policy, or human approval process. Those belong to the consuming project.
