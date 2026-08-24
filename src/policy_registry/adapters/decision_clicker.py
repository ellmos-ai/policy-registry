"""Optional seam onto the sibling ``decision-clicker`` tool.

Mechanic choice (ticket T-20260824-474639761, F2): decision-clicker is
registered as an OPTIONAL, importable seam -- the same lightweight pattern
already used for ``system_gap.py`` -- rather than a fixed manifest bundle
binding. Reasons, so a later reader does not have to re-derive them:

1. decision-clicker still carries an open PRIVATE.txt condition (personal
   chain paths in ``config.py`` are not yet made configurable) and unrelated
   work-in-progress at the time of this seam; a hard bundle dependency would
   couple policy-registry's release cadence to that unfinished state.
2. decision-clicker must stay independently, manually startable
   (``START.bat`` / ``python -m decision_clicker``) per the user decision --
   a fixed bundle binding in the module manifest would suggest the opposite,
   that policy-registry pulls it in as a required component.
3. The real coupling between the two tools is DATA, not code: both point at
   the same ``_DECISIONS`` chain (policy-registry as a pointer/index reader,
   decision-clicker as the writer/UI). Neither needs to import the other's
   internals to cooperate; policy-registry's ``adapters.decisions`` module
   already expresses the shared location contract.

This module therefore only offers an availability probe. It performs no
import at module load time and policy-registry's own tests/CI never install
decision-clicker, keeping the optional relationship truly optional.
"""

from __future__ import annotations


def available() -> bool:
    """Whether the sibling ``decision-clicker`` package is importable.

    policy-registry never requires decision-clicker; this only lets a caller
    (CLI, MCP adapter, another module) check whether the tool that WRITES
    into the same decision chain happens to be installed alongside, without
    the caller needing to know decision-clicker's import path itself.
    """
    try:
        import decision_clicker  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        return False
    return True


__all__ = ["available"]
