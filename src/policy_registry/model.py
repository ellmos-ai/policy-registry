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
# D2-R2 Stufe 1 (T-20260825-601850637, Option C): kind=policy trägt Audit-/
# Driftschutz-Felder schon in der Praxis (jedes P-XXX hat hash+valid_from über
# register_decision_locations()/manuelle Registrierung). Fuer NEUE, ueber den
# Append-only-Weg (Registry.register_rule()) verwaltete kind=rule-Eintraege
# gilt dieselbe Pflicht -- durchgesetzt dort, NICHT im allgemeinen
# validate_entry()/register(): bestehende leichte kind=rule-Pointer (z.B.
# decisions.py "project-local-convention") wurden nie fuer diese
# Audit-Disziplin gebaut und sollen dadurch nicht rueckwirkend brechen.
RULE_AUDIT_REQUIRED = {"hash", "valid_from"}
ADOPTIONS = {"adopted", "partial", "pending", "exempt"}
PRIVACY = {"public", "internal", "private", "restricted"}
FORBIDDEN_CONTENT_KEYS = {"content", "body", "full_text", "fulltext", "payload"}


class ValidationError(ValueError):
    pass


def expand_uri(uri: str) -> Path | None:
    # Nicht-Dateisystem-Schemata: nichts zum Hashen, also auch nichts zu pruefen.
    # "usmc://" gehoert dazu -- USMC-Fakten liegen in der USMC-DB, nicht als Datei.
    # Fehlte es hier, landeten sie als "missing" in verify() und hielten das
    # Gesamtflag "ok" dauerhaft auf False (6 von 38 Eintraegen, gemessen 2026-09-05).
    if uri.startswith(("http://", "https://", "git+", "chat://", "usmc://")):
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

