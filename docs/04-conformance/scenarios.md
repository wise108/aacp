# AACP 1.0 Mandatory Conformance Scenarios

These scenarios are normative. An implementation claiming AACP Core 1.0 conformance MUST have executable tests or equivalent auditable evidence for every scenario.

| ID | Scenario | Required outcome |
|---|---|---|
| S01 | Normal command | Exactly one task execution and valid terminal outcome |
| S02 | Duplicate command | No second logical execution |
| S03 | Lost ACK | Original command is safely retransmitted |
| S04 | Lost RESULT | Execution is not repeated solely because result is missing |
| S05 | Crash before acceptance | Same command identity can be safely retried |
| S06 | Crash after acceptance | Task recovers as ACCEPTED |
| S07 | Crash during execution | Outcome treated as potentially unknown |
| S08 | Crash after side effect before result | Side effect is not blindly repeated |
| S09 | Crash after remote publication | Existing artifact is reconciled |
| S10 | Sequence gap | Later ordered message is retained/reported, not silently reordered |
| S11 | Duplicate RESULT | No second logical terminal result |
| S12 | Concurrent state mutation | Stale writer receives STATE_CONFLICT |
| S13 | Completion/cancellation race | First valid commit wins; stale operation cannot overwrite |
| S14 | Timeout with unknown outcome | No blind retry |
| S15 | Safe retry after known non-execution | New attempt may start on same task |
| S16 | Cancellation before execution | CANCELLED without execution side effect |
| S17 | Cancellation during execution | Cannot claim cancellation unless safely stoppable |
| S18 | Invalid transition | State mutation rejected |
| S19 | Result publication failure | Task completion remains distinct from publication state |
| S20 | Recovery idempotency | Repeated recovery produces no additional side effect |

## S01 — Normal command

Given a valid new command, acceptance and execution MUST produce exactly one logical execution and the contractually required terminal result/error.

## S02 — Duplicate command

Deliver the same command twice with the same `message_id`. The second delivery MUST NOT execute the logical side effect again.

## S03 — Lost ACK

Execute a command while suppressing its ACK, then retransmit the original message. The receiver MUST recognize the original identity and execute at most once.

## S04 — Lost RESULT

Complete execution while suppressing RESULT delivery. Recovery/retry MUST republish or reconstruct the existing result without rerunning the task.

## S05 — Crash before acceptance

Crash before durable acceptance. The original command identity MUST remain safe to retransmit.

## S06 — Crash after acceptance

Persist acceptance, then crash before execution. Recovery MUST reconstruct ACCEPTED and continue without creating a new logical command.

## S07 — Crash during execution

Crash after execution starts and before outcome is known. Recovery MUST treat execution as potentially having occurred and reconcile before retry.

## S08 — Crash after side effect before result

Perform the side effect, crash, and omit the result. Recovery MUST establish the outcome and publish/reconstruct the result rather than blindly repeating the side effect.

## S09 — Crash after remote publication

Publish a result remotely, then crash before local publication state is persisted. Recovery MUST verify the remote artifact and converge to PUBLISHED without re-execution.

## S10 — Sequence gap

Deliver sequence N+1 before N on an ordered stream. Receiver MUST detect `SEQUENCE_GAP` and MUST NOT silently reinterpret delivery order as protocol order.

## S11 — Duplicate RESULT

Deliver the same RESULT twice. The second delivery MUST be idempotent and MUST NOT create another terminal result.

## S12 — Concurrent state mutation

Two writers use the same state version; one commits first. The other MUST receive `STATE_CONFLICT` and MUST NOT overwrite the newer state.

## S13 — Completion/cancellation race

Completion and cancellation target the same version concurrently. Exactly one valid state mutation commits; the stale operation loses with `STATE_CONFLICT`.

## S14 — Timeout with unknown outcome

Timeout occurs while the remote operation may still be executing. The implementation MUST NOT blindly start a new attempt.

## S15 — Safe retry after known non-execution

Recovery establishes that the previous attempt definitely produced no side effect. An explicit retry policy MAY start a new attempt on the same task.

## S16 — Cancellation before execution

Cancel PENDING or ACCEPTED work before execution starts. The task MUST become CANCELLED and execution side effect MUST NOT occur.

## S17 — Cancellation during execution

Cancel IN_PROGRESS work that cannot safely be stopped. The implementation MUST NOT claim CANCELLED solely because the request was received.

## S18 — Invalid transition

Attempt a transition not permitted by the Task State Machine. The mutation MUST be rejected and authoritative state/version MUST remain unchanged.

## S19 — Result publication failure

Complete execution successfully while remote publication fails. Task MAY be COMPLETED while publication is PENDING or FAILED; publication retry MUST NOT rerun execution.

## S20 — Recovery idempotency

Run recovery repeatedly against unchanged durable state. It MUST converge without creating additional non-idempotent side effects.

## Conformance rule

A missing test is a failed conformance item, not an implicit pass. AACP Core 1.0 conformance is PASS only when S01–S20 all pass and the implementation can identify executable evidence for each scenario.
