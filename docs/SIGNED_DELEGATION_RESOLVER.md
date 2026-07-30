# Signed Delegation Resolver (candidate-only)

Status: V4-08 implementation candidate for `D-20260730-001`.

The resolver verifies whether a delegated-avatar decision candidate satisfies a
signed, current, narrowly scoped delegation. It does **not** activate delegated
authorization:

```json
{
  "status": "candidate-qualified",
  "qualified_for_future_cutover": true,
  "cutover_enabled": false,
  "authorizes_action": false
}
```

`candidate-qualified` is therefore an audit result, not permission to execute
an action.

## Trust chain

```text
external issuer trust store
  -> pinned Ed25519 issuer key
    -> signed delegation grant
      -> pinned delegate public key
        -> signed decision candidate
          -> current policy-registry authority/conflict resolution
            -> candidate-qualified, cutover still false
```

The issuer trust store is external configuration. A grant cannot add its own
issuer to that trust store. The issuer signature covers the delegate identity,
delegate key and pin, authority-source hash, scopes, actions, exclusions,
allowed consumers, a canonical registry snapshot hash, confidence threshold,
issuance, expiry and review boundary.

The candidate signature is verified against the delegate key bound by the
issuer-signed grant. Candidate and grant identifiers are deterministic hashes
of their canonical JSON payloads.

Only Ed25519 is accepted in v1. The contract is provider-neutral: the candidate
may identify any bounded provider code, but provider identity never creates
authority.

## Required gates

The resolver fails closed unless all gates pass:

- trusted issuer ID, key ID, key pin and Ed25519 signature;
- current, active, adopted and canonical `D-20260730-001` registry entry with
  `authority=explicit-user-decision`;
- byte-current local SHA-256 readback of that decision source;
- current registry entries exactly match the issuer-reviewed snapshot;
- valid `issued_at`, `expires_at` and `review_at` window;
- delegate identity, delegate key pin and candidate signature;
- candidate ID, receipt ID and both canonical content hashes;
- non-global delegated scope and matching action;
- consumer explicitly bound by the signed grant;
- no matching scope/action exclusion;
- signed confidence threshold of at least `0.80`, and candidate confidence at
  or above that threshold;
- one to sixteen opaque evidence references and bounded reason codes;
- current project/global policy and user-decision context without unresolved
  machine-readable conflicts;
- higher-authority precedence (binding policy/rule, explicit user decision,
  then other adopted decision; project-specific scope precedes global scope
  only within the same authority class).

An applicable current policy/decision without `effect` (`allow`/`deny`) and
`action_patterns` is unresolved and blocks qualification. This is intentional:
prose is not silently interpreted as permission.

Any registry entry added, replaced or removed after grant signing invalidates
the snapshot hash and requires a newly reviewed and signed grant.

## Raw data and self-assertion

Grant, candidate and trust-store inputs reject raw-content, body, payload,
private-key, secret and token fields recursively. Evidence references contain
only opaque `pe-`/`loc-` identifiers and SHA-256 hashes.

Raw TOM_lm output, raw evidence, unsigned candidates, self-asserted receipts and
keys carried only by a candidate never authorize anything.

## Python API

```python
from policy_registry import (
    DelegationResolver,
    IssuerTrustStore,
    PolicyRegistry,
)

registry = PolicyRegistry()
trust = IssuerTrustStore.from_file("issuer-trust.json")
result = DelegationResolver(registry, trust).resolve(grant, candidate)

assert result.cutover_enabled is False
assert result.authorizes_action is False
```

## CLI

```powershell
policy-registry resolve-delegation `
  --grant signed-grant.json `
  --candidate signed-candidate.json `
  --trust-store issuer-trust.json
```

Candidate qualification returns exit `3`, deliberately not shell-success,
because runtime cutover is disabled. Rejection returns exit `2`; malformed CLI
input returns exit `1`. Use `--at <UTC timestamp>` only for reproducible
audits.

## Nonclaims

- no key generation, signing or secret storage;
- no automatic TOM_lm call;
- no action execution;
- no network trust discovery;
- no remote source verification;
- no cutover or authority migration;
- no claim that a cryptographically valid candidate is factually correct.

## Versioned JSON contracts

The strict Python validators remain the runtime enforcement layer. External
clients can validate the same wire formats before invoking the resolver:

- [`signed-delegation-grant.v1.schema.json`](../schemas/signed-delegation-grant.v1.schema.json)
- [`delegated-avatar-decision-candidate.v2.schema.json`](../schemas/delegated-avatar-decision-candidate.v2.schema.json)
- [`delegation-issuer-trust.v1.schema.json`](../schemas/delegation-issuer-trust.v1.schema.json)
- [`delegation-resolution.v1.schema.json`](../schemas/delegation-resolution.v1.schema.json)
