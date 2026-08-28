# AACP 1.0 Conformance Scenarios

Mandatory reliability scenarios:

| ID | Scenario | Expected invariant |
|---|---|---|
| C-01 | Duplicate delivery | A command side effect occurs at most once when the implementation claims command idempotency. |
| C-02 | Sequence gap | A strict ordered stream does not silently process a later message while an earlier sequence is missing. |
| C-03 | State conflict | Concurrent mutation cannot overwrite newer state. |
| C-04 | Crash before publication | Completed work is not re-executed; pending publication remains recoverable. |
| C-05 | Crash after remote push | Recovery verifies the remote artifact and marks publication `PUBLISHED`; task is not re-executed. |
| C-06 | Lost ACK | Retransmission remains safe under at-least-once delivery and idempotent processing. |
| C-07 | Worker crash | Stale heartbeat is identified as a recovery condition without inventing a `STALE` task status. |
| C-08 | Invalid transition | State remains unchanged and the mutation is rejected. |
| C-09 | Transport outage | Completed task survives and publication remains/reverts to retryable pending state. |
| C-10 | Restart recovery | Durable state reconciles without duplicate execution. |
| C-11 | Cancel race | Optimistic concurrency determines one committed outcome; stale mutation loses with `STATE_CONFLICT`. |
| C-12 | False completion claim | Prose is not evidence of publication. |
| C-13 | Version increment | Every accepted task mutation changes `state_version` exactly N → N+1. |
| C-14 | Unordered stream | An explicitly unordered stream can process messages without a sequence barrier. |
| C-15 | Extension isolation | Namespaced extensions do not alter Core semantics. |

The scenarios are linked to the detailed [Conformance Matrix](matrix.md), which provides the requirement-to-test traceability.

See [requirements.md](requirements.md) for the conformance claim requirements.
