# AACP Core 1.0 Conformance Matrix

This matrix maps the six minimum Core conformance properties to observable tests. Transport profiles may add their own tests, but they MUST NOT redefine Core semantics.

| ID | Core property | Observable test | Expected result |
|---|---|---|---|
| CORE-01 | Immutable unique message identity | Deliver two messages with distinct IDs and retransmit one with the same ID | Identity remains stable; retransmission is the same message |
| CORE-02 | Safe duplicate command handling | Deliver the same command twice with the same `message_id` | Second delivery is `duplicate`; no second logical execution |
| CORE-03 | ACK semantics | Process valid, invalid and already-processed commands | ACK is respectively `accepted`, `rejected`, or `duplicate`; ACK never means completion |
| CORE-04 | Valid task lifecycle | Attempt valid and invalid task transitions | Valid transitions succeed; invalid transitions are rejected; terminal states remain terminal |
| CORE-05 | No stale state overwrite | Two writers mutate the same task version | One commit wins; stale mutation receives `STATE_CONFLICT` and cannot overwrite newer state |
| CORE-06 | Safe recovery after uncertain execution | Execute, lose acknowledgement/result, restart and retry | Recovery reconciles durable state and does not blindly repeat uncertain side effects |

## Recommended extended tests

Implementations SHOULD additionally test transport loss, duplicate delivery, crash points, ordering where a transport profile defines ordering, cancellation races, schema validation and extension isolation.

These tests are useful engineering coverage, but they are not additional Core semantics unless promoted into a future AACP specification.

## Conformance result

An implementation may claim **AACP Core 1.0 conformance** only when all six Core properties pass and no implementation-specific exception changes Core semantics.
