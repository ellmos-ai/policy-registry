"""Pointer-only seam for prevalidated BYUM decision-prediction metadata.

This module deliberately does not import BYUM, read event files, or parse a
decision journal.  Its input is a closed pointer envelope produced only after
the BYUM v2 contract has already been validated.  The resulting registry entry
is discoverable metadata, never an authoritative decision or policy.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from ..model import ValidationError, validate_entry
from ..registry import PolicyRegistry

POINTER_SCHEMA = "ellmos.policy-registry.byum-pointer.v1"
BYUM_PROTOCOL = "byum.decision-prediction.v2"
PROJECTION_STATUSES = {"pending", "decision-observed", "validated"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@#-]{0,255}$")

_POINTER_FIELDS = {"schema", "byum_protocol", "prediction_id", "decision_ref", "projection"}
_DECISION_REF_FIELDS = {"decision_id", "index_key", "scope", "source_locator", "source_sha256"}
_LOCATOR_FIELDS = {"path", "block_id"}
_PROJECTION_FIELDS = {"uri", "sha256", "status"}


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field} muss ein Objekt sein")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} muss eine nichtleere Zeichenkette sein")
    return value.strip()


def _closed(value: dict[str, Any], expected: set[str], field: str) -> None:
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing or unexpected:
        raise ValidationError(
            f"{field} hat fehlende oder unerwartete Pointer-Felder: "
            f"missing={missing}, unexpected={unexpected}"
        )


def _sha256(value: object, field: str) -> str:
    value = _string(value, field)
    if not SHA256_RE.fullmatch(value):
        raise ValidationError(f"{field} muss ein kleingeschriebener SHA-256-Wert sein")
    return value


def _identifier(value: object, field: str) -> str:
    value = _string(value, field)
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValidationError(f"{field} muss ein stabiler ID-Token ohne Freitext sein")
    return value


def validate_pointer(pointer: dict[str, Any]) -> dict[str, Any]:
    """Validate only policy-registry's closed pointer boundary.

    BYUM event semantics remain BYUM's responsibility.  This function checks
    protocol identity, stable locator/hash metadata, and the absence of any
    additional content or authority fields before registry projection.
    """

    value = _object(pointer, "pointer")
    _closed(value, _POINTER_FIELDS, "pointer")
    if value.get("schema") != POINTER_SCHEMA:
        raise ValidationError(f"pointer.schema muss {POINTER_SCHEMA!r} sein")
    if value.get("byum_protocol") != BYUM_PROTOCOL:
        raise ValidationError(f"BYUM-Protokoll muss {BYUM_PROTOCOL!r} sein")
    _identifier(value.get("prediction_id"), "prediction_id")

    decision_ref = _object(value.get("decision_ref"), "decision_ref")
    _closed(decision_ref, _DECISION_REF_FIELDS, "decision_ref")
    _identifier(decision_ref.get("decision_id"), "decision_ref.decision_id")
    _identifier(decision_ref.get("index_key"), "decision_ref.index_key")
    _string(decision_ref.get("scope"), "decision_ref.scope")
    locator = _object(decision_ref.get("source_locator"), "decision_ref.source_locator")
    _closed(locator, _LOCATOR_FIELDS, "decision_ref.source_locator")
    _string(locator.get("path"), "decision_ref.source_locator.path")
    _identifier(locator.get("block_id"), "decision_ref.source_locator.block_id")
    _sha256(decision_ref.get("source_sha256"), "decision_ref.source_sha256")

    projection = _object(value.get("projection"), "projection")
    _closed(projection, _PROJECTION_FIELDS, "projection")
    projection_uri = _string(projection.get("uri"), "projection.uri")
    if projection_uri.casefold().startswith(("http://", "https://", "git+")):
        raise ValidationError("projection.uri muss ein lokaler Pointer sein")
    _sha256(projection.get("sha256"), "projection.sha256")
    if projection.get("status") not in PROJECTION_STATUSES:
        raise ValidationError(
            "projection.status muss pending, decision-observed oder validated sein"
        )
    return copy.deepcopy(value)


def candidate_entry(
    pointer: dict[str, Any],
    *,
    owner: str = "BYUM",
    consumers: list[str] | None = None,
) -> dict[str, Any]:
    """Project one prevalidated BYUM pointer into candidate-only metadata."""

    value = validate_pointer(pointer)
    prediction_id = value["prediction_id"]
    decision_ref = value["decision_ref"]
    projection = value["projection"]
    owner = _string(owner, "owner")
    consumers = ["*"] if consumers is None else list(consumers)
    if any(not isinstance(consumer, str) or not consumer.strip() for consumer in consumers):
        raise ValidationError("consumers darf nur nichtleere Zeichenketten enthalten")

    entry = {
        "id": f"byum-candidate:{prediction_id}@sha256:{projection['sha256']}",
        "kind": "decision-candidate",
        "title": f"BYUM decision candidate {decision_ref['decision_id']}",
        "summary": "Pointer-only BYUM v2 projection; no decision content is stored.",
        "scope": decision_ref["scope"],
        "owner": owner,
        "authority": "advisory-pointer",
        "priority": 0,
        "precedence": 0,
        "version": value["byum_protocol"],
        "hash": {"algorithm": "sha256", "value": projection["sha256"]},
        "privacy": "private",
        "source": {
            "uri": projection["uri"],
            "type": "byum-projection",
            "canonical": False,
            "origin": "build-your-users-mind",
        },
        "consumers": consumers,
        "status": "active",
        "adoption": "pending",
        "tags": ["byum", "decision-candidate", "pointer-only"],
        "provenance": {
            "protocol": value["byum_protocol"],
            "prediction_id": prediction_id,
            "decision_ref": decision_ref,
            "projection_status": projection["status"],
        },
    }
    return validate_entry(entry)


def register_candidate(
    registry: PolicyRegistry,
    pointer: dict[str, Any],
    *,
    owner: str = "BYUM",
    consumers: list[str] | None = None,
) -> dict[str, Any]:
    """Append one candidate pointer without replace or promotion semantics."""

    return registry.register(
        candidate_entry(pointer, owner=owner, consumers=consumers),
        replace=False,
    )


__all__ = [
    "BYUM_PROTOCOL",
    "POINTER_SCHEMA",
    "PROJECTION_STATUSES",
    "candidate_entry",
    "register_candidate",
    "validate_pointer",
]
