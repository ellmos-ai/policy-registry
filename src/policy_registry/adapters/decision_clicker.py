"""Guarded availability probe for the required decision-bundle writer/UI.

The 2026-08-27 user decision supersedes the optional composition choice from
ticket T-20260824-474639761: ``policy-registry`` now requires the
``decision.clicker`` capability in its module manifest.

Composition and Python import coupling remain separate. Both tools cooperate
through the same on-disk ``_DECISIONS`` chain: policy-registry reads and
indexes location pointers, while decision-clicker performs controlled writes
and provides the human UI. Neither needs to import the other's internals.

This module therefore remains a guarded availability probe with no module-
level import. A false result means the complete decision-system bundle is not
available; it does not prevent pointer-only maintenance or recovery commands
inside policy-registry itself.
"""

from __future__ import annotations


def available() -> bool:
    """Whether the sibling ``decision-clicker`` package is importable.

    The manifest requires decision-clicker for a complete decision-system
    bundle. This guarded probe lets callers report whether that required
    writer/UI is importable without creating a package-level import cycle.
    """
    try:
        import decision_clicker  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        return False
    return True


__all__ = ["available"]
