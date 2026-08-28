# AACP 1.0 — Universal Adoption Prompt

Use this prompt when migrating an existing agent project to AACP.

---

## Prompt

You are working in an existing software project that must communicate with another software agent.

The project must use **AACP 1.0** as its protocol for agent-to-agent communication.

Canonical specification:

`https://github.com/wise108/aacp`

### 1. Read the protocol first

Before changing code, read the AACP repository, especially:

- `README.md`;
- `docs/02-core/specification.md`;
- `docs/01-overview/`;
- `schemas/`;
- `docs/03-transports/` when a transport profile is relevant;
- `docs/04-conformance/`.

Treat the AACP Core specification as the source of truth. Do not infer protocol behavior from this prompt when the repository specifies it more precisely.

### 2. Audit the existing project

Find every mechanism currently used for agent-to-agent communication, including:

- message formats;
- task IDs and correlation IDs;
- ACKs;
- retries;
- result delivery;
- status/state tracking;
- recovery after restart;
- ordering/deduplication;
- Git/branch/commit based coordination;
- protocol documentation and tests.

Do not modify anything until you understand the existing protocol and identify its migration surface.

### 3. Produce a migration map

Map each existing protocol concept to AACP 1.0 or explicitly mark it as project-specific.

Do not add an AACP feature merely because the old protocol had one.

AACP Core is intentionally minimal.

### 4. Implement AACP

Implement only the AACP Core requirements needed by this project.

Use the canonical AACP message envelope and message types.

Preserve project-specific business/domain payloads inside AACP `payload` rather than changing the meaning of Core fields.

Use immutable `message_id` for message identity and `task_id` for logical task identity.

Retries of the same message MUST reuse its `message_id`.

Duplicate command delivery MUST NOT cause duplicate logical execution.

ACK acceptance MUST NOT be interpreted as task completion.

### 5. Migrate existing state

Existing protocol data MUST be migrated before legacy protocol data is removed.

Migration MUST preserve, where applicable:

- logical task identity;
- current task state;
- execution/result information;
- correlation information;
- evidence needed for recovery and deduplication.

If an old field has no AACP equivalent, preserve it as project-specific metadata rather than silently discarding information.

### 6. Compatibility and cutover

Use a controlled migration/cutover strategy appropriate to the project.

During migration, the implementation MUST NOT create two competing sources of truth.

After successful migration and verification, remove or disable the legacy protocol implementation and documentation.

Do not delete legacy data before its migration is verified.

### 7. Tests

Add or update tests proving the six minimum Core properties:

1. immutable unique message identity;
2. safe duplicate command handling;
3. accepted/rejected/duplicate ACK semantics;
4. valid task lifecycle enforcement;
5. protection against stale state overwrite;
6. safe restart behavior for uncertain execution.

Run the project's existing tests as well.

Use the AACP conformance scenarios when they are applicable to the project's transport/runtime.

### 8. Do not over-engineer

Do NOT implement advanced distributed-systems machinery unless the project independently requires it.

Do not add brokers, consensus, distributed transactions, mandatory sequence numbers, publication state, heartbeats, or other mechanisms solely because they appear in experimental/conformance material.

AACP Core should remain minimal.

### 9. Documentation

Document:

- that the project uses AACP 1.0;
- the transport profile, if any;
- project-specific payloads/extensions;
- migration decisions;
- tests proving conformance.

Reference the canonical AACP repository instead of copying the whole protocol specification into the project.

### 10. Final verification

Before declaring migration complete, verify:

- both agents use the same AACP Core semantics;
- duplicate delivery cannot duplicate logical execution;
- lost ACK does not cause duplicate execution;
- lost result does not cause blind re-execution;
- restart does not blindly repeat uncertain execution;
- stale state cannot overwrite newer state;
- legacy protocol is no longer an active source of truth;
- tests pass.

Then provide a concise migration report containing:

1. existing protocol found;
2. AACP mapping;
3. files changed;
4. data migrated;
5. legacy components removed/disabled;
6. tests executed and results;
7. any project-specific deviations or extensions.

Do not claim AACP conformance if a normative Core requirement is not satisfied.
