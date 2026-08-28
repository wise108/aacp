# AACP 1.0 Message Envelope

Every AACP message uses the canonical envelope defined in `schemas/envelope.schema.json`.

Required fields:

- `protocol`: `AACP`
- `version`: `1.0`
- `message_id`: immutable unique message identity
- `conversation_id`: collaboration context
- `task_id`: logical unit of work
- `type`: message type
- `sender`: sender identity
- `recipient`: recipient identity
- `created_at`: RFC 3339 timestamp
- `payload`: message-specific object

Optional fields:

- `correlation_id`
- `causation_id`
- `sequence`
- `stream_id`

`sequence` is not required by Core. Use it only when an applicable transport profile requires ordering. Retransmission keeps the original `message_id` and sequence.
