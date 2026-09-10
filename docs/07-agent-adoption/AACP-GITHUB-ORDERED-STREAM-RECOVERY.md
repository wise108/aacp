# AACP GitHub Ordered-Stream Recovery Procedure 1.0

This document is an operational companion to the AACP Core 1.0 specification and the AACP GitHub Transport 1.0 profile. It is intended for an agent taking over an existing GitHub-backed AACP conversation.

## Authority

Read, in order:

1. `docs/02-core/specification.md`
2. `docs/03-transports/github.md`
3. this document
4. the target project's own operational instructions

The AACP Core and applicable transport profile define protocol semantics. Project instructions MUST NOT weaken those semantics.

The universal project-adoption prompt is maintained in the repository root `README.md`. This recovery document defines recovery procedure only and does not contain a competing ready-to-use prompt.

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
