# AACP 1.0 Consistency Review

## Scope

Reviewed the normative Core specification, Message & Identity Model, Task State Machine, Envelope schema, ACK schema, Result schema, Runtime Contract, and Conformance Checklist as one protocol.

## Findings and resolutions

### 1. ACCEPTED state was missing from Core

The Task State Machine defined `ACCEPTED`, while Core did not. Core now includes `ACCEPTED` as the durable acknowledgement boundary.

### 2. ACK vocabulary differed between Core and schema

Core required `received`, `rejected`, `duplicate`; the schema allowed `accepted`, `duplicate`. The canonical vocabulary is now `accepted`, `rejected`, `duplicate`.

### 3. stream_id was referenced but absent from the envelope

Ordering is explicitly scoped to `(conversation_id, stream_id)`. `stream_id` is now mandatory in the Core envelope contract.

### 4. Message type vocabulary differed

The identity model used `progress`; Core used `event`. AACP 1.0 keeps the Core set: `command`, `ack`, `result`, `error`, `cancel`, `event`. Progress is represented as an `event` payload.

### 5. PENDING invalid-command transition was ambiguous

The Task State Machine no longer invents an implicit `PENDING → FAILED` transition for malformed/rejected commands. Rejection normally occurs before a Task enters the lifecycle. Existing Tasks require an explicit task contract.

### 6. Task completion and publication were conflated

The state model now explicitly separates `task.status=COMPLETED` from `publication.status=PUBLISHED`.

### 7. Sequence semantics were clarified

Sequence belongs to a stream, not a task or message lifecycle. Retransmission reuses both message ID and sequence. ACK/RESULT consume sequence numbers if they are members of the ordered stream.

## Remaining implementation requirements

The specification is now internally aligned at the document level, but implementation conformance still requires executable schema validation and mandatory failure/recovery scenarios.

## Review status

**DOCUMENT CONSISTENCY: PASS**

This review does not declare any implementation AACP-conformant. Conformance requires the executable checklist and scenario suite.
