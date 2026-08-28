# AACP 1.0 Conformance Harness

This directory defines the reference test harness for AACP Core 1.0.

The harness is intentionally small and transport-neutral. It is not an agent runtime and it is not a production message broker.

## Purpose

The harness provides a deterministic way to prove the protocol's failure semantics before integrating AACP into a real agent.

It models four components:

```text
Test Controller
      │
      ├── Agent A (sender)
      │
      ├── Fault-Injection Transport
      │
      ├── Agent B (receiver)
      │
      └── Durable Test Store
```

The transport can inject:

- message loss;
- duplicate delivery;
- reordering;
- delayed delivery;
- crash/restart at defined points;
- publication failure;
- concurrent state races;
- timeout.

## Required properties

The harness MUST be deterministic: a scenario is defined by a fixed initial state, message sequence, fault schedule, and expected invariants.

The harness MUST distinguish:

- message publication retry;
- task execution retry;
- result publication retry.

These are different operations and MUST NOT be collapsed into one generic `retry()`.

## Evidence model

Every scenario produces an evidence record containing at least:

- scenario ID;
- pass/fail;
- final task state;
- final `state_version`;
- observed message IDs;
- execution-attempt count;
- side-effect count;
- publication state;
- detected protocol errors;
- recovery count;
- deterministic fault schedule.

A scenario passes only when both the final state and side-effect count satisfy its invariant.

## Fault model

Faults are injected at protocol boundaries, not randomly. The canonical points are:

```text
SEND_BEFORE
SEND_AFTER
RECEIVE_BEFORE
RECEIVE_AFTER
ACCEPT_BEFORE
ACCEPT_AFTER
EXECUTE_BEFORE
SIDE_EFFECT_AFTER
RESULT_BEFORE
RESULT_AFTER
PUBLISH_BEFORE
PUBLISH_AFTER
STATE_COMMIT_BEFORE
STATE_COMMIT_AFTER
RECOVERY_BEFORE
RECOVERY_AFTER
```

A crash at a boundary means process state after the boundary is exactly defined by the scenario. This prevents tests from relying on timing luck.

## Reference side effect

The harness SHOULD use a deliberately non-idempotent counter-like side effect as its primary safety oracle. A duplicate execution increments the counter twice and therefore cannot be hidden by a superficially identical result.

## Minimal implementation layout

```text
conformance/
├── README.md
├── scenarios/
│   └── S01-S20.md
├── fixtures/
├── harness/
├── evidence/
└── report/
```

The first implementation may use an in-memory deterministic transport and durable test store backed by the host process. A later transport profile can reuse the same scenario contract.

## Exit criterion

The harness is considered operational only when S01–S20 have executable tests and produce machine-readable evidence. A green test suite is necessary but does not by itself make a production agent conformant; the production implementation must run the same mandatory scenarios against its own runtime.
