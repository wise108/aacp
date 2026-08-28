# AACP 1.0 Conformance Requirements

An implementation may claim AACP Core 1.0 compatibility only if it satisfies every normative `MUST` and `MUST NOT` requirement in the Core specification and passes all mandatory scenarios in [scenarios.md](scenarios.md).

The normative requirements are mapped to observable tests in the [Conformance Matrix](matrix.md).

`SHOULD` and `SHOULD NOT` requirements are recommended rather than mandatory for Core conformance. An implementation that deviates from one MUST document the deviation and its rationale; such deviations MUST NOT change Core semantics.

Transport profiles add their own requirements. Passing a transport profile does not permit an implementation to violate Core semantics.

Conformance tests SHOULD be automated where practical and SHOULD include process interruption, duplicate delivery, transport failure and concurrent state mutation.
