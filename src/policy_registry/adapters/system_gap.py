from __future__ import annotations

from pathlib import Path

from ..registry import PolicyRegistry
from .sync_policies import export_aggregated_view


def available() -> bool:
    try:
        import system_gap_master  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        return False
    return True


def publish_view(
    registry: PolicyRegistry, sync_root: str | Path, *, slot: str
) -> Path:
    """
    Optional seam for a system-gap installation.

    The registry remains authoritative. The adapter deliberately writes only a
    metadata view into the existing ``_policies`` structure and never requires
    system-gap-master for offline operation.
    """
    return export_aggregated_view(registry, Path(sync_root) / "_policies", slot=slot)

