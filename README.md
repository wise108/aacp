# AACP — Agent-to-Agent Collaboration Protocol

AACP (Agent-to-Agent Collaboration Protocol) is a small, transport-independent protocol for reliable task coordination between software agents.

## Scope

AACP defines:

- task identity and lifecycle;
- ordered messages;
- idempotent processing;
- acknowledgements;
- optimistic concurrency for task state;
- results and evidence;
- publication state;
- crash recovery and heartbeat semantics;
- a conformance test model.

AACP does **not** define an LLM, agent runtime, Telegram integration, Cursor ACP, MCP, or a particular transport. Those belong to implementations and transport adapters.

## Version

This repository contains the normative AACP Core 1.0 specification.

## Design principle

> AACP describes reliable state and communication between agents; it does not prescribe how an agent performs its internal work.

## Documents

- [SPEC.md](SPEC.md) — normative Core 1.0 specification
- [core/envelope.md](core/envelope.md) — message envelope
- [core/task.md](core/task.md) — task model and lifecycle
- [core/message.md](core/message.md) — messages, ordering and idempotency
- [core/result.md](core/result.md) — results and evidence
- [core/publication.md](core/publication.md) — publication semantics
- [core/errors.md](core/errors.md) — error model and registry
- [state-machine/task.md](state-machine/task.md) — state machine
- [transports/github.md](transports/github.md) — GitHub transport profile
- [conformance/scenarios.md](conformance/scenarios.md) — mandatory reliability scenarios
- [schemas/](schemas/) — machine-readable JSON Schemas

## Status

AACP 1.0 is a design/specification baseline. Implementations should pass the conformance scenarios before declaring AACP 1.0 compatibility.
