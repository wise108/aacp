# AACP Message 1.0

Messages are carried in the AACP Envelope. Core message types are:

- `command` — request execution or an operation.
- `ack` — confirms receipt/recognition.
- `result` — reports task outcome.
- `error` — reports protocol or execution failure.
- `cancel` — requests cancellation.
- `event` — reports a meaningful state/event without requesting execution.

## Idempotency

`message_id` is the idempotency key. A receiver MUST persist or otherwise durably remember processed message IDs for at least as long as duplicate delivery could occur. A duplicate MUST NOT execute a command again.

## Ordering

Each ordered stream has its own sequence space. The receiver tracks the next expected sequence. A gap MUST be detected and MUST NOT be silently ignored under strict ordering.

## ACK

Typical flow:

```text
COMMAND
  ↓
ACK(received)
  ↓
RESULT
```

ACK loss is expected to be recoverable through retransmission and idempotent handling.

## Command example

```yaml
protocol: AACP
version: "1.0"
message_id: M-01...
task_id: T-01...
conversation_id: C-01...
sender: chatgpt
recipient: cursor
sequence: 1
type: command
created_at: "2026-08-28T12:30:00Z"
payload:
  action: implement
  instructions: "Implement feature X"
```
