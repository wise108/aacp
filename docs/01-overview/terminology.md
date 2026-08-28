# AACP Terminology

| Term | Definition |
|---|---|
| Agent | Software participant capable of sending or processing AACP messages |
| Conversation | Logical collaboration context identified by `conversation_id` |
| Task | Durable unit of work identified by `task_id` |
| Message | One protocol communication identified by `message_id` |
| Stream | Ordered sequence space for messages between participants |
| Result | Durable record of task outcome |
| Publication | Transport-specific availability state of a result |
| Transport | Mechanism used to move/publish AACP state |
| Evidence | Data supporting a result, such as test or commit references |
| Recovery | Reconciliation performed after interruption or restart |
| Core | Transport-independent normative AACP semantics |
| Profile | Transport- or implementation-specific rules that extend Core without redefining it |

AACP uses **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in their conventional normative sense.
