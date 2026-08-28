# AACP Core 1.0 Conformance Matrix

This matrix provides traceability from normative Core requirements to observable tests. `MUST` and `MUST NOT` requirements are mandatory for Core conformance. `SHOULD` and `SHOULD NOT` requirements are recommended; deviations MUST be documented.

| ID | Spec | Requirement | Test | Expected result |
|---|---|---|---|---|
| ENV-01 | §5 | Required envelope fields MUST exist | Submit envelope missing each required field | `INVALID_MESSAGE`; no processing |
| ENV-02 | §5 | Protocol/version MUST be recognized | Submit wrong protocol/version | `INVALID_MESSAGE` or `UNSUPPORTED_VERSION`; no processing |
| ENV-03 | §4, §7 | `message_id` identifies a message and is its idempotency key | Deliver same command twice with same `message_id` | Second delivery is duplicate; no second side effect |
| ORD-01 | §6 | Ordered stream sequence starts at 1 | Submit first stream message with sequence 0 | Rejected |
| ORD-02 | §6 | Ordered sequence increments exactly by 1 | Submit N then N+2 | `SEQUENCE_GAP`; N+2 not processed under strict ordering |
| ORD-03 | §6 | Stream scope is `(conversation_id, sender, recipient)` | Send same sequence on two distinct streams | Both accepted independently |
| ORD-04 | §6 | Unordered streams MAY process without barrier | Declare unordered stream and send N+1 before N | N+1 may process; sequence remains evidence |
| DEL-01 | §7 | Core delivery is at-least-once | Drop first ACK and retransmit command | Retransmission is permitted and safely handled |
| DEL-02 | §7 | Duplicate command MUST NOT repeat side effect when idempotency is claimed | Deliver identical command twice | Side effect occurs once |
| DEL-03 | §7 | Uncertain execution MUST NOT be blindly rerun | Execute independently idempotent side effect, crash before processing record, retransmit | Recovery reconciles without duplicate effect |
| DEL-04 | §7 | Durable processing state can provide crash-safe duplicate suppression | Process command with durable record and interrupt at defined crash points | Recovery does not execute command more than once |
| ACK-01 | §10 | Valid command MUST receive ACK after durable acceptance | Deliver valid command | ACK `received` after acceptance |
| ACK-02 | §10 | Invalid command is rejected | Deliver malformed/unauthorized command | ACK `rejected` plus reason/error |
| ACK-03 | §10 | Duplicate is distinguished | Deliver already accepted message | ACK `duplicate`; no execution |
| TASK-01 | §8 | Task statuses are constrained | Attempt unknown status | Rejected |
| TASK-02 | §8 | Invalid transition MUST be rejected | Attempt terminal → IN_PROGRESS | `INVALID_STATE_TRANSITION`; state unchanged |
| TASK-03 | §8 | Accepted state transition increments version exactly once | Perform valid transition | Version N → N+1 exactly once |
| CAS-01 | §9 | Stale mutation MUST fail | Two writers use same expected version | Exactly one succeeds; other gets `STATE_CONFLICT` |
| CAS-02 | §9 | Stale writer MUST NOT overwrite newer state | Repeat stale mutation after winner commits | Stored state remains winner's state |
| RES-01 | §11 | Result records task outcome | Complete task | Result/error is durable |
| RES-02 | §11, §12 | Result is independent from publication | Complete task without transport publication | Task completed while publication remains pending |
| PUB-01 | §12 | PUBLISHED requires remote verification where supported | Mark PUBLISHED before verification | Status rejected/deferred |
| PUB-02 | §12 | Crash after remote publication is recoverable | Push artifact, crash before local status update | Recovery verifies artifact and marks PUBLISHED |
| PUB-03 | §12 | Publication recovery MUST NOT execute task | Recover pending publication | Only publication state changes; execution count unchanged |
| REC-01 | §13 | Durable recovery is required | Restart with pending/unacknowledged messages | State reconstructed and reconciled |
| REC-02 | §13 | Lost ACK/RESULT must not trigger re-execution | Lose ACK/RESULT then retry | No duplicate side effect |
| REC-03 | §14 | Stale heartbeat is a recovery condition, not a status | Stop worker until heartbeat stale | Task identified as recovery candidate; no `STALE` status |
| CAN-01 | §15 | Cancellation uses optimistic concurrency | Cancel with stale version | `STATE_CONFLICT`; state unchanged |
| CAN-02 | §15 | Terminal task cannot be cancelled | Cancel COMPLETED/FAILED/CANCELLED | Terminal state unchanged; authoritative state returned |
| CAN-03 | §15 | Completion/cancel race has deterministic winner | Race two valid mutations from same version | First committed transition wins; other gets `STATE_CONFLICT` |
| ERR-01 | §16 | Error has stable code and retryability | Trigger known protocol error | Code, message and `retryable` present |
| ATOM-01 | §17 | Atomicity MAY be used but distributed transaction is not required | Run implementation without distributed transaction | Core remains implementable and recoverable |
| EVID-01 | §18 | Prose is not protocol evidence | Agent says “pushed” without publication record | Publication remains unverified |
| EXT-01 | §19 | Extensions MUST NOT redefine Core | Add namespaced extension field | Core semantics unchanged |
| EXT-02 | §19 | Extensions SHOULD be namespaced | Add extension field | Namespace is documented; deviation recorded if absent |

## Normative coverage

Every Core `MUST` / `MUST NOT` requirement is mapped above. `SHOULD` / `SHOULD NOT` requirements are explicitly identified and tested where practical; any deviation MUST be documented by the implementation.

## Conformance result

An implementation is **AACP Core 1.0 conformant** only when all mandatory rows pass and no implementation-specific exception changes Core semantics.
