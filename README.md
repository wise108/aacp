# AACP — Agent-to-Agent Collaboration Protocol

AACP is a small, transport-independent protocol for reliable collaboration between software agents.

## What AACP solves

AACP defines a minimal contract for:

- task identity and lifecycle;
- message identity and retries;
- acknowledgements;
- duplicate-safe processing;
- results and errors;
- crash recovery;
- optional ordering and concurrency control.

## What AACP does not solve

AACP does not define an LLM, prompting, agent internals, Cursor ACP, MCP, Telegram/UI protocols, a message broker, a database, or a mandatory transport.

## Documentation

Start with:

- [Architecture](docs/01-overview/architecture.md)
- [Terminology](docs/01-overview/terminology.md)
- [AACP Core 1.0](docs/02-core/specification.md)
- [Transport profiles](docs/03-transports/)
- [Conformance](docs/04-conformance/requirements.md)
- [Schemas](schemas/)

All human-readable protocol documentation is under `docs/`. Machine-readable schemas remain under `schemas/`.

## Design principle

> The protocol should be simpler than the systems that use it.

## Status

AACP 1.0 is a design/specification baseline. The Core deliberately contains only the rules required for reliable agent-to-agent task exchange. Advanced fault-injection and recovery experiments belong to the conformance harness and are not required protocol features.
