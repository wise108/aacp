# AACP Envelope 1.0

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
payload: {}
```

## Required fields

| Field | Type | Requirement |
|---|---|---|
| protocol | string | MUST be `AACP` |
| version | string | MUST be `1.0` for Core 1.0 |
| message_id | string | MUST be unique |
| task_id | string | MUST identify the task |
| conversation_id | string | MUST identify the conversation |
| sender | string | MUST identify sender |
| recipient | string | MUST identify intended recipient |
| sequence | integer | MUST be monotonic within the stream |
| type | enum | MUST be a defined AACP message type |
| created_at | datetime | MUST be RFC 3339/ISO 8601 |
| payload | object | MUST contain type-specific data |

Optional metadata:

- `correlation_id`
- `causation_id`
- `metadata`

Unknown extension fields MUST NOT change Core semantics.
