# AACP 1.0 Conformance Scenarios

Mandatory reliability scenarios:

1. Duplicate delivery — command executes at most once.
2. Sequence gap — later message is not silently processed.
3. State conflict — concurrent mutation cannot overwrite newer state.
4. Crash before publication — completed work is not re-executed.
5. Crash after remote push — recovery verifies and marks publication.
6. Lost ACK — retransmission remains idempotent.
7. Worker crash — stale heartbeat is recoverable.
8. Invalid transition — state remains unchanged.
9. Transport outage — completed task survives and publication retries.
10. Restart recovery — durable state reconciles without duplicate execution.
11. Cancel race — optimistic concurrency resolves the race safely.
12. False completion claim — prose is not evidence of publication.

See [requirements.md](requirements.md) for the conformance claim requirements.