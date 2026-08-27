"""The required bundle member stays a guarded runtime probe."""

import ast
import inspect
import json
from pathlib import Path

from policy_registry.adapters import decision_clicker

ROOT = Path(__file__).resolve().parents[1]


def test_available_returns_a_plain_bool_without_raising():
    result = decision_clicker.available()
    assert isinstance(result, bool)


def test_seam_module_only_imports_decision_clicker_inside_the_guarded_probe():
    source = inspect.getsource(decision_clicker)
    tree = ast.parse(source)
    module_level_imports = [
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    for node in module_level_imports:
        names = [alias.name for alias in node.names]
        assert "decision_clicker" not in names, (
            "adapters/decision_clicker.py must only import decision_clicker "
            "inside the guarded available() probe, never at module scope."
        )


def test_manifest_requires_decision_clicker_capability():
    data = json.loads((ROOT / "ellmos-module.v2.json").read_text(encoding="utf-8"))
    assert "decision.clicker" in data["requires"]
    assert "decision.clicker" not in data["optional"]
    seams = [item for item in data["adapters"] if item.get("id") == "decision-clicker-v1"]
    assert len(seams) == 1
    assert seams[0]["status"] == "required"
