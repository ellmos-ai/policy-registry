# Beitragsrichtlinie / Contributing Guide

## Deutsch

Vielen Dank für dein Interesse, zu `policy-registry` beizutragen!

### Wie du beitragen kannst

1. **Bug melden:** Erstelle ein Issue über die Vorlage `Bug Report` mit dem Label `bug`
2. **Feature vorschlagen:** Erstelle ein Issue über die Vorlage `Feature Request` mit dem Label `enhancement`
3. **Code oder Dokumentation beitragen:** Erstelle einen Pull Request gegen `main`
4. **Sicherheitslücken:** Bitte vertraulich gemäß [`SECURITY.md`](SECURITY.md) melden

### Pull Requests

1. Forke das Repository
2. Erstelle einen Feature-Branch: `git checkout -b feature/mein-feature`
3. Prüfe deine Änderungen lokal:
   - `python -m pip install -e ".[test,mcp]"`
   - `ruff check .`
   - `python -m compileall -q .`
   - `pytest -ra -v`
4. Committe deine Änderungen: `git commit -m "Beschreibung der Änderung"`
5. Pushe den Branch: `git push origin feature/mein-feature`
6. Erstelle einen Pull Request

### Lizenz- und Rechtehinweise

Ohne ausdrückliche Zusatzregel gelten Pull Requests unter der Projektlizenz ([`LICENSE`](LICENSE), MIT). Bitte beachte außerdem [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

### Code-Richtlinien

- Python >= 3.10 (kein `datetime.UTC` — verwende `datetime.timezone.utc`)
- Encoding: UTF-8 für alle Dateien; deutsche Doku mit echten Umlauten (`ä ö ü Ä Ö Ü ß`)
- Pointer-Only- und Zero-Egress-Invarianten wahren: keine Volltexte im Register, keine ungeprüften Netzwerkmodule in `src/policy_registry`
- Keine hartkodierten lokalen Host- oder Benutzerpfade und keine Secrets

### Erste Schritte

Lies zuerst [`README_de.md`](README_de.md) / [`README.md`](README.md), [`ARCHITECTURE.md`](ARCHITECTURE.md) und [`pyproject.toml`](pyproject.toml).

---

## English

Thank you for your interest in contributing to `policy-registry`!

### How to Contribute

1. **Report bugs:** Open an issue using the `Bug Report` template (`bug` label)
2. **Suggest features:** Open an issue using the `Feature Request` template (`enhancement` label)
3. **Contribute code or documentation:** Open a Pull Request targeting `main`
4. **Security issues:** Report privately as described in [`SECURITY.md`](SECURITY.md)

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run the local checks before committing:
   - `python -m pip install -e ".[test,mcp]"`
   - `ruff check .`
   - `python -m compileall -q .`
   - `pytest -ra -v`
4. Commit your changes: `git commit -m "Description of change"`
5. Push the branch: `git push origin feature/my-feature`
6. Open a Pull Request

### Licensing and Contribution Terms

Unless stated otherwise, pull requests are understood to be submitted under the project's license ([`LICENSE`](LICENSE), MIT). Please also follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

### Code Guidelines

- Python >= 3.10 (avoid `datetime.UTC`; use `datetime.timezone.utc`)
- Encoding: UTF-8 for all files
- Preserve pointer-only and zero-egress invariants: never duplicate full policy payloads in the registry or add network-egress dependencies to `src/policy_registry`
- No hardcoded host or user paths and no secrets

### Getting Started

Start with [`README.md`](README.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`pyproject.toml`](pyproject.toml).
