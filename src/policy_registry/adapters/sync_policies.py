from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..model import sha256_file
from ..registry import PolicyRegistry

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        title = next(
            (line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")),
            path.stem,
        )
        policy_id = path.name.split("_", 1)[0]
        return {"id": policy_id, "title": title, "scope": "system-wide", "status": "active"}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def import_sync_pointers(
    registry: PolicyRegistry,
    root: str | Path,
    *,
    slot: str,
    replace: bool = True,
) -> list[dict[str, Any]]:
    """Import metadata/pointers from the existing .SYNC/_policies layout."""
    root = Path(root)
    adoption_file = root / "adoption" / f"{slot}.json"
    sources_file = root / "sources" / f"{slot}.json"
    adoption = json.loads(adoption_file.read_text(encoding="utf-8"))
    sources = json.loads(sources_file.read_text(encoding="utf-8"))
    host = adoption.get("host") or sources.get("host") or slot
    entries: list[dict[str, Any]] = []

    for policy_file in sorted((root / "library").glob("P-*.md")):
        meta = _frontmatter(policy_file)
        policy_id = meta.get("id") or policy_file.name.split("_", 1)[0]
        adopted = adoption.get("policies", {}).get(policy_id, {})
        adoption_status = adopted.get("status", "pending")
        entries.append(
            {
                "id": policy_id,
                "kind": "policy",
                "title": meta.get("title", policy_file.stem),
                "summary": f"Pointer aus .SYNC/_policies/library; Adoption für {host}.",
                "scope": meta.get("scope", "system-wide"),
                "owner": meta.get("decided_by", "LG"),
                "authority": "explicit",
                "priority": 100,
                "precedence": 100,
                "version": meta.get("updated") or meta.get("created") or "1",
                "hash": {"algorithm": "sha256", "value": sha256_file(policy_file)},
                "privacy": "private",
                "source": {
                    "uri": str(policy_file.resolve()),
                    "type": "file",
                    "canonical": meta.get("canonical_text", "hier") == "hier",
                    "origin": ".SYNC/_policies/library",
                },
                "consumers": adopted.get("actors", ["*"]),
                "status": meta.get("status", "active"),
                "adoption": adoption_status if adoption_status in {"adopted", "partial", "pending", "exempt"} else "pending",
                "tags": [meta.get("category", "policy"), slot],
            }
        )

    for source in sources.get("sources", []):
        entries.append(
            {
                "id": f"source:{slot}:{source['id']}",
                "kind": "rule",
                "title": source.get("purpose") or source["id"],
                "summary": source.get("purpose", ""),
                "scope": source.get("pipeline") or "system-wide",
                "owner": host,
                "authority": "explicit-pointer",
                "priority": 50,
                "precedence": 50,
                "version": sources.get("updated", "1"),
                "privacy": "private",
                "source": {
                    "uri": source["path"],
                    "type": source.get("kind", "file"),
                    "canonical": True,
                    "origin": f".SYNC/_policies/sources/{slot}.json",
                    "include": source.get("include", []),
                    "depth": source.get("depth", 0),
                },
                "consumers": ["*"],
                "status": "active",
                "adoption": "adopted",
                "tags": [source.get("category", "rule-source"), slot],
            }
        )
    return registry.register_many(entries, replace=replace)


def export_aggregated_view(
    registry: PolicyRegistry, root: str | Path, *, slot: str
) -> Path:
    """Write a metadata-only host view inside the existing _policies structure."""
    root = Path(root)
    target = root / "registry" / f"{slot}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    data = registry.load()
    view = {
        "schema": "ellmos.policy-registry-view.v1",
        "slot": slot,
        "authority": "local-policy-registry",
        "registry_path": str(registry.path),
        "updated_at": data["updated_at"],
        "entries": data["entries"],
        "note": "Metadaten/Pointer, kein kanonischer Regelvolltext.",
    }
    target.write_text(json.dumps(view, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target

