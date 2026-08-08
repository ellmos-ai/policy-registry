from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .model import (
    AUTHORITATIVE_KINDS,
    SCHEMA,
    ValidationError,
    expand_uri,
    is_valid_now,
    sha256_file,
    validate_entry,
)
from .scope import consumer_matches, scope_matches, scope_precedence


class RegistryError(RuntimeError):
    pass


def default_registry_path() -> Path:
    configured = os.environ.get("POLICY_REGISTRY_PATH")
    if configured:
        return Path(os.path.expandvars(os.path.expanduser(configured)))
    return Path.home() / ".policy-registry" / "registry.json"


class PolicyRegistry:
    """Metadata-only registry. Canonical rule text stays at source.uri."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_registry_path()

    def _empty(self) -> dict[str, Any]:
        return {"schema": SCHEMA, "updated_at": None, "entries": []}

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RegistryError(f"Registry nicht lesbar: {self.path}: {exc}") from exc
        if data.get("schema") != SCHEMA or not isinstance(data.get("entries"), list):
            raise RegistryError(f"Ungültiges Registry-Format: {self.path}")
        for entry in data["entries"]:
            validate_entry(entry)
        return data

    def save(self, data: dict[str, Any]) -> None:
        data["schema"] = SCHEMA
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        for entry in data["entries"]:
            validate_entry(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, self.path)

    def init(self) -> Path:
        if not self.path.exists():
            self.save(self._empty())
        return self.path

    def register(self, entry: dict[str, Any], *, replace: bool = False) -> dict[str, Any]:
        entry = validate_entry(dict(entry))
        data = self.load()
        matches = [index for index, item in enumerate(data["entries"]) if item["id"] == entry["id"]]
        if matches and not replace:
            raise RegistryError(f"Eintrag existiert bereits: {entry['id']}")
        if matches:
            data["entries"][matches[0]] = entry
        else:
            data["entries"].append(entry)
        data["entries"].sort(key=lambda item: item["id"])
        self.save(data)
        return entry

    def register_many(
        self, entries: Iterable[dict[str, Any]], *, replace: bool = False
    ) -> list[dict[str, Any]]:
        data = self.load()
        by_id = {item["id"]: item for item in data["entries"]}
        registered = []
        for raw in entries:
            entry = validate_entry(dict(raw))
            if entry["id"] in by_id and not replace:
                raise RegistryError(f"Eintrag existiert bereits: {entry['id']}")
            by_id[entry["id"]] = entry
            registered.append(entry)
        data["entries"] = sorted(by_id.values(), key=lambda item: item["id"])
        self.save(data)
        return registered

    def get(self, entry_id: str) -> dict[str, Any] | None:
        return next((e for e in self.load()["entries"] if e["id"] == entry_id), None)

    def search(
        self,
        query: str = "",
        *,
        scope: str | None = None,
        consumer: str | None = None,
        kind: str | None = None,
    ) -> list[dict[str, Any]]:
        needle = query.casefold()
        results = []
        for entry in self.load()["entries"]:
            haystack = " ".join(
                [
                    entry["id"],
                    entry["title"],
                    entry.get("summary", ""),
                    " ".join(entry.get("tags", [])),
                ]
            ).casefold()
            if needle and needle not in haystack:
                continue
            if scope and not scope_matches(entry.get("scope"), scope):
                continue
            if not consumer_matches(entry.get("consumers"), consumer):
                continue
            if kind and entry["kind"] != kind:
                continue
            results.append(entry)
        return results

    def resolve(
        self,
        *,
        scope: str,
        consumer: str | None = None,
        query: str = "",
        required_kind: str | None = None,
    ) -> dict[str, Any]:
        candidates = [
            entry
            for entry in self.search(query, scope=scope, consumer=consumer)
            if entry["kind"] in AUTHORITATIVE_KINDS and is_valid_now(entry)
        ]
        if required_kind:
            candidates = [entry for entry in candidates if entry["kind"] == required_kind]
        candidates.sort(
            key=lambda item: (
                *scope_precedence(item["scope"], scope),
                item["priority"],
                item["precedence"],
                item["version"],
                item["id"],
            ),
            reverse=True,
        )
        reason = None
        if not candidates:
            status = "missing" if not required_kind else "insufficient"
            selected = None
            reason = "Keine gültige, explizit adoptierte Norm gefunden."
        else:
            top = candidates[0]
            top_key = (
                *scope_precedence(top["scope"], scope),
                top["priority"],
                top["precedence"],
            )
            ties = []
            for item in candidates:
                item_key = (
                    *scope_precedence(item["scope"], scope),
                    item["priority"],
                    item["precedence"],
                )
                if item_key == top_key:
                    ties.append(item)
            if len(ties) > 1:
                status = "conflict"
                selected = None
                reason = "Mehrere Normen teilen höchste Priorität und Präzedenz."
            else:
                status = "resolved"
                selected = top
        result = {
            "status": status,
            "selected": selected,
            "candidates": candidates,
            "reason": reason,
            "fallback": None,
        }
        if status != "resolved":
            result["fallback"] = {
                "provider": "TOM-lm",
                "mode": "advisory",
                "automatic_authority": False,
                "result_role": "evidence-or-decision-candidate",
                "general_policy_requires_explicit_adoption": True,
            }
        return result

    def verify(self) -> dict[str, Any]:
        entries = self.load()["entries"]
        checks = []
        for entry in entries:
            source_path = expand_uri(entry["source"]["uri"])
            if source_path is None:
                checks.append({"id": entry["id"], "state": "remote-unchecked"})
                continue
            if not source_path.exists():
                checks.append({"id": entry["id"], "state": "missing"})
                continue
            expected = (entry.get("hash") or {}).get("value")
            if expected and source_path.is_file():
                actual = sha256_file(source_path)
                checks.append(
                    {
                        "id": entry["id"],
                        "state": "ok" if actual == expected else "hash-mismatch",
                        "actual": actual,
                    }
                )
            else:
                checks.append({"id": entry["id"], "state": "present"})
        return {
            "registry": str(self.path),
            "entries": len(entries),
            "checks": checks,
            "ok": all(item["state"] not in {"missing", "hash-mismatch"} for item in checks),
        }

__all__ = ["PolicyRegistry", "RegistryError", "ValidationError"]
