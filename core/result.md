# AACP Result 1.0

A Result records what happened when a Task was executed.

```yaml
task_id: T-01...
status: completed
summary: "Implemented feature X."
evidence:
  commits:
    - abc123...
  tests:
    - command: pytest
      exit_code: 0
      summary: "All tests passed"
```

A Result SHOULD contain enough concise evidence for the recipient to understand and verify the outcome.

Recommended evidence fields:

- `commits`
- `tests`
- `files`
- `artifacts`

Evidence is informational unless the relevant transport or project profile defines a stronger verification rule.

A Result being created or locally persisted does not imply that it is remotely published.
