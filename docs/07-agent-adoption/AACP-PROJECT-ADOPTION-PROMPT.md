# AACP Universal Project Adoption Prompt

**Status:** normative adoption aid  
**Protocol:** AACP Core 1.0 / current protocol distribution  
**Purpose:** подключить AACP к любому существующему проекту одним промтом.

Этот документ — **универсальный onboarding prompt**. Его можно целиком передать агенту, работающему в любом проекте, независимо от того, является ли агент ChatGPT, Cursor или другим AACP-compatible agent.

Prompt не заменяет AACP specification. Он указывает агенту, какие canonical документы прочитать и какие project-local integration artifacts создать.

## Prompt

```text
Ты должен подключить AACP к текущему проекту как единственный протокол взаимодействия между агентами.

CANONICAL PROTOCOL

Канонический репозиторий AACP:
https://github.com/wise108/aacp

Сначала прочитай актуальные canonical документы AACP. Минимально обязательны:

1. AACP Core:
   https://github.com/wise108/aacp/blob/main/docs/02-core/specification.md

2. Agent Adoption & Migration Protocol:
   https://github.com/wise108/aacp/blob/main/docs/07-agent-adoption/AACP-ADOPTION.md

3. Agent Runtime Contract:
   https://github.com/wise108/aacp/blob/main/docs/07-agent-adoption/AACP-AGENT-RUNTIME.md

4. Applicable transport profile из:
   https://github.com/wise108/aacp/tree/main/docs/03-transports

5. Conformance requirements:
   https://github.com/wise108/aacp/blob/main/docs/04-conformance/requirements.md

Не копируй эти спецификации в проект. Они остаются canonical в AACP.

ТВОЯ РОЛЬ

Сначала определи свою AACP identity и роль в текущем проекте. Не выводи identity из имени пользователя, GitHub account, branch или имени проекта без явного project binding.

Если ты не можешь определить identity/role или необходимые capabilities, не выдумывай их: зафиксируй gap и продолжай только в безопасной части adoption.

DISCOVER → FREEZE → INVENTORY → PLAN → MIGRATE → VERIFY → CUTOVER → CLEANUP → OPERATE

Следуй этой последовательности из AACP Adoption Protocol.

1. DISCOVER

Изучи текущий проект и найди ВСЕ существующие механизмы agent-to-agent communication:

- файлы сообщений;
- IPC;
- prompts/rules/skills;
- journals;
- command/response files;
- branch-based communication;
- commit-based conventions;
- message stores;
- task/response IDs;
- polling/watch mechanisms;
- application-specific coordination.

Не изменяй и не удаляй ничего на этой стадии.

2. ОПРЕДЕЛИ TRANSPORT

Определи, какой transport будет использоваться для AACP.

Если используется GitHub, прочитай соответствующий GitHub Transport и ordered-stream semantics.

Transport implementation не должна менять семантику AACP Core.

3. СОЗДАЙ PROJECT-LOCAL AACP BINDING

В проекте должен появиться небольшой machine-readable binding, описывающий как этот конкретный проект использует AACP.

Минимально binding должен позволять определить:

- protocol = AACP;
- Core version;
- distribution/version, если требуется;
- transport/profile;
- participating agent identities and roles;
- conversation/stream identifiers, если они применимы;
- canonical transport ref/location;
- статус legacy communication, если migration выполняется.

Binding является consumer configuration. Он НЕ является новой спецификацией протокола.

4. СОЗДАЙ PROJECT-LOCAL AGENT INTEGRATION INSTRUCTIONS

Создай только те файлы, которые нужны конкретной среде проекта.

Если текущая среда — Cursor:

- создай или обнови project-local Cursor rule/instruction;
- она должна ссылаться на canonical AACP documents;
- она должна описывать только binding и поведение Cursor как AACP agent;
- не дублируй всю AACP specification;
- не создавай второй protocol/runtime specification.

Если текущая среда — ChatGPT Project или другой агент без Cursor rules:

- создай project-local onboarding/integration instruction в подходящем для этой среды месте;
- она должна ссылаться на canonical AACP documents;
- она должна описывать identity, role, binding, transport и обязанности агента;
- не копируй всю спецификацию AACP.

Если в проекте одновременно присутствуют несколько AACP participants, project-local integration должен обеспечить согласованный binding для всех участников. Не создавай отдельный протокол для каждого участника.

5. МИГРАЦИЯ LEGACY IPC

Если существовал legacy agent-to-agent protocol, следуй AACP Adoption Protocol.

Не удаляй legacy artifacts до успешной миграции и verification.

Не считай простое копирование файлов успешной миграцией.

Каждый migratable legacy record должен иметь понятное AACP mapping.

Не превращай ambiguous/in-flight work в completed без authoritative evidence.

6. CUTOVER

После успешной verification:

- AACP становится единственным active agent-to-agent protocol;
- новые agent-to-agent messages создаются только как AACP messages;
- legacy IPC больше не используется как рабочий канал;
- obsolete legacy artifacts можно удалить только после verification и только если они действительно obsolete.

7. ОСНОВНЫЕ RUNTIME ПРАВИЛА

Соблюдай AACP Agent Runtime Contract.

Минимально:

- каждый новый logical message получает уникальный immutable message_id;
- task_id идентифицирует logical task;
- retry той же доставки не создаёт новый message_id;
- duplicate message не должен повторно выполнять non-idempotent side effect;
- ACK accepted означает acceptance, а не completion;
- RESULT означает outcome, когда он предусмотрен контрактом;
- потерянный ACK/RESULT не доказывает отсутствие execution;
- PUBLISHED не означает EXECUTED;
- UNKNOWN execution outcome нельзя слепо трактовать как NOT_EXECUTED;
- ordered stream использует sequence для ordering, message_id — для identity;
- immutable published records нельзя редактировать, удалять или перенумеровывать для исправления истории;
- ordering conflicts/gaps обрабатываются согласно transport semantics;
- после restart состояние восстанавливается из canonical/durable protocol state.

8. НЕ СОЗДАВАЙ ПРОТОКОЛ ПОВЕРХ AACP

Запрещено без отдельного protocol change:

- второй IPC рядом с AACP;
- mutable coordination files как протокол;
- commit message как command;
- branch movement как ACK;
- timestamps как ordering;
- специальные marker-команды вроде mvp.write_marker;
- новый message ID при retransmission;
- произвольные project-specific shortcuts, противоречащие AACP;
- изменение AACP Core ради удобства одного проекта.

Если проектное требование не покрывается AACP, сначала определи, относится ли оно к protocol, transport, adapter или application orchestration. Не расширяй Core автоматически.

9. НЕ СМЕШИВАЙ AACP И ORCHESTRATION

AACP отвечает за inter-agent communication.

Registry, Task Registry, Dependency Graph, Progress Projection, orchestration event store и иные application-level механизмы не являются частью AACP adoption, если они не требуются текущей задачей.

Не добавляй их только потому, что проект в будущем может их использовать.

10. MINIMAL REAL-WORLD VERIFICATION

После integration проверь реальный минимальный Golden Path:

COMMAND
  → canonical transport state
  → receiving agent discovery/validation
  → ACK accepted
  → execution
  → RESULT
  → canonical transport state
  → originating agent observes RESULT

Отдельно проверь retransmission:

same logical COMMAND / same message_id
  → duplicate handling
  → no second non-idempotent execution

Если transport или среда не позволяют выполнить этот сценарий, не создавай workaround protocol. Зафиксируй конкретный technical gap.

11. КРИТЕРИЙ ЗАВЕРШЕНИЯ

Adoption завершён, если:

- canonical AACP documents определены;
- project-local binding создан или подтверждён;
- необходимые integration instructions созданы для фактической среды;
- legacy IPC inventory и migration выполнены, если legacy IPC существовал;
- verification завершена;
- AACP стал единственным active agent-to-agent protocol;
- минимальный real-world communication path проверен или конкретно зафиксирован blocking gap;
- AACP Core не был изменён без отдельной protocol-level процедуры.

12. ОТЧЁТ

В конце дай краткий отчёт:

- AACP Core / distribution;
- transport/profile;
- agent identities/roles;
- project-local binding location;
- created/updated integration files;
- legacy IPC found and migration result;
- verification result;
- remaining technical gaps;
- active AACP communication path.

Не утверждай compliance только потому, что файлы существуют. Отделяй configuration/documentation от реально проверенного protocol behavior.
```

## Design intent

The universal prompt is intentionally **role-neutral and project-neutral**. The target agent decides what project-local artifacts are appropriate for its environment.

The expected result is therefore not a fixed set of files in every repository. For example, a Cursor project may receive a Cursor rule plus an AACP binding, while a ChatGPT Project may receive a project instruction plus the same binding. Both point back to the same canonical AACP specification.

The canonical repository remains the only place where AACP protocol semantics are defined.
