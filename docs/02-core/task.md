# AACP Task 1.0

A Task is the durable unit of work coordinated between agents.

Core statuses are `PENDING`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `FAILED`, and `CANCELLED`. `STALE` is a recovery condition, not a Task status.

A Task has `task_id`, `conversation_id`, `created_by`, `status`, `state_version`, `created_at`, and `updated_at`. `assigned_to`, `heartbeat_at`, and `command_message_id` are lifecycle-dependent fields.

See [SPEC.md](../../SPEC.md) for the authoritative normative requirements.