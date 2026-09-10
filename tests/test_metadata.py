import ast
import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 compatibility
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_version_consistency():
    """Verify version parity across pyproject.toml, package __init__, module manifest, and CHANGELOG."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)
    pyproject_version = pyproject_data["project"]["version"]

    init_path = REPO_ROOT / "src" / "policy_registry" / "__init__.py"
    init_content = init_path.read_text(encoding="utf-8")
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
    assert version_match, "Could not find __version__ in src/policy_registry/__init__.py"
    init_version = version_match.group(1)

    assert pyproject_version == init_version, (
        f"Version mismatch: pyproject.toml ({pyproject_version}) != __init__.py ({init_version})"
    )

    manifest_path = REPO_ROOT / "ellmos-module.v2.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data.get("version") == pyproject_version, (
        f"Version mismatch: ellmos-module.v2.json ({manifest_data.get('version')}) != pyproject.toml ({pyproject_version})"
    )

    changelog_path = REPO_ROOT / "CHANGELOG.md"
    assert changelog_path.exists(), "CHANGELOG.md is missing"
    changelog_content = changelog_path.read_text(encoding="utf-8")
    assert pyproject_version in changelog_content, (
        f"Version {pyproject_version} not referenced in CHANGELOG.md"
    )


def test_required_documentation_files():
    """Verify that all core documentation and governance files exist."""
    required_files = [
        "README.md",
        "README_de.md",
        "llms.txt",
        "CHANGELOG.md",
        "SECURITY.md",
        "ARCHITECTURE.md",
        "LICENSE",
        "ellmos-module.v2.json",
        "pyproject.toml",
        ".github/workflows/ci.yml",
    ]
    for rel_path in required_files:
        full_path = REPO_ROOT / rel_path
        assert full_path.is_file(), f"Required file '{rel_path}' does not exist"


def test_ellmos_module_manifest():
    """Verify ellmos-module.v2.json structure and capabilities."""
    manifest_path = REPO_ROOT / "ellmos-module.v2.json"
    assert manifest_path.is_file(), "ellmos-module.v2.json is missing"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data.get("schema") == "ellmos.module.v2"
    assert data.get("id") == "policy-registry"
    assert data.get("status") == "active"
    assert data.get("visibility") == "public"
    assert "provides" in data and len(data["provides"]) >= 4
    assert "policy.registry" in data["provides"]
    assert "policy.resolve" in data["provides"]
    assert "policy.discovery" in data["provides"]
    assert "delegation.candidate.resolve" in data["provides"]
    assert "adapters" in data and len(data["adapters"]) >= 3


def test_llms_txt_integrity():
    """Verify llms.txt index references and timestamps."""
    llms_path = REPO_ROOT / "llms.txt"
    assert llms_path.is_file(), "llms.txt is missing"
    content = llms_path.read_text(encoding="utf-8")

    assert "ellmos-ai / policy-registry" in content
    assert "Last-checked: 2026-09-10" in content
    assert "Test-suite:" in content
    assert "Local-First" in content or "LOCAL-FIRST" in content

    # Check referenced markdown and schema files exist
    referenced_files = [
        "README.md",
        "ARCHITECTURE.md",
        "SECURITY.md",
        "pyproject.toml",
        "schemas/policy-entry.schema.json",
        "schemas/byum-decision-candidate-pointer.v1.schema.json",
        "src/policy_registry/scope.py",
    ]
    for ref in referenced_files:
        assert (REPO_ROOT / ref).exists(), f"llms.txt references missing file: {ref}"


def test_schemas_validity():
    """Verify that all JSON schemas in schemas/ are valid JSON."""
    schemas_dir = REPO_ROOT / "schemas"
    assert schemas_dir.is_dir(), "schemas directory is missing"

    schema_files = list(schemas_dir.glob("*.json"))
    assert len(schema_files) >= 5, f"Expected at least 5 schema files, found {len(schema_files)}"

    for schema_path in schema_files:
        content = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "$schema" in content or "type" in content or "properties" in content, (
            f"Schema file {schema_path.name} does not appear to be a valid JSON Schema"
        )


def test_security_policy_parity_and_contacts():
    """Verify bilingual SECURITY.md invariants, zero-egress, and contact info."""
    sec_path = REPO_ROOT / "SECURITY.md"
    assert sec_path.is_file(), "SECURITY.md is missing"
    content = sec_path.read_text(encoding="utf-8")

    assert "English Security Policy" in content
    assert "Deutsche Sicherheitsrichtlinie" in content
    assert "security@ellmos.ai" in content
    assert "lukas@open-bricks.org" in content
    assert "support@lukasgeiger.com" in content
    assert "Local-First" in content
    assert "Zero-Egress" in content
    assert "Ed25519" in content
    assert "security/advisories" in content


def test_readme_and_readme_de_parity_and_structure():
    """Verify section structure and mermaid diagram parity between README.md and README_de.md."""
    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")

    # Both must have banners and badges
    assert "assets/banner.png" in readme_en and "assets/banner.png" in readme_de
    assert "llms.txt" in readme_en and "llms.txt" in readme_de
    assert "open--bricks" in readme_en and "open--bricks" in readme_de
    assert "ellmos--ai" in readme_en and "ellmos--ai" in readme_de

    # Both must contain Mermaid diagrams
    en_mermaid_count = readme_en.count("```mermaid")
    de_mermaid_count = readme_de.count("```mermaid")
    assert en_mermaid_count >= 3, f"Expected >=3 mermaid blocks in README.md, found {en_mermaid_count}"
    assert de_mermaid_count >= 3, f"Expected >=3 mermaid blocks in README_de.md, found {de_mermaid_count}"
    assert en_mermaid_count == de_mermaid_count, "Mermaid diagram count mismatch between EN and DE READMEs"

    # Both must link to sibling tools
    for tool in ["memoryhooker", "ellmos-scheduler", "ellmos-voice-io", "automation-master", "CodeBox"]:
        assert tool in readme_en, f"Tool '{tool}' missing from README.md"
        assert tool in readme_de, f"Tool '{tool}' missing from README_de.md"


def test_pyproject_python_classifiers_and_lint_config():
    """Verify python classifiers and ruff lint configuration in pyproject.toml."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    classifiers = pyproject_data["project"].get("classifiers", [])
    assert "Programming Language :: Python :: 3.10" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Programming Language :: Python :: 3.12" in classifiers
    assert "Programming Language :: Python :: 3.13" in classifiers

    assert "tool" in pyproject_data and "ruff" in pyproject_data["tool"]
    assert "lint" in pyproject_data["tool"]["ruff"]


def test_ci_workflow_integrity():
    """Verify that the GitHub Actions CI workflow configures multi-OS matrix and test gates."""
    ci_file = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_file.is_file(), "CI workflow file .github/workflows/ci.yml does not exist"
    ci_content = ci_file.read_text(encoding="utf-8")

    assert "actions/checkout@v4" in ci_content
    assert "actions/setup-python@v5" in ci_content
    assert "ubuntu-latest" in ci_content
    assert "windows-latest" in ci_content
    assert "macos-latest" in ci_content
    assert "3.10" in ci_content and "3.13" in ci_content
    assert "ruff check ." in ci_content
    assert "pytest" in ci_content


def test_pyproject_pep621_classifiers_and_urls():
    """Verify PEP 621 classifiers, keywords, and project URLs."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    project = pyproject_data.get("project", {})
    classifiers = project.get("classifiers", [])
    assert "Development Status :: 4 - Beta" in classifiers
    assert "Topic :: Security" in classifiers
    assert "Operating System :: Microsoft :: Windows" in classifiers
    assert "Operating System :: POSIX :: Linux" in classifiers
    assert "Operating System :: MacOS" in classifiers

    keywords = project.get("keywords", [])
    assert "policy" in keywords
    assert "security" in keywords
    assert "local-first" in keywords

    urls = project.get("urls", {})
    assert "Homepage" in urls
    assert "Documentation" in urls
    assert "Repository" in urls
    assert "Issues" in urls
    assert "Changelog" in urls
    assert "Security" in urls
    assert "Umbrella" in urls
    assert "Parent-Organization" in urls


def test_pep639_license_expression_has_no_legacy_trove_classifier():
    """Current setuptools rejects SPDX license plus legacy license classifiers."""
    with (REPO_ROOT / "pyproject.toml").open("rb") as f:
        project = tomllib.load(f)["project"]

    assert project["license"] == "MIT"
    assert not any(value.startswith("License ::") for value in project.get("classifiers", []))


def test_python_310_compatible_datetime_utc_imports():
    """Python 3.10 lacks datetime.UTC; the advertised minimum must remain importable."""
    python_files = [
        *(REPO_ROOT / "src").rglob("*.py"),
        *(REPO_ROOT / "tests").rglob("*.py"),
    ]

    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in python_files
        if re.search(r"^from datetime import .*\bUTC\b", path.read_text(encoding="utf-8"), re.MULTILINE)
    ]
    assert offenders == [], f"datetime.UTC is unavailable on Python 3.10: {offenders}"


def test_offline_and_privacy_invariants():
    """Verify that the core source code contains zero unauthorized network egress modules."""
    src_dir = REPO_ROOT / "src" / "policy_registry"
    assert src_dir.is_dir(), "src/policy_registry directory missing"

    forbidden_modules = {"requests", "urllib.request", "httpx", "aiohttp", "urllib3"}

    for py_file in src_dir.rglob("*.py"):
        code = py_file.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules, (
                        f"Forbidden network module '{alias.name}' imported in {py_file.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module not in forbidden_modules, (
                    f"Forbidden network module '{module}' imported in {py_file.name}"
                )


def test_readme_quick_navigation_and_anchors():
    """Verify both English and German READMEs have structured Quick Navigation."""
    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "## 🧭 Quick Navigation" in readme_en
    assert "## 🧭 Schnellnavigation" in readme_de

    # Ensure all key sections are referenced in Quick Navigation
    en_nav_items = [
        "#what-is-policy-registry",
        "#discovery-context",
        "#test-status",
        "#system-architecture",
        "#scope-resolution--hierarchical-precedence",
        "#signed-delegation-verification-lifecycle",
        "#governance--runtime-invariants",
        "#security--authority-contract",
        "#metadata-model",
        "#cli-usage",
        "#python-api",
        "#model-context-protocol-mcp-server",
        "#sibling-projects--ecosystem-matrix",
        "#security-policy--vulnerability-reporting",
        "#haftung--liability",
    ]
    for item in en_nav_items:
        assert item in readme_en, f"Quick navigation missing anchor '{item}' in README.md"

    de_nav_items = [
        "#was-ist-policy-registry",
        "#discovery-kontext",
        "#teststatus",
        "#systemarchitektur",
        "#scope-auflösung--hierarchische-präzedenz",
        "#lebenszyklus-der-kryptografischen-delegationsprüfung",
        "#governance---laufzeit-invarianten",
        "#sicherheits---autoritätsvertrag",
        "#metadatenmodell",
        "#cli-nutzung",
        "#python-api",
        "#model-context-protocol-mcp-server",
        "#geschwisterprojekte--ökosystem-matrix",
        "#sicherheitsrichtlinie--meldung-von-schwachstellen",
        "#haftungsausschluss--liability",
    ]
    for item in de_nav_items:
        assert item in readme_de, f"Schnellnavigation missing anchor '{item}' in README_de.md"


def test_governance_invariants_matrix_parity():
    """Verify that both READMEs contain the 10 Governance & Runtime Invariants."""
    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "## Governance & Runtime Invariants" in readme_en
    assert "## Governance- & Laufzeit-Invarianten" in readme_de

    # Verify 10 numbered rows exist in both tables
    for i in range(1, 11):
        assert f"| {i} |" in readme_en, f"Invariant {i} missing from README.md"
        assert f"| {i} |" in readme_de, f"Invariante {i} missing from README_de.md"


def test_security_policy_slas_and_contacts():
    """Verify SECURITY.md defines explicit SLAs, non-elevation, and contact emails."""
    sec_path = REPO_ROOT / "SECURITY.md"
    assert sec_path.is_file(), "SECURITY.md is missing"
    content = sec_path.read_text(encoding="utf-8")

    assert "48 hours" in content or "48 Stunden" in content
    assert "5 business days" in content or "5 Werktagen" in content
    assert "RunAsInvoker" in content or "Non-Elevation" in content
    assert "security@ellmos.ai" in content
    assert "security@open-bricks.org" in content
    assert "support@lukasgeiger.com" in content
    assert "lukas@open-bricks.org" in content


def test_ci_concurrency_and_bytecode_gate():
    """Verify CI workflow enforces cancel-in-progress and byte-compilation validation."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), ".github/workflows/ci.yml missing"
    content = ci_path.read_text(encoding="utf-8")

    assert "concurrency:" in content
    assert "cancel-in-progress: true" in content
    assert "python -m compileall -q ." in content


def test_local_marketing_log():
    """Verify local MARKETING-LOG.txt audit log exists and documents discovery updates."""
    log_path = REPO_ROOT / "MARKETING-LOG.txt"
    assert log_path.is_file(), "MARKETING-LOG.txt is missing"
    content = log_path.read_text(encoding="utf-8")

    assert "[GITHUBBOT_ONE_REPO_MARKETING_AND_DESIGN]" in content
    assert "AUDIT FINDINGS" in content
    assert "RECOMMENDATIONS FOR FUTURE WORK" in content or "RECOMMENDATIONS" in content


def test_sibling_ecosystem_matrix_parity():
    """Verify that both READMEs list the sibling ecosystem tools."""
    readme_en = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (REPO_ROOT / "README_de.md").read_text(encoding="utf-8")

    siblings = [
        "decision-clicker",
        "memoryhooker",
        "ellmos-scheduler",
        "ellmos-voice-io",
        "lock-master",
        "ticket-master",
        "clutch",
        "ellmos-controlcenter-mcp",
        "ellmos-filecommander-mcp",
        "ellmos-codecommander-mcp",
        "n8n-manager-mcp",
        "automation-master",
        "DevCenter",
        "CodeBox",
        "companion-for-agy",
        "safe-start-for-codex",
        "open-bricks",
    ]
    for sibling in siblings:
        assert sibling in readme_en, f"Sibling '{sibling}' missing in README.md"
        assert sibling in readme_de, f"Sibling '{sibling}' missing in README_de.md"


def test_gitignore_hygiene_patterns():
    """Verify that .gitignore contains standardized multi-host conflict, multi-agent lock, and cache rules."""
    gitignore_path = REPO_ROOT / ".gitignore"
    assert gitignore_path.is_file(), ".gitignore missing"
    content = gitignore_path.read_text(encoding="utf-8")

    required_patterns = [
        "*-conflict-*",
        "*.sync-conflict-*",
        "*.conflict",
        "*-CONFLIT-*",
        "*.sync-temp-*",
        "*-ASUS-GEI*",
        "*-ASUS-GEI.*",
        "*-WORKSTATION-LG*",
        "*-WORKSTATION-LG.*",
        "*-WORKSTATION.*",
        "LOCK",
        "LOCK.*",
        "*.lock",
        "LOCK*.txt",
        "LOCK.permissions.json",
        "uv.lock",
        "!LOCK.md",
        "coverage/",
        "htmlcov/",
        "wheelhouse/",
        ".wheel-smoke/",
    ]
    for pattern in required_patterns:
        assert pattern in content, f"Missing required .gitignore pattern: {pattern}"


def test_pytest_configuration_and_flags():
    """Verify pyproject.toml configures standardized pytest runner flags."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    pytest_opts = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
    addopts = pytest_opts.get("addopts", "")
    assert "-ra" in addopts and "-v" in addopts, (
        f"Expected standardized '-ra -v' in pyproject.toml [tool.pytest.ini_options].addopts, got: '{addopts}'"
    )


def test_ci_workflow_pytest_flags():
    """Verify CI workflow executes pytest with standardized -ra -v flags."""
    ci_file = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_file.is_file(), "CI workflow missing"
    ci_content = ci_file.read_text(encoding="utf-8")

    assert "pytest -ra -v" in ci_content, "CI workflow does not use standardized 'pytest -ra -v'"


def test_changelog_recent_pfad_a_entry():
    """Verify CHANGELOG.md contains the latest 0.2.2 release entry with hygiene updates."""
    changelog_path = REPO_ROOT / "CHANGELOG.md"
    assert changelog_path.is_file(), "CHANGELOG.md missing"
    content = changelog_path.read_text(encoding="utf-8")

    assert "## [0.2.2] - 2026-09-10" in content
    assert "Standardized pytest test runner options" in content
    assert "Comprehensive hardening of `.gitignore`" in content
