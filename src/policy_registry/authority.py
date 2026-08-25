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

POLICY_ONLY = "policy-only"
MEMORY_ONLY = "memory-only"
MEMORY_AND_POLICY = "memory+policy"
KNOWN_MODES = {POLICY_ONLY, MEMORY_ONLY, MEMORY_AND_POLICY}

ENV_VAR = "POLICY_AUTHORITY_MODE"
DEFAULT_MODE = POLICY_ONLY


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


def describe() -> dict[str, object]:
    """Kompakter Statusbericht für CLI/Diagnose: konfigurierter Modus,
    USMC-Anwesenheit, und die ausdrückliche Klarstellung, dass der Modus
    heute nichts am Verhalten ändert (nur `policy-only` ist verdrahtet)."""
    mode = current_mode()
    return {
        "mode": mode,
        "effective": POLICY_ONLY,  # heute IMMER policy-only, unabhängig vom Schalter
        "note": (
            "Schalter ist vorbereitet, aber wirkungslos: policy-registry bleibt "
            "in dieser Stufe (Stufe 1) in jedem Modus die alleinige Autorität. "
            "Echtes Handover ist Stufe 2 (eigenes Folgeticket)."
        ),
        "usmc": usmc_present(),
    }
