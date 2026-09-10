# AACP — Agent-to-Agent Collaboration Protocol

AACP is a small, transport-independent protocol for reliable collaboration between software agents.

**Protocol distribution:** 1.1.0  
**AACP Core:** 1.0

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
- [Universal project adoption prompt](docs/07-agent-adoption/AACP-PROJECT-ADOPTION-PROMPT.md)
- [Changelog](CHANGELOG.md)

Вся человекочитаемая документация протокола находится в `docs/`. Машиночитаемые схемы находятся в `schemas/`.

## Как подключить AACP к существующему проекту

Для подключения AACP к **любому существующему проекту** используйте универсальный adoption prompt:

**[AACP Universal Project Adoption Prompt](docs/07-agent-adoption/AACP-PROJECT-ADOPTION-PROMPT.md)**

Его можно передать агенту как есть. Prompt определяет, какие canonical документы необходимо прочитать, какие project-local artifacts создать и как адаптировать их под конкретную среду (например, Cursor или ChatGPT Project).

Важно: prompt не является отдельной спецификацией и не должен копироваться в каждый проект целиком. Он ссылается на canonical AACP и instructs the adopting agent to create the минимальный project-local binding/integration layer, необходимый именно этому проекту.

## Принцип дизайна

> Протокол должен быть проще систем, которые его используют.

## Версионирование

AACP uses separate versioning for the protocol distribution and AACP Core. The protocol distribution may advance when transport profiles, recovery procedures, conformance requirements, or adoption guidance change without redefining Core semantics.

The current protocol distribution is **1.1.0**. AACP Core remains **1.0**.

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Статус

AACP Core 1.0 — stable baseline specification. Protocol distribution 1.1.0 strengthens the GitHub ordered-stream transport/recovery profile and conformance requirements without changing AACP Core message semantics.
