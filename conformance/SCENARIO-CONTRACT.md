# AACP Conformance Scenario Contract 1.0

Each mandatory scenario MUST be representable by a deterministic fixture with these fields:

```yaml
id: S01
initial_state: {}
fault_schedule: []
actions: []
expected:
  task_state: COMPLETED
  execution_attempts: 1
  side_effects: 1
  publication: PUBLISHED
  protocol_errors: []
```

## Semantics

`initial_state` defines only durable state that exists before the scenario.

`fault_schedule` defines deterministic faults and their exact injection points.

`actions` are externally observable protocol operations such as send, deliver, recover, cancel, or retry publication.

`expected` defines invariants, not implementation-specific internal details.

## Oracle rules

1. `side_effects` counts externally observable non-idempotent effects.
2. `execution_attempts` counts actual task execution attempts, not message retries.
3. A message publication retry MUST NOT increase `execution_attempts`.
4. A result publication retry MUST NOT increase `execution_attempts`.
5. A duplicate command MUST NOT increase `side_effects`.
6. `STATE_CONFLICT` MUST leave the losing writer's target state unapplied.
7. Recovery MAY be repeated; repeated recovery MUST preserve all safety invariants.
8. Expected final state MUST be checked after all scheduled recovery steps have completed.

## Scenario independence

Each scenario starts from a clean fixture. Scenarios MUST NOT depend on execution order or state left by another scenario.

## Production applicability

A production implementation MAY adapt the fixture mechanics to its storage and transport, but it MUST preserve the same observable fault and oracle semantics. An implementation that cannot demonstrate an equivalent scenario is not conformant merely because its architecture is different.
