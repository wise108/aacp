# AACP Architecture

AACP is the protocol layer between collaborating agents. It sits above agent runtimes and below application orchestration.

```text
User / Application
        ↓
   Orchestrator
        ↓
     AACP 1.0
        ↓
 Transport Adapter
        ↓
 Remote Agent
        ↓
 Agent Runtime (ACP / MCP / tools / LLM)
```

AACP defines the durable contract for tasks, messages, results, publication and recovery. It deliberately does not define the internal execution protocol of an agent.

## Separation of concerns

- **AACP Core** — semantics and reliability guarantees.
- **Transport profile** — how AACP records/messages move between participants.
- **Implementation** — storage, scheduling, orchestration and agent runtime.
- **Project policy** — project-specific rules that must not redefine Core semantics.

The same AACP Core can therefore be implemented by the AI Assistant and Cursor Remote Agent without forcing them to share their internal architecture.
