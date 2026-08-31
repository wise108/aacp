# AACP GitHub Ordered-Stream Recovery Procedure 1.0

This document is an operational companion to the AACP Core 1.0 specification and the AACP GitHub Transport 1.0 profile. It is intended for an agent taking over an existing GitHub-backed AACP conversation.

## Authority

Read, in order:

1. `docs/02-core/specification.md`
2. `docs/03-transports/github.md`
3. this document
4. the target project's own operational instructions

The AACP Core and applicable transport profile define protocol semantics. Project instructions MUST NOT weaken those semantics.

## Recovery objective

Recover an existing ordered stream without rewriting history, losing messages, reusing allocated sequence values, or causing duplicate logical execution.

## Mandatory rules

The recovery agent MUST NOT:

- renumber historical messages;
- edit or delete immutable messages to repair ordering;
- invent a sequence from local state only;
- force-push a canonical ordered stream to bypass a stale writer;
- treat sequence as message identity;
- treat a missing ACK/RESULT as proof that execution did not happen;
- silently choose one side of a true ordering collision;
- create a parallel inter-agent communication protocol.

## Recovery procedure

### 1. Freeze affected stream

Stop ordered processing beyond the first unresolved ambiguity in the affected `(conversation_id, stream_id)`. Do not stop unrelated conversations or streams unless required by the project.

### 2. Establish canonical state

Read the canonical remote ref. Record its commit SHA/ref and timestamp. Re-read after any failed publication. Local branches, stale worktrees, caches, generated indexes, and previous agent memory are not authoritative.

### 3. Inventory

Enumerate all durable messages in the affected ordering domain. For every message record:

- `message_id`;
- `task_id`;
- `type`;
- `sequence`;
- `created_at`;
- `correlation_id` / `causation_id` when present;
- publication commit/ref.

Do not modify these records during inventory.

### 4. Classify

Classify the condition as exactly one of:

- duplicate/retransmission: same `message_id` and same sequence;
- true collision: different `message_id` values share a sequence;
- gap: no discovered record occupies an expected sequence;
- late/out-of-order discovery: a historical record is discovered after a higher sequence.

A gap MUST be checked against canonical remote state before it is accepted as real.

### 5. Reconcile a true collision

For a true collision:

1. preserve every conflicting message;
2. record all conflicting `message_id` values;
3. keep the affected position non-orderable;
4. do not execute either message merely because recovery discovered it;
5. determine application semantics outside the transport if a winner/supersession rule is required;
6. choose the next allocatable sequence as `max(sequence values in canonical ordering domain) + 1`;
7. publish a reconciliation record containing the domain, conflicting sequence, message IDs, canonical ref, classification, and chosen next sequence;
8. re-read canonical state;
9. resume only after reconciliation is durable and verified.

The transport MUST NOT decide which application message is semantically correct.

### 6. Recover a stale writer

If publication fails because the canonical ref advanced, discard the stale allocation attempt as a publication candidate. Do not force-push it. Re-read canonical state, allocate a new sequence, create a fresh publication attempt, and retry.

The original unsafely allocated message MUST NOT be silently republished under the new sequence if doing so would create a second logical message. Preserve its identity and decide whether it was actually published before retrying.

### 7. Recover after restart

After restart, rediscover durable records from canonical state. Reconstruct processing state using `message_id` for identity and sequence for ordering/discovery. Missing local state is not evidence that a message was never processed.

Before retrying a command whose publication or execution outcome is uncertain, reconcile durable task state and follow AACP Core recovery rules.

## Safe continuation invariant

After recovery, the stream MUST satisfy:

```text
all historical messages remain immutable
AND
no new message reuses an allocated sequence
AND
message identity is determined by message_id
AND
ordered processing does not cross an unresolved ambiguity
AND
next publication is based on canonical remote state
```

## Recovery completion report

The agent SHOULD publish or return an auditable report containing:

- recovery status;
- ordering domain;
- canonical ref/commit used;
- first ambiguous sequence, if any;
- conflicting message IDs, if any;
- classification;
- next allocatable sequence;
- reconciliation record identifier;
- whether ordered processing resumed;
- whether execution was performed, skipped, or remains uncertain;
- conformance checks performed.

## Ready-to-use prompt for the protocol-enabled assistant repository

```text
RECOVERY TASK — AACP GITHUB ORDERED STREAM

You are the protocol-enabled agent responsible for the repository:
https://github.com/wise108/vadim-baranov-assistant

This repository is configured to communicate according to AACP. Do NOT invent or introduce another communication protocol.

Canonical AACP protocol:
https://github.com/wise108/aacp

Read these documents BEFORE changing anything:
1. https://github.com/wise108/aacp/blob/main/docs/02-core/specification.md
2. https://github.com/wise108/aacp/blob/main/docs/03-transports/github.md
3. https://github.com/wise108/aacp/blob/main/docs/07-agent-adoption/AACP-GITHUB-ORDERED-STREAM-RECOVERY.md
4. The repository's own AACP/protocol instructions and relevant project governance documents.

Your task is to recover the existing AACP dialogue/transport state and then resume normal protocol-driven work. You are NOT being asked to modify AACP itself.

Recovery rules:
- Do not modify, delete, or renumber historical AACP messages.
- Do not force-push the canonical dialogue/transport branch.
- Do not invent sequence numbers from local state.
- Treat canonical remote state as authoritative.
- Use message_id for identity and deduplication; sequence is ordering metadata only.
- If two different message_ids occupy one sequence in the same (conversation_id, stream_id), classify it as ORDERING_CONFLICT, preserve both records, stop ordered processing beyond the ambiguity, and reconcile before continuing.
- Distinguish ORDERING_CONFLICT from SEQUENCE_GAP and stale publication.
- Do not execute an uncertain command merely because an ACK or RESULT is missing.
- Do not create a parallel protocol or bypass AACP.
- Do not modify the AACP specification during this recovery task.

Your first action is READ-ONLY DIAGNOSTICS. Determine:
1. how this repository is configured to consume/emit AACP messages;
2. the canonical remote transport/dialogue location and current commit/ref;
3. conversation_id and stream_id;
4. complete relevant ordered-stream history;
5. highest allocated sequence;
6. any duplicate, collision, gap, stale-writer, or out-of-order condition;
7. exact message_ids involved;
8. whether any task execution outcome is uncertain;
9. the last protocol message that was successfully processed and the first message that cannot be safely continued.

Do not modify anything during diagnostics.

If and only if reconciliation is required, perform the AACP GitHub Transport reconciliation procedure. Preserve immutable history. Determine the next safe sequence from canonical remote state. Record an auditable reconciliation record in the project's existing AACP-compatible transport location. Re-read and verify canonical remote state before resuming.

After recovery, resume the existing AACP dialogue. Do not reinterpret the original business/implementation task until the protocol state is known to be consistent.

When you make any change:
1. validate it;
2. run relevant tests/checks;
3. commit it;
4. push it to the canonical remote branch;
5. verify the remote ref/commit after push.

Every response/work result MUST be pushed through the repository's established AACP transport mechanism. Do not leave the authoritative result only in the local worktree.

Final report MUST include:
- recovery status;
- canonical commit/ref before and after recovery;
- conversation_id / stream_id;
- sequence findings;
- message IDs involved;
- reconciliation performed or explicit "not required";
- next safe sequence;
- last safely processed message;
- first blocked/uncertain message;
- execution/retry safety assessment;
- commit SHA and push verification.
```

The prompt is an operational invocation of this procedure for `vadim-baranov-assistant`. It is not a replacement for the normative AACP specifications.