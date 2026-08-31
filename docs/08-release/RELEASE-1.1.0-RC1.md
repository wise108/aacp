# AACP 1.1.0-rc.1

Status: release candidate, not final.

Core version: 1.0
Distribution version: 1.1.0-rc.1

## Scope

This candidate contains GitHub ordered-stream hardening, immutable collision recovery, publication/orderability/execution separation, restart/rediscovery rules, and executable conformance coverage G1–G10.

## Final-release gates

The final `1.1.0` release requires:

1. conformance suite execution with passing evidence;
2. final audit of the normative documents;
3. `VERSION` changed to `1.1.0`;
4. changelog finalized;
5. Git tag `v1.1.0` created on the final release commit;
6. GitHub Release created and verified.

Until all gates pass, consumers MUST treat this as a release candidate rather than a final protocol release.
