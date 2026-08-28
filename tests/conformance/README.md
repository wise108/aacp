# AACP Core 1.0 Conformance Harness

This directory defines the transport-neutral conformance harness contract.

The harness tests an implementation through an adapter rather than talking directly to GitHub, Cursor, MCP, or any other transport.

## Adapter contract

An implementation adapter MUST expose operations equivalent to:

- `reset()` — create a clean isolated test state.
- `deliver(message)` — deliver one AACP message, allowing duplicate/reordered delivery.
- `restart()` — simulate process termination and recovery.
- `state(task_id)` — return authoritative task state, state version, result and publication state.
- `side_effect_count(key)` — return observable side-effect count for the test fixture.
- `remote_artifact(id)` — inspect the transport's remote publication fixture.
- `advance_time()` — advance the test clock where heartbeat/retry timing is required.

The adapter MUST make test state deterministic and MUST NOT hide duplicate execution.

## Test policy

Each scenario in `docs/04-conformance/scenarios.md` maps to one or more executable tests. Tests MUST assert protocol invariants, not implementation-specific storage details.

The first harness implementation uses Python/pytest. No transport dependency belongs in Core tests.
