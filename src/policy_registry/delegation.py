"""Fail-closed candidate resolver for signed delegated-avatar decisions.

The resolver deliberately does not activate delegated authorization.  It can
only establish whether a signed candidate satisfies the current contract for a
future cutover.  ``authorizes_action`` therefore remains false in every result.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .model import expand_uri, is_valid_now, sha256_file
from .registry import PolicyRegistry

AUTHORITY_SOURCE_DECISION = "D-20260730-001"
GRANT_SCHEMA = "ellmos.signed-delegation-grant.v1"
CANDIDATE_SCHEMA = "ellmos.delegated-avatar-decision-candidate.v2"
RESULT_SCHEMA = "ellmos.delegation-resolution.v1"
TRUST_STORE_SCHEMA = "ellmos.delegation-issuer-trust.v1"
DECISION_TYPE = "predicted/delegated-avatar-decision"
SIGNATURE_ALGORITHM = "ed25519"
MINIMUM_CONFIDENCE = 0.80
CUTOVER_ENABLED = False

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_ID = re.compile(r"^(?:ar|decision|oid|pe|loc)-[0-9a-f]{64}$")
_CODE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{1,127}$")
_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:/-]{1,125}(?:/\*)?$")
_REASON_CODE = re.compile(r"^[a-z0-9]+(?:[._:/-][a-z0-9]+){0,7}$")
_GLOBAL_SCOPES = {"*", "all", "global", "system-wide"}
_FORBIDDEN_KEYS = {
    "body",
    "content",
    "full_text",
    "fulltext",
    "payload",
    "private_key",
    "raw",
    "raw_evidence",
    "rationale_text",
    "secret",
    "token",
}


class DelegationError(ValueError):
    """The signed delegation input is invalid or cannot be trusted."""


@dataclass(frozen=True)
class TrustedIssuerKey:
    issuer_id: str
    key_id: str
    public_key: bytes
    key_pin: str


class IssuerTrustStore:
    """Externally configured issuer keys; receipts cannot self-assert trust."""

    def __init__(self, keys: Mapping[tuple[str, str], TrustedIssuerKey]):
        self._keys = dict(keys)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "IssuerTrustStore":
        _reject_forbidden_keys(value)
        if set(value) != {"schema", "issuers"}:
            raise DelegationError("trust store fields do not match the schema")
        if value["schema"] != TRUST_STORE_SCHEMA:
            raise DelegationError("unsupported issuer trust-store schema")
        issuers = value["issuers"]
        if not isinstance(issuers, list) or not 1 <= len(issuers) <= 256:
            raise DelegationError("one to 256 trusted issuer keys are required")
        keys: dict[tuple[str, str], TrustedIssuerKey] = {}
        for item in issuers:
            if not isinstance(item, dict) or set(item) != {
                "issuer_id",
                "key_id",
                "algorithm",
                "public_key",
                "key_pin",
            }:
                raise DelegationError("invalid trusted issuer entry")
            _validate_code(item["issuer_id"], "issuer ID")
            _validate_code(item["key_id"], "issuer key ID")
            if item["algorithm"] != SIGNATURE_ALGORITHM:
                raise DelegationError("unsupported issuer signature algorithm")
            public_key = _decode_public_key(item["public_key"])
            key_pin = _validate_key_pin(item["key_pin"], public_key)
            identity = (item["issuer_id"], item["key_id"])
            if identity in keys:
                raise DelegationError("duplicate trusted issuer key")
            keys[identity] = TrustedIssuerKey(
                issuer_id=item["issuer_id"],
                key_id=item["key_id"],
                public_key=public_key,
                key_pin=key_pin,
            )
        return cls(keys)

    @classmethod
    def from_file(cls, path: str | Path) -> "IssuerTrustStore":
        source = Path(path)
        if source.stat().st_size > 262_144:
            raise DelegationError("trust store exceeds the 256 KiB input limit")
        value = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise DelegationError("trust store must be a JSON object")
        return cls.from_dict(value)

    def get(self, issuer_id: str, key_id: str) -> TrustedIssuerKey:
        try:
            return self._keys[(issuer_id, key_id)]
        except KeyError as error:
            raise DelegationError("delegation issuer or key is not trusted") from error


@dataclass(frozen=True)
class DelegationResolution:
    schema: str
    status: str
    evaluation_time_mode: str
    candidate_id: str | None
    delegation_receipt_id: str | None
    qualified_for_future_cutover: bool
    cutover_enabled: bool
    authorizes_action: bool
    reasons: tuple[str, ...]
    verified: tuple[str, ...]
    policy_resolution: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["reasons"] = list(self.reasons)
        value["verified"] = list(self.verified)
        return value


class DelegationResolver:
    """Verifies a signed grant and candidate against current registry authority."""

    def __init__(
        self,
        registry: PolicyRegistry,
        trust_store: IssuerTrustStore,
        *,
        clock_skew: timedelta = timedelta(minutes=5),
        now_provider: Callable[[], datetime] | None = None,
    ):
        self.registry = registry
        self.trust_store = trust_store
        self.clock_skew = clock_skew
        self.now_provider = now_provider or (lambda: datetime.now(UTC))

    def resolve(
        self,
        grant: dict[str, Any],
        candidate: dict[str, Any],
        *,
        at: datetime | None = None,
    ) -> DelegationResolution:
        historical_audit = at is not None
        now = _normalize_now(at if historical_audit else self.now_provider())
        candidate_id = (
            candidate.get("candidate_id")
            if isinstance(candidate, dict)
            and isinstance(candidate.get("candidate_id"), str)
            else None
        )
        receipt_id = (
            grant.get("receipt_id")
            if isinstance(grant, dict) and isinstance(grant.get("receipt_id"), str)
            else None
        )
        verified: list[str] = []
        try:
            _reject_forbidden_keys(grant)
            _reject_forbidden_keys(candidate)
            _validate_grant_shape(grant)
            _validate_candidate_shape(candidate)
            registry_snapshot = self.registry.load()

            grant_hash = _verify_embedded_hash(
                grant,
                hash_field="receipt_content_hash",
                signature_field="signature",
                identity_field="receipt_id",
            )
            if grant["receipt_id"] != f"ar-{grant_hash}":
                raise DelegationError("delegation receipt ID is not content-bound")
            trusted_issuer = self.trust_store.get(
                grant["issuer"]["id"],
                grant["issuer"]["key_id"],
            )
            if trusted_issuer.key_pin != grant["issuer"]["key_pin"]:
                raise DelegationError("delegation issuer key pin mismatch")
            _verify_signature(
                trusted_issuer.public_key,
                grant["signature"],
                _signature_message("grant", grant_hash),
            )
            verified.extend(("grant-content-hash", "grant-issuer-signature"))

            current_registry_hash = _registry_content_hash(registry_snapshot)
            if grant["registry_content_hash"] != current_registry_hash:
                raise DelegationError(
                    "current policy registry differs from the signed delegation snapshot"
                )
            verified.append("current-registry-snapshot")
            self._verify_authority_source(grant, now, registry_snapshot)
            verified.append("current-authority-source")
            self._verify_grant_window(grant, now)
            verified.append("grant-time-window")

            candidate_hash = _verify_embedded_hash(
                candidate,
                hash_field="candidate_content_hash",
                signature_field="signature",
                identity_field="candidate_id",
            )
            if candidate["candidate_id"] != f"decision-{candidate_hash}":
                raise DelegationError("candidate ID is not content-bound")
            if candidate["delegation_receipt_id"] != grant["receipt_id"]:
                raise DelegationError(
                    "candidate references a different delegation receipt"
                )
            if candidate["delegation_content_hash"] != grant_hash:
                raise DelegationError("candidate delegation content hash mismatch")
            if candidate["subject"]["id"] != grant["delegate"]["id"]:
                raise DelegationError("candidate subject is not the delegated subject")
            if candidate["subject"]["key_id"] != grant["delegate"]["key_id"]:
                raise DelegationError("candidate key is not the delegated key")

            delegate_key = _decode_public_key(grant["delegate"]["public_key"])
            _validate_key_pin(grant["delegate"]["key_pin"], delegate_key)
            _verify_signature(
                delegate_key,
                candidate["signature"],
                _signature_message("candidate", candidate_hash),
            )
            verified.extend(("candidate-content-hash", "candidate-delegate-signature"))

            self._verify_candidate_window(candidate, grant, now)
            self._verify_scope_action_confidence(candidate, grant)
            verified.extend(("candidate-time-window", "scope-action-confidence"))

            policy_resolution = self._resolve_policy_context(
                candidate,
                grant,
                now,
                registry_snapshot,
            )
            if policy_resolution["status"] != "clear":
                raise DelegationError(policy_resolution["reason"])
            verified.append("current-project-global-policy-context")
        except (DelegationError, OSError, json.JSONDecodeError) as error:
            return DelegationResolution(
                schema=RESULT_SCHEMA,
                status="rejected",
                evaluation_time_mode=(
                    "historical-audit" if historical_audit else "current"
                ),
                candidate_id=candidate_id,
                delegation_receipt_id=receipt_id,
                qualified_for_future_cutover=False,
                cutover_enabled=CUTOVER_ENABLED,
                authorizes_action=False,
                reasons=(str(error),),
                verified=tuple(verified),
                policy_resolution=locals().get(
                    "policy_resolution",
                    {"status": "not-evaluated", "reason": str(error)},
                ),
            )

        if historical_audit:
            status = "historical-audit-qualified"
            qualified_for_future_cutover = False
            reasons = ("historical audit cannot qualify a future cutover",)
        else:
            status = "candidate-qualified"
            qualified_for_future_cutover = True
            reasons = ("runtime cutover remains disabled",)
        return DelegationResolution(
            schema=RESULT_SCHEMA,
            status=status,
            evaluation_time_mode=(
                "historical-audit" if historical_audit else "current"
            ),
            candidate_id=candidate["candidate_id"],
            delegation_receipt_id=grant["receipt_id"],
            qualified_for_future_cutover=qualified_for_future_cutover,
            cutover_enabled=CUTOVER_ENABLED,
            authorizes_action=False,
            reasons=reasons,
            verified=tuple(verified),
            policy_resolution=policy_resolution,
        )

    def _verify_authority_source(
        self,
        grant: dict[str, Any],
        now: datetime,
        registry_snapshot: dict[str, Any],
    ) -> None:
        if grant["authority_source_id"] != AUTHORITY_SOURCE_DECISION:
            raise DelegationError("unsupported delegation authority source")
        entry = next(
            (
                candidate
                for candidate in registry_snapshot["entries"]
                if candidate["id"] == AUTHORITY_SOURCE_DECISION
            ),
            None,
        )
        if entry is None:
            raise DelegationError("current authority-source decision is not registered")
        if (
            entry["kind"] != "decision"
            or entry.get("authority") != "explicit-user-decision"
            or entry.get("source", {}).get("canonical") is not True
            or not is_valid_now(entry, today=now.date())
        ):
            raise DelegationError(
                "authority-source decision is not current and explicit"
            )
        expected_hash = (entry.get("hash") or {}).get("value")
        if (
            not isinstance(expected_hash, str)
            or not _SHA256.fullmatch(expected_hash)
            or expected_hash != grant["authority_source_content_hash"]
        ):
            raise DelegationError("authority-source receipt/content hash mismatch")
        source_path = expand_uri(entry["source"]["uri"])
        if source_path is None or not source_path.is_file():
            raise DelegationError("authority-source content is not locally verifiable")
        if sha256_file(source_path) != expected_hash:
            raise DelegationError("current authority-source content hash is stale")

    def _verify_grant_window(
        self,
        grant: dict[str, Any],
        now: datetime,
    ) -> None:
        issued_at = _parse_utc(grant["issued_at"], "issued_at")
        expires_at = _parse_utc(grant["expires_at"], "expires_at")
        review_at = _parse_utc(grant["review_at"], "review_at")
        if issued_at > now + self.clock_skew:
            raise DelegationError("delegation grant is not yet valid")
        if expires_at <= issued_at or review_at <= issued_at:
            raise DelegationError("delegation expiry/review must follow issuance")
        if now >= expires_at:
            raise DelegationError("delegation grant has expired")
        if now >= review_at:
            raise DelegationError("delegation grant requires current review")

    def _verify_candidate_window(
        self,
        candidate: dict[str, Any],
        grant: dict[str, Any],
        now: datetime,
    ) -> None:
        created_at = _parse_utc(candidate["created_at"], "created_at")
        issued_at = _parse_utc(grant["issued_at"], "issued_at")
        expires_at = _parse_utc(grant["expires_at"], "expires_at")
        review_at = _parse_utc(grant["review_at"], "review_at")
        if created_at < issued_at:
            raise DelegationError("candidate predates the delegation grant")
        if created_at > now + self.clock_skew:
            raise DelegationError("candidate creation time is in the future")
        if created_at >= expires_at or created_at >= review_at:
            raise DelegationError(
                "candidate was created outside the reviewed grant window"
            )

    @staticmethod
    def _verify_scope_action_confidence(
        candidate: dict[str, Any],
        grant: dict[str, Any],
    ) -> None:
        scope = candidate["scope"]
        action = candidate["action_code"]
        consumer = candidate["consumer_code"]
        if _is_global_scope(scope):
            raise DelegationError("global blank-scope delegation is forbidden")
        if not any(_pattern_matches(pattern, scope) for pattern in grant["scopes"]):
            raise DelegationError("candidate scope is outside the signed delegation")
        if not any(
            _pattern_matches(pattern, action) for pattern in grant["action_patterns"]
        ):
            raise DelegationError("candidate action is outside the signed delegation")
        if consumer not in grant["consumers"]:
            raise DelegationError("candidate consumer is outside the signed delegation")
        if any(
            _pattern_matches(pattern, scope) for pattern in grant["excluded_scopes"]
        ):
            raise DelegationError("candidate scope is explicitly excluded")
        if any(
            _pattern_matches(pattern, action) for pattern in grant["excluded_actions"]
        ):
            raise DelegationError("candidate action is explicitly excluded")
        threshold = grant["minimum_confidence"]
        if threshold < MINIMUM_CONFIDENCE:
            raise DelegationError("signed confidence threshold is below the hard floor")
        if candidate["confidence"] < threshold:
            raise DelegationError("candidate confidence is below the signed threshold")

    def _resolve_policy_context(
        self,
        candidate: dict[str, Any],
        grant: dict[str, Any],
        now: datetime,
        registry_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        scope = candidate["scope"]
        action = candidate["action_code"]
        consumer = candidate["consumer_code"]
        relevant: list[dict[str, Any]] = []
        unresolved: list[str] = []
        for entry in registry_snapshot["entries"]:
            if entry["id"] == grant["authority_source_id"]:
                continue
            if entry["kind"] not in {"policy", "rule", "decision"}:
                continue
            if not is_valid_now(entry, today=now.date()):
                continue
            if not isinstance(entry.get("scope"), str):
                unresolved.append(entry["id"])
                continue
            if not _entry_scope_applies(entry["scope"], scope):
                continue
            consumers = entry.get("consumers", [])
            if consumers and "*" not in consumers and consumer not in consumers:
                continue
            try:
                _verify_context_entry_source(entry)
            except DelegationError:
                unresolved.append(entry["id"])
                continue
            patterns = entry.get("action_patterns", entry.get("actions"))
            effect = entry.get("effect")
            if (
                not isinstance(patterns, list)
                or not patterns
                or effect
                not in {
                    "allow",
                    "deny",
                }
            ):
                unresolved.append(entry["id"])
                continue
            try:
                _validate_patterns(patterns, "registry action patterns")
            except DelegationError:
                unresolved.append(entry["id"])
                continue
            if any(_pattern_matches(pattern, action) for pattern in patterns):
                relevant.append(entry)
        if unresolved:
            return {
                "status": "unresolved",
                "reason": (
                    "applicable current policies/decisions lack machine-readable "
                    "delegation conflict metadata: " + ", ".join(sorted(unresolved))
                ),
                "considered": sorted(item["id"] for item in relevant),
                "unresolved": sorted(unresolved),
            }
        if not relevant:
            return {
                "status": "clear",
                "reason": None,
                "considered": [],
                "selected": None,
            }
        ranked = sorted(
            relevant,
            key=lambda item: _authority_key(item, scope),
            reverse=True,
        )
        top_key = _authority_key(ranked[0], scope)
        top = [item for item in ranked if _authority_key(item, scope) == top_key]
        effects = {item["effect"] for item in top}
        if len(effects) != 1:
            return {
                "status": "conflict",
                "reason": "equal higher-authority entries conflict for this action",
                "considered": [item["id"] for item in ranked],
                "selected": None,
            }
        selected = sorted(item["id"] for item in top)
        if effects == {"deny"}:
            return {
                "status": "denied",
                "reason": "a current higher-authority policy or decision denies the action",
                "considered": [item["id"] for item in ranked],
                "selected": selected,
            }
        return {
            "status": "clear",
            "reason": None,
            "considered": [item["id"] for item in ranked],
            "selected": selected,
        }


def _validate_grant_shape(value: dict[str, Any]) -> None:
    required = {
        "schema",
        "receipt_id",
        "authority_source_id",
        "authority_source_content_hash",
        "registry_content_hash",
        "issuer",
        "delegate",
        "issued_at",
        "expires_at",
        "review_at",
        "scopes",
        "action_patterns",
        "consumers",
        "excluded_scopes",
        "excluded_actions",
        "minimum_confidence",
        "receipt_content_hash",
        "signature_algorithm",
        "signature",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise DelegationError("delegation grant fields do not match the schema")
    if value["schema"] != GRANT_SCHEMA:
        raise DelegationError("unsupported delegation grant schema")
    if value["authority_source_id"] != AUTHORITY_SOURCE_DECISION:
        raise DelegationError("unsupported authority-source decision")
    _validate_hash(value["authority_source_content_hash"], "authority source hash")
    _validate_hash(value["registry_content_hash"], "policy registry hash")
    _validate_hash(value["receipt_content_hash"], "receipt content hash")
    if value["signature_algorithm"] != SIGNATURE_ALGORITHM:
        raise DelegationError("unsupported grant signature algorithm")
    _validate_signature_text(value["signature"])
    _validate_identity(value["issuer"], issuer=True)
    _validate_delegate(value["delegate"])
    for field in ("issued_at", "expires_at", "review_at"):
        _parse_utc(value[field], field)
    _validate_patterns(value["scopes"], "delegation scopes")
    _validate_patterns(value["action_patterns"], "delegation action patterns")
    _validate_codes_list(value["consumers"], "delegation consumers")
    _validate_patterns(value["excluded_scopes"], "excluded scopes", allow_empty=True)
    _validate_patterns(value["excluded_actions"], "excluded actions", allow_empty=True)
    _validate_confidence(value["minimum_confidence"], "minimum confidence")


def _validate_candidate_shape(value: dict[str, Any]) -> None:
    required = {
        "schema",
        "candidate_id",
        "decision_type",
        "delegation_receipt_id",
        "delegation_content_hash",
        "subject",
        "scope",
        "action_code",
        "consumer_code",
        "confidence",
        "reason_codes",
        "evidence_refs",
        "provenance",
        "created_at",
        "candidate_content_hash",
        "signature_algorithm",
        "signature",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise DelegationError("delegated candidate fields do not match the schema")
    if value["schema"] != CANDIDATE_SCHEMA:
        raise DelegationError("unsupported delegated candidate schema")
    if value["decision_type"] != DECISION_TYPE:
        raise DelegationError("unsupported delegated decision type")
    _validate_opaque_id(value["candidate_id"], "candidate ID", prefix="decision-")
    _validate_opaque_id(
        value["delegation_receipt_id"],
        "delegation receipt ID",
        prefix="ar-",
    )
    _validate_hash(value["delegation_content_hash"], "delegation content hash")
    _validate_identity(value["subject"], issuer=False)
    _validate_code(value["scope"], "candidate scope")
    _validate_code(value["action_code"], "candidate action")
    _validate_code(value["consumer_code"], "candidate consumer")
    _validate_confidence(value["confidence"], "candidate confidence")
    _validate_reason_codes(value["reason_codes"])
    _validate_evidence_refs(value["evidence_refs"])
    _validate_provenance(value["provenance"])
    _parse_utc(value["created_at"], "created_at")
    _validate_hash(value["candidate_content_hash"], "candidate content hash")
    if value["signature_algorithm"] != SIGNATURE_ALGORITHM:
        raise DelegationError("unsupported candidate signature algorithm")
    _validate_signature_text(value["signature"])


def _validate_identity(value: Any, *, issuer: bool) -> None:
    fields = {"id", "key_id", "key_pin"} if issuer else {"id", "key_id"}
    if not isinstance(value, dict) or set(value) != fields:
        raise DelegationError("invalid signed identity binding")
    _validate_code(value["id"], "identity ID")
    _validate_code(value["key_id"], "identity key ID")
    if issuer:
        _validate_hash(value["key_pin"], "issuer key pin")


def _validate_delegate(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "key_id",
        "algorithm",
        "public_key",
        "key_pin",
    }:
        raise DelegationError("invalid delegated subject binding")
    _validate_code(value["id"], "delegate ID")
    _validate_code(value["key_id"], "delegate key ID")
    if value["algorithm"] != SIGNATURE_ALGORITHM:
        raise DelegationError("unsupported delegate signature algorithm")
    public_key = _decode_public_key(value["public_key"])
    _validate_key_pin(value["key_pin"], public_key)


def _validate_provenance(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {
        "provider_code",
        "avatar_id",
        "skill_id",
        "model_id",
    }:
        raise DelegationError("invalid candidate provenance")
    _validate_code(value["provider_code"], "provider code")
    for field in ("avatar_id", "skill_id", "model_id"):
        _validate_opaque_id(value[field], field, prefix="oid-")


def _validate_evidence_refs(value: Any) -> None:
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise DelegationError("one to sixteen evidence references are required")
    seen: set[tuple[str, str]] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "evidence_id",
            "content_hash",
        }:
            raise DelegationError("evidence references must remain opaque")
        _validate_opaque_id(item["evidence_id"], "evidence ID")
        if not item["evidence_id"].startswith(("pe-", "loc-")):
            raise DelegationError("unsupported evidence reference type")
        _validate_hash(item["content_hash"], "evidence content hash")
        identity = (item["evidence_id"], item["content_hash"])
        if identity in seen:
            raise DelegationError("duplicate evidence reference")
        seen.add(identity)


def _validate_reason_codes(value: Any) -> None:
    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= 8
        or any(
            not isinstance(item, str) or not _REASON_CODE.fullmatch(item)
            for item in value
        )
        or len(set(value)) != len(value)
    ):
        raise DelegationError("one to eight unique bounded reason codes are required")


def _validate_codes_list(value: Any, label: str) -> None:
    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= 32
        or any(not isinstance(item, str) or not _CODE.fullmatch(item) for item in value)
        or len(set(value)) != len(value)
    ):
        raise DelegationError(f"invalid {label}")


def _validate_patterns(
    value: Any,
    label: str,
    *,
    allow_empty: bool = False,
) -> None:
    if (
        not isinstance(value, list)
        or (not value and not allow_empty)
        or len(value) > 32
        or any(
            not isinstance(item, str) or not _PATTERN.fullmatch(item) for item in value
        )
        or len(set(value)) != len(value)
    ):
        raise DelegationError(f"invalid {label}")
    if any(_is_global_scope(item) for item in value):
        raise DelegationError(f"global wildcard is forbidden in {label}")


def _is_global_scope(value: str) -> bool:
    """Reject global authorities even when disguised as namespace descendants."""

    return value in _GLOBAL_SCOPES or value.startswith(
        ("all/", "global/", "system-wide/")
    )


def _validate_confidence(value: Any, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0.0 <= float(value) <= 1.0
    ):
        raise DelegationError(f"{label} must be between zero and one")


def _validate_code(value: Any, label: str) -> None:
    if not isinstance(value, str) or not _CODE.fullmatch(value):
        raise DelegationError(f"invalid {label}")


def _validate_opaque_id(value: Any, label: str, *, prefix: str | None = None) -> None:
    if (
        not isinstance(value, str)
        or not _OPAQUE_ID.fullmatch(value)
        or (prefix is not None and not value.startswith(prefix))
    ):
        raise DelegationError(f"invalid {label}")


def _validate_hash(value: Any, label: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise DelegationError(f"invalid {label}")


def _validate_signature_text(value: Any) -> None:
    if not isinstance(value, str) or len(value) != 88:
        raise DelegationError("signature must be base64 text")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise DelegationError("signature is not valid base64") from error
    if len(decoded) != 64:
        raise DelegationError("invalid Ed25519 signature length")


def _decode_public_key(value: Any) -> bytes:
    if not isinstance(value, str) or len(value) != 44:
        raise DelegationError("public key must be base64 text")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise DelegationError("public key is not valid base64") from error
    if len(decoded) != 32:
        raise DelegationError("invalid Ed25519 public-key length")
    return decoded


def _validate_key_pin(value: Any, public_key: bytes) -> str:
    _validate_hash(value, "key pin")
    actual = hashlib.sha256(public_key).hexdigest()
    if value != actual:
        raise DelegationError("public key does not match its key pin")
    return actual


def _verify_embedded_hash(
    value: dict[str, Any],
    *,
    hash_field: str,
    signature_field: str,
    identity_field: str,
) -> str:
    unsigned = {
        key: item
        for key, item in value.items()
        if key not in {hash_field, signature_field, identity_field}
    }
    actual = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    if value[hash_field] != actual:
        raise DelegationError(f"{hash_field} does not match canonical content")
    return actual


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DelegationError("signed object is not canonical JSON data") from error


def _registry_content_hash(data: dict[str, Any]) -> str:
    snapshot = {
        "schema": data["schema"],
        "entries": sorted(data["entries"], key=lambda item: item["id"]),
    }
    return hashlib.sha256(_canonical_json(snapshot)).hexdigest()


def _signature_message(kind: str, content_hash: str) -> bytes:
    return f"policy-registry:{kind}:v1:{content_hash}".encode("ascii")


def _verify_signature(public_key: bytes, signature: str, message: bytes) -> None:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            base64.b64decode(signature, validate=True),
            message,
        )
    except (InvalidSignature, ValueError, binascii.Error) as error:
        raise DelegationError("signature verification failed") from error


def _parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise DelegationError(f"{label} must be a UTC timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise DelegationError(f"{label} must be a UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise DelegationError(f"{label} must be an explicit UTC timestamp")
    return parsed.astimezone(UTC)


def _normalize_now(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise DelegationError("resolver time must be an explicit UTC timestamp")
    return value.astimezone(UTC)


def _pattern_matches(pattern: str, value: str) -> bool:
    if pattern.endswith("/*"):
        prefix = pattern[:-1]
        return value.startswith(prefix) and len(value) > len(prefix)
    return value == pattern


def _entry_scope_applies(entry_scope: str, candidate_scope: str) -> bool:
    if entry_scope in _GLOBAL_SCOPES:
        return True
    if entry_scope.endswith("/*"):
        return _pattern_matches(entry_scope, candidate_scope)
    return entry_scope == candidate_scope or candidate_scope.startswith(
        entry_scope.rstrip("/") + "/"
    )


def _authority_key(
    entry: dict[str, Any], candidate_scope: str
) -> tuple[int, int, int, int]:
    authority = entry.get("authority")
    if entry["kind"] in {"policy", "rule"} and authority in {
        "binding",
        "binding-policy",
        "constitutional-policy",
    }:
        rank = 500
    elif entry["kind"] == "decision" and authority == "explicit-user-decision":
        rank = 400
    elif entry["kind"] in {"policy", "rule"}:
        rank = 300
    else:
        rank = 200
    if entry["scope"] == candidate_scope:
        scope_rank = 2
    elif entry["scope"] in _GLOBAL_SCOPES:
        scope_rank = 0
    else:
        scope_rank = 1
    return (rank, scope_rank, entry["priority"], entry["precedence"])


def _verify_context_entry_source(entry: dict[str, Any]) -> None:
    expected = (entry.get("hash") or {}).get("value")
    source = entry.get("source")
    if (
        not isinstance(expected, str)
        or not _SHA256.fullmatch(expected)
        or not isinstance(source, dict)
        or source.get("canonical") is not True
    ):
        raise DelegationError("authority context source is not hash-bound")
    path = expand_uri(source.get("uri", ""))
    if path is None or not path.is_file():
        raise DelegationError("authority context source is not locally verifiable")
    if sha256_file(path) != expected:
        raise DelegationError("authority context source hash is stale")


def _reject_forbidden_keys(value: Any) -> None:
    stack: list[tuple[Any, int]] = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 4096 or depth > 16:
            raise DelegationError("signed delegation input exceeds structure limits")
        if isinstance(item, dict):
            forbidden = _FORBIDDEN_KEYS & set(item)
            if forbidden:
                raise DelegationError(
                    "raw/self-asserted content is forbidden in signed delegation inputs: "
                    + ", ".join(sorted(forbidden))
                )
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)


__all__ = [
    "AUTHORITY_SOURCE_DECISION",
    "CANDIDATE_SCHEMA",
    "CUTOVER_ENABLED",
    "DECISION_TYPE",
    "DelegationError",
    "DelegationResolution",
    "DelegationResolver",
    "GRANT_SCHEMA",
    "IssuerTrustStore",
    "MINIMUM_CONFIDENCE",
    "RESULT_SCHEMA",
    "SIGNATURE_ALGORITHM",
    "TRUST_STORE_SCHEMA",
]
