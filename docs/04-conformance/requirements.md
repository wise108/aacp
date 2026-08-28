# AACP 1.0 Conformance Requirements

An implementation may claim AACP Core 1.0 compatibility when it satisfies every normative `MUST` and `MUST NOT` in the Core specification.

The minimum conformance properties are:

1. immutable unique message identity;
2. safe duplicate command handling;
3. accepted/rejected/duplicate ACK semantics;
4. valid task lifecycle enforcement;
5. no stale state overwrite;
6. safe restart behavior for uncertain execution.

The [Conformance Matrix](matrix.md) maps these properties to observable tests.

The S01–S20 scenario catalogue is a broader test suite. It is recommended for robust implementations, but advanced fault-injection coverage is not itself an additional Core protocol requirement.

Transport profiles may add requirements but MUST NOT change Core semantics.
