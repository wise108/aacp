# AACP Agent Adoption Prompt

Use the AACP protocol for all inter-agent communication in this repository.

AACP specification and normative agent procedures:
https://github.com/wise108/aacp

## Instructions

1. Read the AACP repository, including the Core specification, the applicable transport profile, `docs/07-agent-adoption/AACP-ADOPTION.md`, and `docs/07-agent-adoption/AACP-AGENT-RUNTIME.md`.
2. Inspect this repository before changing anything. Identify every existing mechanism used for communication with another AI agent or external coding agent, including markdown IPC, message journals, indexes, state files, issue/PR conventions, branch conventions, commit conventions, and other project-specific coordination mechanisms.
3. Determine the applicable AACP transport profile from the repository and available project infrastructure. Do not invent a project-specific protocol when an AACP profile applies.
4. Freeze legacy inter-agent communication before migration. Do not delete or rewrite legacy data before a verified migration plan exists.
5. Inventory all existing messages, pending work, responses, acknowledgements, task state, and in-flight operations. Preserve provenance and identity during migration.
6. Produce a concise migration plan and execute it according to the AACP Adoption & Migration Protocol. If migration cannot be completed safely, stop before destructive cleanup and report the blocking condition.
7. Verify migration for zero loss, duplicate safety, task-state consistency, and recoverability.
8. Perform cutover only after verification succeeds. Record that AACP is now the sole inter-agent protocol for this repository.
9. Remove obsolete IPC artifacts only after successful cutover and only when the adoption procedure permits their removal. Preserve any required migration/audit evidence.
10. After cutover, follow the AACP Agent Runtime Contract for every inter-agent command, ACK, result, progress event, error, retry, recovery, and protocol upgrade.
11. For retries, preserve the original logical `message_id`. Never execute a logical command twice merely because an ACK or transport response was lost.
12. Never infer message identity, ordering, completion, or state solely from Git commits, file timestamps, branch movement, chat prose, or repository search results.
13. If an AACP requirement conflicts with an existing project convention, AACP takes precedence for inter-agent communication. Product/build conventions remain unchanged unless the migration explicitly requires otherwise.
14. At the end of adoption, report: selected transport profile, migration scope, verification result, obsolete artifacts removed, and the exact AACP operating state now in effect.

## Operating rule

From successful cutover onward: **use AACP and only AACP for inter-agent communication.**
