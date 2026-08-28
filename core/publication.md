# AACP Publication 1.0

Publication records whether a result is available to the remote participant through a transport.

Statuses:

- `PENDING`
- `PUBLISHED`
- `FAILED`

Example:

```yaml
publication:
  status: PUBLISHED
  transport: github
  repository: wise108/example
  ref: refs/heads/main
  commit: abc123...
```

`task.status: COMPLETED` and `publication.status: PUBLISHED` are independent facts.

A transport MUST NOT report `PUBLISHED` merely because a local commit exists. Where remote verification is possible, the transport MUST verify that the referenced commit/result is available on the remote ref.

For Git, `commit → push → verify remote ref` is the minimum publication sequence.
