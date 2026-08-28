# AACP 1.0 Errors

Errors are machine-readable protocol outcomes. Project-specific diagnostic details MAY be carried in `payload`.

Core implementations SHOULD distinguish at least:

- `INVALID_MESSAGE` — envelope or required field is invalid;
- `UNSUPPORTED_VERSION` — protocol version is unsupported;
- `REJECTED` — command is valid but will not be accepted;
- `DUPLICATE` — message identity has already been accepted/processed;
- `STATE_CONFLICT` — stale state mutation was rejected;
- `EXECUTION_FAILED` — task execution failed;
- `CANCEL_REJECTED` — requested cancellation could not be safely applied.

Transport-specific failures are not task failures unless the task contract says otherwise.

Core does not define a `PUBLICATION_FAILED` error because publication is not a Core concept.
