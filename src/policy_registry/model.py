from __future__ import annotations

import hashlib
import os
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA = "ellmos.policy-registry.v1"
ENTRY_KINDS = {"policy", "rule", "decision", "evidence", "decision-candidate"}
AUTHORITATIVE_KINDS = {"policy", "rule", "decision"}
STATUSES = {"active", "draft", "superseded", "revoked", "expired"}
ADOPTIONS = {"adopted", "partial", "pending", "exempt"}
PRIVACY = {"public", "internal", "private", "restricted"}
FORBIDDEN_CONTENT_KEYS = {"content", "body", "full_text", "fulltext", "payload"}


class ValidationError(ValueError):
    pass


def expand_uri(uri: str) -> Path | None:
    if uri.startswith(("http://", "https://", "git+")):
        return None
    expanded = os.path.expandvars(os.path.expanduser(uri))
    return Path(expanded)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    required = {
        "id", "kind", "title", "scope", "owner", "priority", "precedence",
        "version", "privacy", "source", "consumers", "status", "adoption",
    }
    missing = sorted(required - entry.keys())
    if missing:
        raise ValidationError(f"Fehlende Felder: {', '.join(missing)}")
    forbidden = sorted(FORBIDDEN_CONTENT_KEYS & entry.keys())
    if forbidden:
        raise ValidationError(
            "Registry speichert keinen Volltext; unzulässige Felder: "
            + ", ".join(forbidden)
        )
    if entry["kind"] not in ENTRY_KINDS:
        raise ValidationError(f"Unbekannter kind-Wert: {entry['kind']}")
    if entry["status"] not in STATUSES:
        raise ValidationError(f"Unbekannter status-Wert: {entry['status']}")
    if entry["adoption"] not in ADOPTIONS:
        raise ValidationError(f"Unbekannter adoption-Wert: {entry['adoption']}")
    if entry["privacy"] not in PRIVACY:
        raise ValidationError(f"Unbekannter privacy-Wert: {entry['privacy']}")
    if not isinstance(entry["priority"], int) or not isinstance(entry["precedence"], int):
        raise ValidationError("priority und precedence müssen Ganzzahlen sein")
    if not isinstance(entry["consumers"], list):
        raise ValidationError("consumers muss eine Liste sein")
    source = entry["source"]
    if not isinstance(source, dict) or not source.get("uri"):
        raise ValidationError("source.uri ist erforderlich")
    if FORBIDDEN_CONTENT_KEYS & source.keys():
        raise ValidationError("source darf keinen Volltext enthalten")
    hash_value = entry.get("hash")
    if hash_value is not None:
        if not isinstance(hash_value, dict):
            raise ValidationError("hash muss ein Objekt sein")
        if hash_value.get("algorithm") != "sha256":
            raise ValidationError("MVP unterstützt nur sha256")
        value = hash_value.get("value", "")
        if value and (len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower())):
            raise ValidationError("Ungültiger SHA-256-Wert")
    return entry


def is_valid_now(entry: dict[str, Any], today: date | None = None) -> bool:
    today = today or date.today()
    if entry["status"] != "active":
        return False
    if entry["adoption"] != "adopted":
        return False
    valid_from = entry.get("valid_from")
    valid_until = entry.get("valid_until")
    if valid_from and date.fromisoformat(valid_from) > today:
        return False
    if valid_until and date.fromisoformat(valid_until) < today:
        return False
    return True

