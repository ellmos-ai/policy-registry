# TODO.md — Active work & Release Status: policy-registry

**Version:** 0.2.4
**Updated:** 2026-10-31
**Auditor:** Gemini (Antigravity)
**Reason:** Turnusgemäßer AI Modules Care Wartungslauf, Final-Gate-Härtung (10/10 PASS), PEP 561 py.typed & Pfadneutralität
**Target Repo:** `ellmos-ai/policy-registry`

Erledigte Aufgaben gehören nach `CHANGELOG.md` oder in den Abschnitt „Abgeschlossene Aufgaben“.

## STATUS

| Category | Status | Evidence / next gate |
|---|---|---|
| Secrets | DONE | Keine Secrets oder Token in versionierten Dateien (0 Treffer). |
| Private Data (PII) | DONE | Keine personenbezogenen Daten; portable Pfadplatzhalter `<OneDrive>`. |
| .gitignore | DONE | Alle Mindesteinträge (`*.pyc`, `.env`, `*.db`, `.idea/`, `.vscode/`, `data/`, Multi-Host- & Lock-Muster) vorhanden. |
| Language & Parity | DONE | README.md (Englisch) und README_de.md (Deutsch) synchron und mit echter Umlautqualität. |
| BACH Internals | DONE | Zero-BACH-Coupling; rein standardbasierte Policy-Registry. |
| Database Files | DONE | Keine Datenbankdateien versioniert; `*.db`, `*.sqlite`, `*.sqlite3` ignoriert. |
| README.md & Architecture | DONE | Vollständige Spezifikation mit Quick-Navigation, Governance-Invarianten und ARCHITECTURE.md. |
| LICENSE & Governance | DONE | MIT-Lizenz vorhanden; PEP 639 `license-files` deklariert; THIRD_PARTY_LICENSES.md gepflegt. |
| Test Coverage | DONE | 100% Testabdeckung (174/174 Tests grün); Metadaten- und Governance-Vertragstests integriert. |
| **Overall** | **READY** | Alle 10 Release-Gates erfüllt. |

## Offene Aufgaben

- [ ] **TASK-PR-01: Norm-Reconciler für `user-sovereign` auf der Supersede-Kette (W501 Stufe 3)** (`effort=medium`, `scope=authority`, priority `normal`).
  - Stufe 3 nur als eigenes Ticket: Norm-Reconciler für `user-sovereign` auf der Supersede-Kette und transparentes BYUM-Feedback. Der in Stufe 2 ausgegebene Reconciliation-Kandidat bleibt bis dahin `automatic=false`.
- [ ] **TASK-PR-02: TOM-lm-Connector nach eigenständiger Schnittstellenentscheidung** (`effort=medium`, `scope=connectors`, priority `normal`).
  - TOM-lm-Connector nur nach eigenständiger Schnittstellenentscheidung ergänzen; weiterhin niemals automatische Autorität.
  - Für diesen späteren Connector ausschließlich versionierte Kandidaten mit Evidenzankern, Konfidenz, Gegenbelegen und Klärungsstatus akzeptieren. `candidate`/`contradicted`/`superseded` bleiben Metadaten; erst eine explizite menschliche Adoption erzeugt eine aktive Policy-Referenz.
- [ ] **TASK-PR-03: Delegation-Cutover-Vorbereitung** (`effort=high`, `scope=delegation`, priority `normal`).
  - Delegation-Cutover erst nach separater Operatorabnahme, Key-Custody- und Rotation-Vertrag, nativer Runtime-Integration und Live-Readback.
  - Weitere Host-Slots erst auf dem jeweiligen Host importieren und live prüfen; kein Fremdhost-Vollzug aus dieser Workstation behaupten.
- [ ] **TASK-PR-04: Policy-Referenz für Fremdmodul-Lebenszyklus (`stacks/KONZEPT.md`)** (`effort=medium`, `scope=governance`, priority `normal`).
  - Aufnahme, Review, Quarantäne, Deprecation und Entfernung bleiben explizite Adoptionen/Entscheidungen, keine aus Metadaten abgeleitete Autorität.
  - Für jeden Fremdmodul-Statuswechsel unveränderliche Pointer auf Upstream, Commit, Lizenz-/NOTICE-Beleg, Qualitätsnachweis, verantwortliche Rolle, Reviewtermin und Entscheidungsbeleg verlangen. Quelltext und Installationszustand bleiben bei ihren jeweiligen Besitzern.
  - Ein Entfernen darf frühere Adoptionsbelege nicht löschen: Status `removed`, letzter geprüfter Commit, Grund und Export-/Rollbackbeleg müssen weiterhin auflösbar bleiben.

## Rückspiegelung aus sentinel-fleet (T-20260830-294539438, 2026-08-30)

Quelle: `ellmos-ai/sentinel-fleet` @ `e7f9c74` (2026-08-29, unter Judging-Lock, nur gelesen), `src/sentinel_fleet/core/policy_catalog.py`, `permissions.py`, `binding_rules.py`.
Herkunft bei jeder Übernahme im Code-Kommentar mitführen (Repo, Commit, Datei::Symbol).

- [ ] **Projektion statt Registrierung für code-abgeleitete Einträge** (Vorbild `PolicyCatalog._permission_entries` / `_engine_entries` / `list_all`): Regeln, die bereits in Code oder Konfiguration leben (z. B. `LOCK.permissions.json`-Regeln via lock-master `permissions.evaluate`), werden **bei jedem Lesen** als Einträge mit `source="permission-registry"`, `source_ref="<datei>::<symbol>"`, `enforced_by` projiziert — nie gespeichert. Gespeichert bleibt nur der Nutzer-Slot. Damit kann die Registry nicht in eine zweite Kopie des Rechtesystems driften; `verify()` behält seine Rolle nur für **verfasste** Pointer. Entwurfsfrage: Adapter `adapters/projected_permissions.py` (read-only), Kennzeichnung `origin: projected` im `search/resolve`-Ergebnis, damit Konsumenten Projektion von Verfasstem unterscheiden.
- [ ] **Begründete Verdicts statt nackter Strings** (Vorbild `BindingVerdict`: `verdict + reason + triggered_rule + applied_rules + decisive_rule`): `resolve()` liefert heute den Gewinner; ergänzen um die Kette der geprüften Kandidaten und die entscheidende Regel (Scope-Relation, priority, precedence), damit ein Konflikt oder ein Gleichstand erklärbar ist statt nur gemeldet.
- **Verworfen (beitragsspezifisch):** `policies.py::PolicyEngine` (§ 14 UStG Rechnungsprüfung, Hackathon-Domäne), Mandanten-/Organisationsmodell (`users.py`, `organization_id`, Demo-Tenancy) — gehört nicht in eine local-first Einzelnutzer-Registry.

## Abgeschlossene Aufgaben

- [x] Metadata-only Schema und lokale atomare Speicherung.
- [x] CLI und Python-API für Register, Suche, Auflösung und Prüfung.
- [x] W501 Stufe 2: Decision-Change als pending Kandidat plus explizite, hashgebundene Rule-Adoption; wirksames modusabhängiges Ranking in `resolve()` und Projektmodus über `.policy-registry.toml` mit Sitzung > Projekt > Default `governance-bound`.
- [x] Optionaler MCP-Seam.
- [x] Import bestehender `.SYNC/_policies`-Pointer.
- [x] Optionaler system-gap-/`.SYNC`-Exportseam.
- [x] Optionaler, pointer-only BYUM-v2-Seam für vorvalidierte `decision-candidate`-Metadaten (`adoption=pending`, niemals Authority), ohne BYUM-Import, Eventparser oder private Inhalte. Ticket T-20260826-542328608; Vertrag in `ARCHITECTURE.md`.
- [x] Wiederkehrenden Multi-OS-CI-Installationsfehler behoben: SPDX-Lizenzexpression `MIT` bleibt kanonisch, redundanter und von aktuellem Setuptools abgewiesener Trove-Lizenzklassifikator entfernt; PEP-639-Regressionstest ergänzt. Ticket T-20260826-542328608.
- [x] Den durch die 3.10-Matrix entdeckten Importfehler behoben: Das Paket verspricht Python `>=3.10`, deshalb verwendet der Delegation-Resolver `timezone.utc` statt des erst ab Python 3.11 verfügbaren `datetime.UTC`; der Kompatibilitätsvertrag ist regressionsgetestet. Ticket T-20260826-542328608.
- [x] Stabile Orts-Pointer auf die realen `_DECISIONS`-Ablagen (`adapters/decisions.py`, CLI `seed-decisions`) + optionaler importierbarer Seam auf `decision-clicker` (`adapters/decision_clicker.py`). Ticket T-20260824-474639761, Begründung der Mechanik-Wahl in `ARCHITECTURE.md`.
- [x] Signer-/issuer-gebundener Delegation-Resolver als fail-closed Candidate-API/CLI; Runtime-Cutover bleibt deaktiviert.
- [x] **TASK-PR-00: Release-Hygiene, Final-Gate-Härtung (10/10 PASS), PEP 561 & Pfadneutralität (v0.2.4)** (`effort=low`, `scope=hygiene`, priority `high`).
  - Standardisiertes `TODO.md` mit `## STATUS`-Tabelle etabliert.
  - `.gitignore` um standardisierte Ausschlussmuster (`*.pyc`, `.env`, `*.db`, `.idea/`, `.vscode/`, `data/`) gehärtet (Gate 1).
  - Pfadneutralität in `MARKETING-LOG.txt:158` wiederhergestellt (Gate 7).
  - PEP 561 Marker `src/policy_registry/py.typed` erstellt und via `package-data` in `pyproject.toml` verankert.
  - PEP 639 Deklaration `license-files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]` in `pyproject.toml` ergänzt.
  - Vertragstests in `tests/test_metadata.py` erweitert.

---
<!-- HINWEIS: Deutsche End-User-Texte immer mit echten Umlauten schreiben: ä ö ü Ä Ö Ü ß, nicht ae/oe/ue. -->
