"""POLICY_AUTHORITY_MODE -- dünner, additiver Schalter für ein künftiges
Autoritäts-Handover an USMC (D2-R2 Stufe 1, T-20260825-601850637 Option C).

WICHTIG: Dieses Modul bereitet den Schalter nur VOR. Es gibt heute keinen
Umbau von USMC und keine echte Handover-Logik -- policy-registry bleibt in
jedem Modus die alleinige Autorität für kind=policy/rule/decision. Die
eigentliche Entscheidung, ob/wann Autorität an USMC wandert, ist Stufe 2
(separates Folgeticket) und wird hier bewusst NICHT vorweggenommen.

Drei Modi:
- "policy-only" (Default, Status quo): policy-registry ist alleinige
  Autorität, unabhängig davon, ob USMC erreichbar ist.
- "memory-only": vorbereitet für den Fall, dass Autorität vollständig an
  USMC wandert (Stufe 2/3-Zielbild) -- heute NICHT aktiv, nur die
  Konstante existiert schon, damit spätere Umsetzung keinen neuen
  Modusnamen erfinden muss.
- "memory+policy": vorbereitet für einen hybriden Zwischenzustand (beide
  Quellen gelten parallel, Konfliktauflösung wäre Stufe-2-Arbeit) --
  ebenfalls heute nicht aktiv.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

POLICY_ONLY = "policy-only"
MEMORY_ONLY = "memory-only"
MEMORY_AND_POLICY = "memory+policy"
KNOWN_MODES = {POLICY_ONLY, MEMORY_ONLY, MEMORY_AND_POLICY}

ENV_VAR = "POLICY_AUTHORITY_MODE"
DEFAULT_MODE = POLICY_ONLY

# Independent interaction/ranking axis. Unlike POLICY_AUTHORITY_MODE, this
# axis is effective: it controls how the same registry candidates and the
# current chat instruction are ranked.
CHAT_AUTHORITY_ONLY = "chat-authority-only"
GOVERNANCE_BOUND = "governance-bound"
USER_SOVEREIGN = "user-sovereign"
KNOWN_INTERACTION_MODES = {
    CHAT_AUTHORITY_ONLY,
    GOVERNANCE_BOUND,
    USER_SOVEREIGN,
}
INTERACTION_ENV_VAR = "POLICY_INTERACTION_MODE"
DEFAULT_INTERACTION_MODE = GOVERNANCE_BOUND
PROJECT_CONFIG = ".policy-registry.toml"


def _interaction_fallback(source: str, issue: str, config_path: Path | None = None) -> dict[str, Any]:
    return {
        "mode": DEFAULT_INTERACTION_MODE,
        "source": source,
        "config_path": str(config_path) if config_path else None,
        "issue": issue,
    }


def resolve_interaction_mode(
    *,
    session_mode: str | None = None,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve session > project > safe default for the interaction mode.

    The explicit API/CLI argument and ``POLICY_INTERACTION_MODE`` are both
    session-level choices; the explicit argument wins. Invalid or ambiguous
    configuration never falls through to a less restrictive mode. It fails
    closed to ``governance-bound`` and reports the issue.
    """
    if session_mode is not None:
        if session_mode in KNOWN_INTERACTION_MODES:
            return {
                "mode": session_mode,
                "source": "session-argument",
                "config_path": None,
                "issue": None,
            }
        return _interaction_fallback(
            "session-invalid-fallback",
            f"Unbekannter Sitzungsmodus: {session_mode}",
        )

    environment_mode = os.environ.get(INTERACTION_ENV_VAR)
    if environment_mode is not None:
        if environment_mode in KNOWN_INTERACTION_MODES:
            return {
                "mode": environment_mode,
                "source": "session-environment",
                "config_path": None,
                "issue": None,
            }
        return _interaction_fallback(
            "session-invalid-fallback",
            f"Unbekannter Wert in {INTERACTION_ENV_VAR}: {environment_mode}",
        )

    root = Path(project_root) if project_root is not None else Path.cwd()
    config_path = root / PROJECT_CONFIG
    if config_path.exists():
        try:
            with config_path.open("rb") as handle:
                config = tomllib.load(handle)
            section = config.get("policy_registry")
            if not isinstance(section, dict):
                raise ValueError("Abschnitt [policy_registry] fehlt")
            project_mode = section.get("interaction_mode")
            if project_mode not in KNOWN_INTERACTION_MODES:
                raise ValueError(f"unbekannter interaction_mode: {project_mode}")
        except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
            return _interaction_fallback(
                "project-invalid-fallback",
                f"Projekt-TOML ist ungültig: {exc}",
                config_path,
            )
        return {
            "mode": project_mode,
            "source": "project",
            "config_path": str(config_path),
            "issue": None,
        }

    return {
        "mode": DEFAULT_INTERACTION_MODE,
        "source": "default",
        "config_path": str(config_path),
        "issue": None,
    }


def current_interaction_mode(
    *,
    session_mode: str | None = None,
    project_root: str | Path | None = None,
) -> str:
    """Return only the effective interaction mode."""
    return str(
        resolve_interaction_mode(
            session_mode=session_mode,
            project_root=project_root,
        )["mode"]
    )


def current_mode() -> str:
    """Liest den konfigurierten Modus; fällt auf den sicheren Default
    zurück, wenn die Variable fehlt oder einen unbekannten Wert trägt
    (fail-closed auf den heutigen Status quo, nie auf einen der beiden
    noch ungebauten Modi)."""
    value = os.environ.get(ENV_VAR, DEFAULT_MODE)
    return value if value in KNOWN_MODES else DEFAULT_MODE


def usmc_present() -> dict[str, object]:
    """Reine Anwesenheits-Prüfung, KEINE Autoritätsentscheidung: ist das
    `usmc`-Paket auf diesem Host importierbar und die kanonische DB-Datei
    vorhanden? Wird von Stufe 2 gebraucht, wenn Handover-Logik entsteht --
    heute nur beobachtbar, nicht wirksam."""
    importable = importlib.util.find_spec("usmc") is not None
    db_path = os.path.expanduser(os.path.expandvars("~/.usmc/usmc_memory.db"))
    return {
        "importable": importable,
        "db_path": db_path,
        "db_exists": os.path.isfile(db_path),
    }


def describe(
    *,
    session_mode: str | None = None,
    project_root: str | Path | None = None,
) -> dict[str, object]:
    """Report the inert source axis and effective interaction axis."""
    mode = current_mode()
    interaction = resolve_interaction_mode(
        session_mode=session_mode,
        project_root=project_root,
    )
    return {
        "mode": mode,
        "effective": POLICY_ONLY,  # source axis remains intentionally inert
        "interaction_mode": interaction["mode"],
        "interaction_effective": interaction["mode"],
        "interaction_source": interaction["source"],
        "interaction_config_path": interaction["config_path"],
        "interaction_issue": interaction["issue"],
        "note": (
            "POLICY_AUTHORITY_MODE bleibt ein vorbereiteter Quellen-Schalter; "
            "die unabhängige Interaktionsachse ist wirksam und rangiert Chat "
            "und Governance. TOM-lm/BYUM bleiben beratend."
        ),
        "usmc": usmc_present(),
    }
