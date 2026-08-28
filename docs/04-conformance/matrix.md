# AACP Core 1.0 Conformance Matrix

This matrix maps normative Core requirements to observable tests. `MUST` and `MUST NOT` requirements are mandatory for Core conformance. `SHOULD` requirements are tested as recommended behavior and may be waived only with documented rationale.

| ID | Core requirement | Test | Expected result |
|---|---|---|---|
| ENV-01 | Required envelope fields MUST exist | Submit envelope missing each required field | `INVALID_MESSAGE`; no processing |
| ENV-02 | Protocol/version MUST be recognized | Submit wrong protocol/version | `INVALID_MESSAGE` or `UNSUPPORTED_VERSION`; no processing |
| ENV-03 | Message ID MUST be unique | Submit two distinct commands with same `message_id` | Second is treated as duplicate; no second side effect |
| ORD-01 | Sequence starts at 1 | Submit first stream message with sequence 0 | Rejected |
| ORD-02 | Ordered sequence increments by exactly 1 | Submit N then N+2 | `SEQUENCE_GAP`; N+2 not processed under strict ordering |
| ORD-03 | Streams are scoped by conversation/sender/recipient | Send same sequence on two distinct streams | Both accepted independently |
| ORD-04 | Unordered stream may process without barrier | Declare unordered stream and send N+1 before N | N+1 may process; sequence remains observable evidence |
| DEL-01 | Core delivery is at-least-once | Drop first ACK and retransmit command | Retransmission accepted for delivery semantics |
| DEL-02 | Duplicate command MUST NOT repeat side effect when idempotency is claimed | Deliver identical command twice | Side effect occurs once |
| DEL-03 | Crash recovery must not blindly rerun uncertain execution | Execute side effect, crash before processing record, retransmit | Recovery reconciles idempotently; no known duplicate side effect |
| ACK-01 | Command receipt produces ACK | Deliver valid command | ACK `received` after durable acceptance |
| ACK-02 | Invalid command is rejected | Deliver malformed/unauthorized command | ACK `rejected` plus reason/error |
| ACK-03 | Duplicate is distinguished | Deliver already accepted message | ACK `duplicate`; no execution |
| TASK-01 | Task statuses are constrained | Attempt unknown status | Rejected |
| TASK-02 | Invalid transition is rejected | Attempt terminal → IN_PROGRESS | `INVALID_STATE_TRANSITION`; state unchanged |
| TASK-03 | State version increments on accepted mutation | Perform valid transition | Version increments exactly once |
| CAS-01 | Stale mutation MUST fail | Two writers use same expected version | Exactly one succeeds; other gets `STATE_CONFLICT` |
| CAS-02 | Stale writer MUST NOT overwrite newer state | Repeat stale mutation after winner commits | Stored state remains winner's state |
| RES-01 | Completion has result or error | Complete task | Corresponding result/error is durable |
| RES-02 | Result is not publication | Complete task without transport publication | Task may be completed while publication remains pending |
| PUB-01 | Published requires remote verification where supported | Mark PUBLISHED before remote verification | Implementation must reject/defer status |
| PUB-02 | Crash after remote publication is recoverable | Push artifact, crash before local status update | Recovery verifies remote artifact and marks PUBLISHED |
| PUB-03 | Publication recovery MUST NOT execute task | Recover PUB-PENDING result | Only publication state changes; task execution count unchanged |
| REC-01 | Durable recovery is required | Restart with pending/unacknowledged messages | State reconstructed and messages reconciled |
| REC-02 | Lost ACK/RESULT must not trigger re-execution | Lose ACK/RESULT then retry | No duplicate side effect |
| REC-03 | In-progress stale heartbeat is recoverable | Stop worker until heartbeat stale | Recovery identifies task as candidate without inventing `STALE` task status |
| CAN-01 | Cancellation uses optimistic concurrency | Cancel with stale version | `STATE_CONFLICT`; state unchanged |
| CAN-02 | Terminal task cannot be cancelled | Cancel COMPLETED/FAILED/CANCELLED | Terminal state unchanged; authoritative state returned |
| CAN-03 | Completion/cancel race has deterministic winner | Race two valid mutations from same version | First committed transition wins; other gets `STATE_CONFLICT` |
| ERR-01 | Error has stable code/retryability | Trigger known protocol error | Code and `retryable` are present |
| EVID-01 | Prose is not evidence | Agent says “pushed” without publication record | Publication remains unverified |
| EXT-01 | Extensions cannot redefine Core | Add extension field | Core semantics unchanged |

## Required scenario set

The matrix must be exercised with the scenarios in `scenarios.md`. Implementations SHOULD additionally run the tests against process crashes and transport outages, not only simulated exceptions.

## Conformance result

An implementation is **AACP Core 1.0 conformant** only when all mandatory rows pass and no implementation-specific exception changes Core semantics.
