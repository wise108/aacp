# AACP — Agent-to-Agent Collaboration Protocol

AACP is a small, transport-independent protocol for reliable task coordination between software agents.

## What AACP solves

AACP defines a durable contract for:

- task identity and lifecycle;
- ordered messages;
- idempotent processing;
- acknowledgements;
- optimistic concurrency;
- results and evidence;
- publication state;
- crash recovery and heartbeat semantics;
- conformance testing.

## What AACP does not solve

AACP does **not** define an LLM, agent runtime, Telegram integration, Cursor ACP, MCP, or a mandatory transport. Those belong to implementations and transport profiles.

## Documentation

Start here:

- [Architecture](docs/01-overview/architecture.md)
- [Terminology](docs/01-overview/terminology.md)
- [AACP Core 1.0](docs/02-core/specification.md)
- [Transport profiles](docs/03-transports/)
- [Conformance](docs/04-conformance/requirements.md)
- [Machine-readable schemas](schemas/)

All human-readable protocol documentation is under `docs/`. Machine-readable schemas remain at repository root as implementation artifacts.

## Design principle

> AACP describes reliable state and communication between agents; it does not prescribe how an agent performs its internal work.

## Status

AACP 1.0 is a design/specification baseline. Implementations should pass the conformance scenarios before declaring AACP 1.0 compatibility.
