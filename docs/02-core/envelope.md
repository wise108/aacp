# AACP Envelope 1.0

Every AACP message MUST contain `protocol`, `version`, `message_id`, `task_id`, `conversation_id`, `sender`, `recipient`, `sequence`, `type`, `created_at`, and `payload`.

Message types: `command`, `ack`, `result`, `error`, `cancel`, `event`.

Optional metadata includes `correlation_id`, `causation_id`, and `metadata`.

See [SPEC.md](../../SPEC.md) for the authoritative normative requirements.