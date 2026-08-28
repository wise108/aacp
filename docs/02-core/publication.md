# AACP Publication 1.0

Publication records whether a Result is available to the remote participant through a transport.

Statuses are `PENDING`, `PUBLISHED`, and `FAILED`.

## Completion and publication are independent

`task.status: COMPLETED` and `publication.status: PUBLISHED` are independent facts. Completing execution MUST NOT imply publication.

## Publication invariant

A transport that supports remote verification MUST NOT report `PUBLISHED` until it has verified that the referenced Result is available remotely.

For Git, the normal sequence is:

```text
Result durable locally
      ↓
commit
      ↓
push
      ↓
verify remote ref contains commit/result
      ↓
PUBLISHED
```

A local commit is not publication.

## Crash after push

If the process crashes after the remote push but before durable publication state is updated, recovery MUST verify the remote transport before retrying publication.

If the expected Result/commit is already present remotely, recovery MUST mark the publication `PUBLISHED` without re-executing the Task. It MUST NOT require another execution merely because the local publication record still says `PENDING`.

If the expected Result is absent, publication MAY be retried. Retry MUST NOT imply task re-execution.

## Publication identity

A publication record SHOULD identify the immutable artifact/result being published and the transport location needed for verification. For Git this normally includes repository, ref and commit SHA.

## Failed publication

`FAILED` means publication was attempted and did not succeed. It does not mean the Task failed. A completed Task with failed publication remains completed and MAY be retried for publication.
