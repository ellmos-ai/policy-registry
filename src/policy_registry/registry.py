from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .authority import (
    CHAT_AUTHORITY_ONLY,
    GOVERNANCE_BOUND,
    USER_SOVEREIGN,
    resolve_interaction_mode,
)
from .model import (
    AUTHORITATIVE_KINDS,
    RULE_AUDIT_REQUIRED,
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


def _parse_explicit_utc(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RegistryError(f"{label} muss ein expliziter UTC-Zeitstempel sein")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise RegistryError(f"{label} ist kein gültiger ISO-8601-Zeitstempel") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RegistryError(f"{label} muss eine UTC-Zeitzone enthalten")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z")


def _current_instruction(
    instruction: str | None,
    *,
    scope: str,
    session: str | None,
    instruction_at: str | None,
) -> dict[str, Any] | None:
    if instruction is None:
        return None
    if not isinstance(instruction, str) or not instruction.strip():
        raise RegistryError("current_instruction darf nicht leer sein")
    if len(instruction) > 4096:
        raise RegistryError("current_instruction darf höchstens 4096 Zeichen enthalten")
    instruction_value = instruction.strip()
    digest = hashlib.sha256(instruction_value.encode("utf-8")).hexdigest()
    source: dict[str, Any] = {
        "type": "chat-instruction",
        "session": session or "current-session",
    }
    if instruction_at is not None:
        source["captured_at"] = _parse_explicit_utc(instruction_at, "instruction_at")
    return {
        "id": f"current-user:{digest[:24]}",
        "kind": "current-user-instruction",
        "scope": scope,
        "authority": "current-user",
        "instruction": instruction_value,
        "hash": {"algorithm": "sha256", "value": digest},
        "source": source,
    }


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

    def register_rule(
        self, entry: dict[str, Any], *, supersedes: str | None = None
    ) -> dict[str, Any]:
        """Append-only registration for kind=rule (D2-R2 Stufe 1,
        T-20260825-601850637 Option C). Vorbild: session-checkpoints
        ADR-003/004/005-Muster (immutable rows + Hash-Verifikation +
        konservative destruktive Operationen), hier auf das bestehende
        registry.json übertragen statt eine neue Storage-Schicht zu bauen.

        Zwei Eigenschaften, die `register(replace=True)` NICHT hat:
        - Es gibt KEIN Ueberschreiben per gleicher `id`: ein Aufruf mit
          bereits vorhandener `id` schlägt immer fehl (RegistryError), auch
          ohne `replace`-Flag -- eine neue Version braucht eine neue `id`
          (Konvention: `<basis-id>@vN`).
        - `supersedes` markiert die Vorgänger-Zeile als abgelöst, OHNE ihren
          Inhalt zu verändern: nur `status` und `superseded_by` werden
          gesetzt, `hash`/`source`/`version`/alle übrigen Felder bleiben
          byte-identisch -- die alte Regel bleibt vollständig auditierbar,
          es wird nichts nachträglich umgeschrieben oder gelöscht.
        """
        if entry.get("kind") != "rule":
            raise RegistryError("register_rule() ist nur für kind=rule gedacht")
        missing_audit = sorted(k for k in RULE_AUDIT_REQUIRED if not entry.get(k))
        if missing_audit:
            raise RegistryError(
                "register_rule() verlangt Audit-Pflichtfelder: " + ", ".join(missing_audit)
            )
        entry = validate_entry(dict(entry))
        data = self.load()
        if any(item["id"] == entry["id"] for item in data["entries"]):
            raise RegistryError(
                f"Append-only: id existiert bereits, neue Version braucht neue id: {entry['id']}"
            )
        if supersedes is not None:
            predecessor = next((i for i in data["entries"] if i["id"] == supersedes), None)
            if predecessor is None:
                raise RegistryError(f"supersedes verweist auf unbekannte id: {supersedes}")
            if predecessor["kind"] != "rule":
                raise RegistryError("supersedes muss auf einen kind=rule-Eintrag zeigen")
            if predecessor.get("status") == "superseded":
                raise RegistryError(f"{supersedes} ist bereits superseded, Kette bricht")
            predecessor["status"] = "superseded"
            predecessor["superseded_by"] = entry["id"]
            entry["supersedes"] = supersedes
        data["entries"].append(entry)
        data["entries"].sort(key=lambda item: item["id"])
        self.save(data)
        return entry

    def propose_change(
        self,
        *,
        change_id: str,
        title: str,
        scope: str,
        owner: str,
        session: str,
        quote: str,
        captured_at: str,
        consumers: list[str] | None = None,
        priority: int = 100,
        precedence: int = 100,
        version: str = "1",
        privacy: str = "private",
    ) -> dict[str, Any]:
        """Record a chat instruction as a non-authoritative pending candidate."""
        if not isinstance(session, str) or not session.strip() or len(session) > 256:
            raise RegistryError("propose-change verlangt eine begrenzte Sitzungsquelle")
        if not isinstance(quote, str) or not quote.strip() or len(quote) > 4096:
            raise RegistryError("propose-change verlangt ein Zitat mit höchstens 4096 Zeichen")
        captured = _parse_explicit_utc(captured_at, "captured_at")
        session_value = session.strip()
        quote_value = quote.strip()
        quote_hash = hashlib.sha256(quote_value.encode("utf-8")).hexdigest()
        session_token = hashlib.sha256(session_value.encode("utf-8")).hexdigest()[:24]
        candidate = {
            "id": change_id,
            "kind": "decision-candidate",
            "title": title,
            "summary": "Chat instruction proposed for explicit governance adoption.",
            "scope": scope,
            "owner": owner,
            "authority": "chat-proposal",
            "priority": priority,
            "precedence": precedence,
            "version": version,
            "hash": {"algorithm": "sha256", "value": quote_hash},
            "privacy": privacy,
            "source": {
                "uri": f"chat://session/{session_token}",
                "type": "chat-instruction",
                "canonical": True,
                "session": session_value,
                "quote": quote_value,
                "captured_at": captured,
            },
            "consumers": consumers or ["*"],
            "status": "active",
            "adoption": "pending",
            "tags": ["decision-change", "chat-instruction", "pending-adoption"],
        }
        return self.register(candidate)

    def adopt_change(
        self,
        candidate_id: str,
        *,
        rule_id: str,
        adopted_at: str,
        supersedes: str | None = None,
    ) -> dict[str, Any]:
        """Explicitly adopt a pending proposal as an audited append-only rule."""
        candidate = self.get(candidate_id)
        if candidate is None:
            raise RegistryError(f"Unbekannter Entscheidungskandidat: {candidate_id}")
        if candidate.get("kind") != "decision-candidate":
            raise RegistryError("adopt verlangt einen kind=decision-candidate-Eintrag")
        if candidate.get("adoption") != "pending":
            raise RegistryError(f"Entscheidungskandidat ist bereits adoptiert: {candidate_id}")
        adopted = _parse_explicit_utc(adopted_at, "adopted_at")
        source = candidate.get("source")
        if not isinstance(source, dict):
            raise RegistryError("Entscheidungskandidat hat keine vollständige Chat-Provenienz")
        source_quote = source.get("quote")
        source_session = source.get("session")
        source_time = source.get("captured_at")
        if (
            not isinstance(source_quote, str)
            or not source_quote
            or not isinstance(source_session, str)
            or not source_session
            or not isinstance(source_time, str)
        ):
            raise RegistryError("Entscheidungskandidat hat keine vollständige Chat-Provenienz")
        _parse_explicit_utc(source_time, "source.captured_at")
        quote_hash = hashlib.sha256(source_quote.encode("utf-8")).hexdigest()
        if candidate.get("hash") != {"algorithm": "sha256", "value": quote_hash}:
            raise RegistryError("Entscheidungskandidat-Hash stimmt nicht mit dem Zitat überein")

        rule = {
            "id": rule_id,
            "kind": "rule",
            "title": candidate["title"],
            "summary": candidate.get("summary", "Adopted decision change."),
            "scope": candidate["scope"],
            "owner": candidate["owner"],
            "authority": "explicit",
            "priority": candidate["priority"],
            "precedence": candidate["precedence"],
            "version": candidate["version"],
            "hash": dict(candidate["hash"]),
            "valid_from": adopted[:10],
            "privacy": candidate["privacy"],
            "source": dict(source),
            "consumers": list(candidate["consumers"]),
            "status": "active",
            "adoption": "adopted",
            "adopted_from": candidate_id,
            "adopted_at": adopted,
        }
        registered_rule = self.register_rule(rule, supersedes=supersedes)

        data = self.load()
        stored_candidate = next(
            (item for item in data["entries"] if item["id"] == candidate_id),
            None,
        )
        if stored_candidate is None or stored_candidate.get("adoption") != "pending":
            raise RegistryError("Entscheidungskandidat änderte sich während der Adoption")
        stored_candidate["adoption"] = "adopted"
        stored_candidate["adopted_as"] = rule_id
        stored_candidate["adopted_at"] = adopted
        self.save(data)
        return {"candidate": stored_candidate, "rule": registered_rule}

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
        mode: str | None = None,
        project_root: str | Path | None = None,
        current_instruction: str | None = None,
        session: str | None = None,
        instruction_at: str | None = None,
    ) -> dict[str, Any]:
        governance = self._resolve_governance(
            scope=scope,
            consumer=consumer,
            query=query,
            required_kind=required_kind,
        )
        interaction = resolve_interaction_mode(
            session_mode=mode,
            project_root=project_root,
        )
        instruction = _current_instruction(
            current_instruction,
            scope=scope,
            session=session,
            instruction_at=instruction_at,
        )
        effective = interaction["mode"]
        result = dict(governance)
        result.update(
            {
                "interaction_mode": effective,
                "interaction_effective": effective,
                "interaction_source": interaction["source"],
                "interaction_issue": interaction["issue"],
                "current_instruction": instruction,
                "governance": {
                    "status": governance["status"],
                    "selected_id": (
                        governance["selected"]["id"]
                        if governance["selected"] is not None
                        else None
                    ),
                    "candidate_ids": [item["id"] for item in governance["candidates"]],
                    "reason": governance["reason"],
                },
                "governance_binding": effective == GOVERNANCE_BOUND,
                "change_proposal_required": False,
                "reconciliation": {
                    "required": False,
                    "candidate_ids": [],
                    "automatic": False,
                },
                "external_effect_gates": "user-controlled",
            }
        )

        if effective == GOVERNANCE_BOUND:
            if governance["status"] == "resolved":
                result["change_proposal_required"] = instruction is not None
                if instruction is not None:
                    result["reason"] = (
                        "Governance outranks the current chat instruction; "
                        "use propose-change and explicit adoption to change it."
                    )
                return result
            if (
                governance["status"] == "missing"
                and instruction is not None
                and required_kind is None
            ):
                instruction["binding"] = "no-governance-found"
                result.update(
                    status="resolved",
                    selected=instruction,
                    reason="No applicable governance entry; current chat instruction applies.",
                    fallback=None,
                )
            return result

        if effective == USER_SOVEREIGN:
            result["governance_binding"] = False
            if instruction is not None:
                instruction["binding"] = "current-user-will"
                candidate_ids = sorted(item["id"] for item in governance["candidates"])
                result.update(
                    status="resolved",
                    selected=instruction,
                    reason="Current user will outranks stored governance in user-sovereign mode.",
                    fallback=None,
                    reconciliation={
                        "required": bool(candidate_ids),
                        "candidate_ids": candidate_ids,
                        "automatic": False,
                    },
                )
            return result

        if effective == CHAT_AUTHORITY_ONLY:
            result["governance_binding"] = False
            if instruction is not None:
                instruction["binding"] = "chat-only"
                result.update(
                    status="resolved",
                    selected=instruction,
                    reason="Chat is the only binding interaction authority in this mode.",
                    fallback=None,
                )
            else:
                result.update(
                    status="missing",
                    selected=None,
                    reason="chat-authority-only requires a current chat instruction.",
                    fallback=None,
                )
            return result

        raise RegistryError(f"Nicht erreichbarer Interaktionsmodus: {effective}")

    def _resolve_governance(
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
