"""Pointer-only seam onto the real _DECISIONS locations.

This adapter never stores decision text. It registers a small, deliberately
short list of STABLE location pointers -- where the real decision ledgers
live -- not one entry per individual decision. Individual decisions keep
living exactly where they already live (the TO-DECIDE-USER chain,
DECIDED-AND-DONE.md, project-local DECISIONS.md); this module only makes
those locations discoverable and verifiable (source + optional hash) from
the registry.

USER decision 2026-08-24 (F1=A-hybrid, ticket T-20260824-474639761 out of
T-20260824-911756255): policy-registry becomes the one place that KNOWS
where decision records live, via pointers -- not a second store of decision
content.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from ..registry import PolicyRegistry

#: Shared scope for every location pointer registered by this adapter.
#: A query for this scope (or any "decisions/..." descendant) resolves them.
LOCATIONS_SCOPE = "decisions"


def _uri(path: Path) -> str:
    return str(path.resolve()) if path.exists() else str(path)


def location_entries(
    control_center_root: str | Path,
    *,
    curated_on: str | None = None,
    owner: str = "LG",
) -> list[dict[str, Any]]:
    """Build the stable decision-location pointer entries.

    ``control_center_root`` is the ``_control-center`` directory (the parent
    of both ``_DECISIONS`` and ``.AI/_templates/project-docs``, one level
    below ``.TOPICS``). Entries always point at the conventional path, even
    when it does not (yet) exist on this checkout -- ``PolicyRegistry.verify``
    is the place that reports a missing source, not this builder.
    """
    root = Path(control_center_root)
    decisions_root = root / "_DECISIONS"
    templates_root = root.parent / ".AI" / "_templates" / "project-docs"
    version = curated_on or date.today().isoformat()

    chain_head = decisions_root / "TO-DECIDE-USER.txt"
    decided = decisions_root / "DECIDED-AND-DONE.md"
    index_file = decisions_root / "decisions.index.json"
    convention = templates_root / "DECISIONS.md"

    return [
        {
            "id": "decision-location:chain-head",
            "kind": "decision",
            "title": "Globale Entscheidungskette -- Einstiegspunkt",
            "summary": (
                "Kopf der aktiven TO-DECIDE-USER-Kette (Cut-and-Clue-Verfahren; "
                "Fortsetzungen ueber bidirektionale Pointer, z.B. _2.txt.._N.txt). "
                "Die verbindliche Entscheidungsregel steht im Kopf dieser Datei."
            ),
            "scope": LOCATIONS_SCOPE,
            "owner": owner,
            "authority": "location-pointer",
            "priority": 60,
            "precedence": 60,
            "version": version,
            "privacy": "private",
            "source": {
                "uri": _uri(chain_head),
                "type": "file",
                "canonical": True,
                "origin": "_control-center/_DECISIONS",
            },
            "consumers": ["*"],
            "status": "active",
            "adoption": "adopted",
            "tags": ["decisions", "location-pointer"],
        },
        {
            "id": "decision-location:host-file-pattern",
            "kind": "decision",
            "title": "Hostbezogene Entscheidungsdatei (Namensmuster)",
            "summary": (
                "Konvention TO-DECIDE-USER-<HOST>.txt je Host, z.B. "
                "TO-DECIDE-USER-ASUS-GEI.txt. Globale Entscheidungen werden nicht "
                "dupliziert; jeder Host liest zusaetzlich die globale Kette."
            ),
            "scope": LOCATIONS_SCOPE,
            "owner": owner,
            "authority": "location-pointer",
            "priority": 55,
            "precedence": 55,
            "version": version,
            "privacy": "private",
            "source": {
                "uri": _uri(decisions_root),
                "type": "directory",
                "canonical": True,
                "origin": "_control-center/_DECISIONS",
                "pattern": "TO-DECIDE-USER-<HOST>.txt",
            },
            "consumers": ["*"],
            "status": "active",
            "adoption": "adopted",
            "tags": ["decisions", "location-pointer"],
        },
        {
            "id": "decision-location:decided-and-done",
            "kind": "decision",
            "title": "Verifizierte, umgesetzte Entscheidungen (Ledger)",
            "summary": (
                "DECIDED-AND-DONE.md -- append-only Ablage bereits verifiziert "
                "umgesetzter Entscheidungen (aktiv, kein Archiv)."
            ),
            "scope": LOCATIONS_SCOPE,
            "owner": owner,
            "authority": "location-pointer",
            "priority": 55,
            "precedence": 55,
            "version": version,
            "privacy": "private",
            "source": {
                "uri": _uri(decided),
                "type": "file",
                "canonical": True,
                "origin": "_control-center/_DECISIONS",
            },
            "consumers": ["*"],
            "status": "active",
            "adoption": "adopted",
            "tags": ["decisions", "location-pointer"],
        },
        {
            "id": "decision-location:machine-index",
            "kind": "evidence",
            "title": "Maschinenlesbarer Entscheidungsindex (generiert)",
            "summary": (
                "decisions.index.json / INDEX-REPORT.md -- generierte Artefakte "
                "ueber die gesamte Kette (_tools/decisions_index.py). Kanonisch "
                "bleiben die Kettendateien selbst, nicht der Index."
            ),
            "scope": LOCATIONS_SCOPE,
            "owner": owner,
            "authority": "location-pointer",
            "priority": 40,
            "precedence": 40,
            "version": version,
            "privacy": "private",
            "source": {
                "uri": _uri(index_file),
                "type": "file",
                "canonical": False,
                "origin": "_control-center/_DECISIONS/_tools",
            },
            "consumers": ["*"],
            "status": "active",
            "adoption": "adopted",
            "tags": ["decisions", "location-pointer", "generated"],
        },
        {
            "id": "decision-location:project-local-convention",
            "kind": "rule",
            "title": "Projektlokale DECISIONS.md-Konvention",
            "summary": (
                "Projektbezogene DECISIONS.md/TO-DECIDE.md/DECIDED-AND-DONE.md haben "
                "in ihrem Projektscope Vorrang vor der zentralen Kette; nur bei "
                "tatsaechlich projektuebergreifenden Fragen zentral eskalieren. "
                "Vorlage/ADR-Format hier."
            ),
            "scope": LOCATIONS_SCOPE,
            "owner": owner,
            "authority": "location-pointer",
            "priority": 50,
            "precedence": 50,
            "version": version,
            "privacy": "private",
            "source": {
                "uri": _uri(convention),
                "type": "file",
                "canonical": True,
                "origin": ".AI/_templates/project-docs",
            },
            "consumers": ["*"],
            "status": "active",
            "adoption": "adopted",
            "tags": ["decisions", "location-pointer", "convention"],
        },
    ]


def register_decision_locations(
    registry: PolicyRegistry,
    control_center_root: str | Path,
    *,
    curated_on: str | None = None,
    owner: str = "LG",
    replace: bool = True,
) -> list[dict[str, Any]]:
    """Register the stable decision-location pointers in the local registry.

    Pointer-only per the module's schema: no decision text is read or
    stored, only ``id``/``title``/``summary``/``source.uri`` metadata.
    """
    entries = location_entries(control_center_root, curated_on=curated_on, owner=owner)
    return registry.register_many(entries, replace=replace)


__all__ = ["LOCATIONS_SCOPE", "location_entries", "register_decision_locations"]
