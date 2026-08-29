# AACP — Agent-to-Agent Collaboration Protocol

AACP is a small, transport-independent protocol for reliable collaboration between software agents.

## Что решает AACP

AACP определяет минимальный контракт для:

- идентификации задач и их жизненного цикла;
- идентификации сообщений и повторной доставки;
- подтверждений (ACK);
- безопасной обработки дубликатов;
- результатов и ошибок;
- восстановления после сбоев;
- опционального упорядочивания и контроля конкурентных изменений.

## Что AACP не решает

AACP не определяет LLM, prompting, внутреннюю архитектуру агента, Cursor ACP, MCP, Telegram/UI-протоколы, брокер сообщений, базу данных или обязательный транспорт.

## Документация

Начните с:

- [Архитектура](docs/01-overview/architecture.md)
- [Терминология](docs/01-overview/terminology.md)
- [AACP Core 1.0](docs/02-core/specification.md)
- [Transport profiles](docs/03-transports/)
- [Conformance](docs/04-conformance/requirements.md)
- [Schemas](schemas/)
- [Adoption](docs/07-agent-adoption/AACP-ADOPTION.md)

Вся человекочитаемая документация протокола находится в `docs/`. Машиночитаемые схемы находятся в `schemas/`.

## Как подключить AACP к существующему проекту

Если вы — агент, которому поручено внедрить AACP в существующий проект, используйте следующий промт. Он предназначен для передачи агенту как есть.

### Русская версия — основная

```text
Внедри AACP как единый протокол взаимодействия между агентами в этом репозитории.

Канонический репозиторий протокола:
https://github.com/wise108/aacp

Сначала изучи документацию протокола, в первую очередь:
https://github.com/wise108/aacp/blob/main/docs/07-agent-adoption/AACP-ADOPTION.md

Также изучи нормативную спецификацию AACP Core 1.0:
https://github.com/wise108/aacp/blob/main/docs/02-core/specification.md

Твоя задача:

1. Найди и проанализируй все существующие механизмы взаимодействия между агентами в этом репозитории.
2. Определи, какие из них являются текущим рабочим протоколом, а какие — историческими, вспомогательными или тестовыми.
3. Не меняй существующий рабочий процесс до завершения инвентаризации и составления плана миграции.
4. Мигрируй существующий протокол взаимодействия на AACP 1.0 согласно процедуре Adoption.
5. Сохрани необходимые существующие данные и историю взаимодействия. Ничего не удаляй до тех пор, пока миграция не будет проверена.
6. После успешной миграции выполни проверку того, что оба участника действительно могут работать по AACP.
7. Только после успешной проверки удали или отключи устаревшие механизмы взаимодействия, которые были заменены AACP.
8. После cutover используй для взаимодействия между агентами только AACP. Не возвращайся к старым механизмам и не создавай параллельный протокол.
9. Не изменяй семантику AACP Core под потребности проекта. Проектные особенности реализуй как transport profile, extension или внутреннюю реализацию, если это допускает спецификация.
10. Не добавляй в AACP новые сущности или усложнения без необходимости. Если требование проекта не покрывается Core, сначала определи, действительно ли оно относится к протоколу, а не к реализации.

Критерий завершения:

- существующий протокол взаимодействия инвентаризирован;
- миграция на AACP 1.0 завершена;
- необходимые исторические данные сохранены;
- миграция проверена;
- старый протокол отключён/удалён только после проверки;
- AACP стал единственным протоколом agent-to-agent взаимодействия в проекте;
- проектные механизмы не изменяют семантику AACP Core.

Не ограничивайся изменением документации. Выполни реальную миграцию кода, конфигурации и рабочих данных, если это необходимо для перехода на AACP.

По завершении дай краткий отчёт:
- что было найдено;
- что мигрировано;
- какие данные сохранены;
- что удалено/отключено;
- как проверена совместимость;
- каким образом дальнейшее взаимодействие теперь выполняется по AACP.
```

### English version

```text
Adopt AACP as the single agent-to-agent communication protocol in this repository.

Canonical protocol repository:
https://github.com/wise108/aacp

First read the protocol documentation, especially:
https://github.com/wise108/aacp/blob/main/docs/07-agent-adoption/AACP-ADOPTION.md

Also read the normative AACP Core 1.0 specification:
https://github.com/wise108/aacp/blob/main/docs/02-core/specification.md

Your task:

1. Discover and analyze all existing mechanisms used for agent-to-agent communication in this repository.
2. Determine which mechanisms are the current working protocol and which are historical, auxiliary, or test-only.
3. Do not change the existing workflow until the inventory and migration plan are complete.
4. Migrate the existing communication protocol to AACP 1.0 according to the Adoption procedure.
5. Preserve required existing data and communication history. Do not delete anything until migration has been verified.
6. After migration, verify that both participants can actually operate using AACP.
7. Only after successful verification, remove or disable obsolete communication mechanisms replaced by AACP.
8. After cutover, use only AACP for agent-to-agent communication. Do not fall back to the old mechanisms or create a parallel protocol.
9. Do not change AACP Core semantics to fit project-specific needs. Implement project-specific behavior as a transport profile, extension, or internal implementation where permitted by the specification.
10. Do not add new protocol concepts or unnecessary complexity. If a project requirement is not covered by Core, first determine whether it belongs to the protocol at all rather than to the implementation.

Completion criteria:

- the existing communication protocol has been inventoried;
- migration to AACP 1.0 is complete;
- required historical data has been preserved;
- migration has been verified;
- the old protocol has been disabled/removed only after verification;
- AACP is the only agent-to-agent communication protocol used by the project;
- project-specific mechanisms do not alter AACP Core semantics.

Do not limit the work to documentation changes. Perform the actual migration of code, configuration, and working data where necessary.

When finished, provide a brief report:
- what was found;
- what was migrated;
- what data was preserved;
- what was removed/disabled;
- how compatibility was verified;
- how future agent-to-agent communication now operates through AACP.
```

## Принцип дизайна

> Протокол должен быть проще систем, которые его используют.

## Статус

AACP 1.0 — baseline спецификации. Core намеренно содержит только правила, необходимые для надёжного обмена задачами между агентами. Расширенные fault-injection и recovery-эксперименты относятся к conformance harness и не являются обязательными возможностями протокола.
