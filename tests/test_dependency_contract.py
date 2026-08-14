from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


def test_mcp_extra_stays_on_the_supported_v1_line():
    with (Path(__file__).parents[1] / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert pyproject["project"]["optional-dependencies"]["mcp"] == [
        "mcp>=1.28.1,<2"
    ]
