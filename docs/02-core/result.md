# AACP 1.0 Result

A `result` is an AACP message describing the outcome of a task.

A successful task normally transitions to `COMPLETED` and produces a result when the command contract requires one.

A failed task normally transitions to `FAILED` and produces an `error` message when required.

A result is immutable and has its own `message_id`. It references the logical `task_id` and SHOULD reference the originating command through `correlation_id` and/or `causation_id`.

A result being missing or delayed MUST NOT be interpreted as proof that execution did not occur. Recovery must reconcile the task state before retrying uncertain work.

AACP Core does not define a separate publication state. Transport-specific delivery/verification is outside Core.
