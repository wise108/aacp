# AACP Agent Adoption & Migration Protocol 1.0

## 1. Purpose

This document defines the procedure an AI agent MUST follow when adopting AACP in an existing project. It is designed so the same procedure can be used for Cursor, ChatGPT-driven project agents, or other cooperating agents.

AACP is the protocol contract. A project-specific prompt should point the agent to this document rather than reproducing protocol rules.

## 2. Authority and precedence

During adoption, the agent MUST treat the AACP repository as the protocol authority. The target project's existing IPC instructions are legacy material and MUST NOT override AACP semantics.

Product requirements and repository safety rules remain authoritative for the product itself. AACP governs inter-agent communication only.

## 3. Roles

Each participant MUST have an AACP identity and role for the conversation. Roles include at least `sender`, `receiver`, or `both`.

An agent MUST NOT infer that a Git author, GitHub account, branch name, or human name is an AACP identity unless the project explicitly binds it.

## 4. Adoption phases

Adoption is a state machine:

`DISCOVER → FREEZE → INVENTORY → PLAN → MIGRATE → VERIFY → CUTOVER → CLEANUP → OPERATE`

If verification fails, the agent MUST remain in the pre-cutover state and MUST NOT delete legacy data.

## 5. DISCOVER

The agent MUST:

1. Read the AACP Core specification and applicable transport profile.
2. Determine the available transport(s).
3. Inspect the target repository for existing inter-agent communication mechanisms.
4. Identify branches, directories, files, indexes, journals, task IDs, response IDs, and state stores used for agent communication.
5. Determine which artifacts are authoritative and which are merely indexes/caches.

The agent MUST NOT modify or delete legacy communication data during discovery.

## 6. FREEZE

Before migration, the agent MUST establish a communication freeze point. No new legacy IPC message may be created after the freeze point.

If another agent is concurrently operating on the legacy protocol and cannot be frozen, adoption MUST stop and report `MIGRATION_CONFLICT` rather than guessing.

## 7. INVENTORY

The agent MUST produce an inventory of all legacy communication records in one of these categories:

- completed and historical;
- pending;
- in progress;
- blocked;
- orphaned;
- duplicate;
- malformed;
- unknown/ambiguous.

Ambiguous records MUST NOT silently become completed AACP tasks.

## 8. PLAN

Before changing data, the agent MUST define a deterministic mapping from every migratable legacy record to an AACP identity.

The migration plan MUST state:

- source artifact;
- target AACP artifact;
- resulting `message_id`;
- task/state mapping;
- preservation of original timestamps/IDs where useful as metadata;
- handling of duplicates and orphans;
- validation criteria;
- rollback boundary.

A legacy identifier MAY be retained as `legacy_id` metadata, but it MUST NOT be confused with an AACP `message_id`.

## 9. MIGRATE

Migration MUST be additive first. Create the AACP representation before removing the legacy representation.

Migrated messages MUST preserve their semantic content. Migration MAY normalize formatting, filenames, or metadata, but MUST NOT change the intended command/result semantics.

Each migrated message MUST be immutable after publication.

Pending/in-flight work MUST remain pending/in-flight unless the inventory provides authoritative evidence that it completed.

## 10. VERIFY

Before cutover, the agent MUST verify:

1. every authoritative legacy message has a corresponding AACP record;
2. no AACP record has an unexplained source;
3. no task has been duplicated by migration;
4. pending/in-flight state is preserved;
5. message IDs are unique;
6. ordered streams have valid sequence information;
7. migrated artifacts validate against AACP schemas;
8. the selected transport can rediscover every migrated artifact;
9. recovery can reconcile interrupted publication without re-execution;
10. the two agents agree on the same migration boundary.

A migration is not successful merely because all files were copied.

## 11. CUTOVER

Cutover occurs only after verification succeeds.

At cutover:

- AACP becomes the sole authoritative inter-agent protocol.
- Agents MUST stop creating new legacy IPC records.
- New communication MUST use AACP message semantics.
- Legacy files become historical migration artifacts until cleanup is explicitly authorized.

The cutover point MUST be recorded in an AACP migration record.

## 12. CLEANUP

Legacy IPC MAY be deleted only after cutover and successful verification.

Deletion MUST be limited to artifacts proven to be obsolete. Product documentation or operational files that still have non-IPC meaning MUST NOT be deleted merely because they resemble legacy protocol files.

Cleanup SHOULD occur in a separate commit from the final migration publication where practical, making rollback and audit easier.

## 13. OPERATE

After cutover, agents MUST use only AACP for inter-agent communication.

Agents MUST NOT reintroduce ad-hoc mechanisms such as:

- shared mutable coordination files;
- hidden status conventions;
- commit messages as commands;
- branch movement as implicit ACK;
- timestamps as message ordering;
- undocumented side channels.

Human conversation may instruct an agent, but it is not itself an AACP transport unless explicitly bound as such.

## 14. Failure and recovery

If an agent crashes during migration, another agent MUST resume from the last durable migration state. It MUST not assume that an unobserved step completed.

If an AACP artifact exists remotely but local state says publication is pending, the agent MUST verify the artifact before retrying and MUST NOT execute the underlying task merely because publication acknowledgement was lost.

If migration verification fails, the system remains in legacy/pre-cutover mode and reports the exact blocking condition.

## 15. Conformance gate

An adopting implementation is AACP-compliant only when:

1. the applicable Core and transport specifications are identified;
2. the adoption procedure has completed through CUTOVER;
3. the implementation passes the applicable conformance suite;
4. the agent can recover after restart without duplicate side effects;
5. no active communication path bypasses AACP.

## 16. Agent completion report

At the end of adoption an agent SHOULD report a machine-readable summary containing:

- protocol version;
- transport profile;
- agent identity and role;
- migration source(s);
- migration boundary;
- number of messages migrated;
- pending/in-flight count;
- verification result;
- cleanup result;
- conformance result;
- AACP activation state.

## 17. Minimal adoption prompt

A project may invoke this protocol with a short instruction such as:

> Adopt AACP for all inter-agent communication in this repository. Read the AACP Agent Adoption & Migration Protocol at `https://github.com/wise108/aacp/blob/main/docs/07-agent-adoption/AACP-ADOPTION.md` and the applicable AACP Core/transport specifications. Inspect the repository, freeze and inventory the existing IPC, produce and execute a zero-loss migration, verify it, cut over to AACP, and remove obsolete IPC artifacts only after successful verification. From cutover onward, use only AACP for agent-to-agent communication. Do not modify product behavior merely for protocol adoption unless required by the migration plan.

The agent MUST read the referenced AACP documents; the prompt is not a substitute for the protocol specification.
