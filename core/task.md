# AACP Task 1.0

A Task is the durable unit of work coordinated between agents.

```yaml
task_id: T-01...
conversation_id: C-01...
created_by: chatgpt
assigned_to: cursor
status: PENDING
state_version: 1
created_at: "2026-08-28T12:30:00Z"
updated_at: "2026-08-28T12:30:00Z"
heartbeat_at: null
command_message_id: M-01...
```

## Required fields

- `task_id`
- `conversation_id`
- `created_by`
- `status`
- `state_version`
- `created_at`
- `updated_at`

`assigned_to`, `heartbeat_at`, and `command_message_id` are optional depending on lifecycle stage.

## Statuses

- `PENDING`
- `IN_PROGRESS`
- `BLOCKED`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

`STALE` is not a Task status; it is a recovery condition derived from heartbeat age.

## Ownership

`assigned_to` identifies the current execution owner. A receiver MUST NOT claim a task already owned by another active worker without a valid recovery/reassignment operation.
