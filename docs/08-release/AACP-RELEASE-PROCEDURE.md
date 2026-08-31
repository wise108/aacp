# AACP Release Procedure

This procedure is normative for publishing an AACP protocol distribution release. A Core version and a distribution version are separate concepts.

## Versioning

- **MAJOR** — incompatible change to AACP Core semantics or wire/schema contract.
- **MINOR** — backward-compatible normative additions to Core, transport profiles, recovery procedures, schemas, or conformance requirements.
- **PATCH** — backward-compatible corrections that do not change normative behavior.
- A release candidate uses a SemVer prerelease identifier such as `1.1.0-rc.1`.

A transport-profile change that does not redefine Core semantics MUST NOT force a Core version change.

## Release gates

A version MUST NOT be described as released until all applicable gates pass:

1. normative specification changes are complete;
2. schemas are consistent;
3. conformance tests are executable and pass;
4. changelog is updated;
5. `VERSION` matches the intended distribution version;
6. a Git tag `v<VERSION>` exists on the release commit;
7. a GitHub Release exists for that tag;
8. adoption documentation identifies the released version/profile.

A commit or branch named for a release is not itself a release.

## Candidate flow

```text
change
  ↓
conformance
  ↓
VERSION = X.Y.Z-rc.N
  ↓
CHANGELOG
  ↓
release candidate tag/release
  ↓
validation
  ↓
VERSION = X.Y.Z
  ↓
final tag/release
```

## Auditability

The release commit, tag, and release notes MUST identify the Core version and distribution version separately when they differ.

If tooling cannot create or verify the tag/release artifact, the release MUST remain in candidate/pre-release status. An agent MUST NOT claim a final release based solely on a file containing a version number.
