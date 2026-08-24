"""The decision-clicker seam is optional: it must never require the package."""

import ast
import inspect

from policy_registry.adapters import decision_clicker


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
