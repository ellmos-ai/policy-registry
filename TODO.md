# TODO

- [x] Metadata-only Schema und lokale atomare Speicherung.
- [x] CLI und Python-API für Register, Suche, Auflösung und Prüfung.
- [x] Optionaler MCP-Seam.
- [x] Import bestehender `.SYNC/_policies`-Pointer.
- [x] Optionaler system-gap-/`.SYNC`-Exportseam.
- [x] Optionaler, pointer-only BYUM-v2-Seam für vorvalidierte
      `decision-candidate`-Metadaten (`adoption=pending`, niemals Authority),
      ohne BYUM-Import, Eventparser oder private Inhalte. Ticket
      T-20260826-542328608; Vertrag in `ARCHITECTURE.md`.
- [x] Wiederkehrenden Multi-OS-CI-Installationsfehler behoben: SPDX-
      Lizenzexpression `MIT` bleibt kanonisch, redundanter und von aktuellem
      Setuptools abgewiesener Trove-Lizenzklassifikator entfernt; PEP-639-
      Regressionstest ergänzt. Ticket T-20260826-542328608.
- [x] Den durch die 3.10-Matrix entdeckten Importfehler behoben: Das Paket
      verspricht Python `>=3.10`, deshalb verwendet der Delegation-Resolver
      `timezone.utc` statt des erst ab Python 3.11 verfügbaren `datetime.UTC`;
      der Kompatibilitätsvertrag ist regressionsgetestet. Ticket
      T-20260826-542328608.
- [x] Stabile Orts-Pointer auf die realen `_DECISIONS`-Ablagen
      (`adapters/decisions.py`, CLI `seed-decisions`) + optionaler
      importierbarer Seam auf `decision-clicker` (`adapters/decision_clicker.py`).
      Ticket T-20260824-474639761, Begründung der Mechanik-Wahl in
      `ARCHITECTURE.md`.
- [ ] TOM-lm-Connector nur nach eigenständiger Schnittstellenentscheidung
      ergänzen; weiterhin niemals automatische Autorität.
- [ ] Für diesen späteren Connector ausschließlich versionierte Kandidaten mit
      Evidenzankern, Konfidenz, Gegenbelegen und Klärungsstatus akzeptieren.
      `candidate`/`contradicted`/`superseded` bleiben Metadaten; erst eine
      explizite menschliche Adoption erzeugt eine aktive Policy-Referenz.
- [x] Signer-/issuer-gebundener Delegation-Resolver als fail-closed
      Candidate-API/CLI; Runtime-Cutover bleibt deaktiviert.
- [ ] Delegation-Cutover erst nach separater Operatorabnahme, Key-Custody- und
      Rotation-Vertrag, nativer Runtime-Integration und Live-Readback.
- [ ] Weitere Host-Slots erst auf dem jeweiligen Host importieren und live
      prüfen; kein Fremdhost-Vollzug aus dieser Workstation behaupten.
- [ ] Eine Policy-Referenz für den Fremdmodul-Lebenszyklus aus `stacks/KONZEPT.md`
      registrierbar machen: Aufnahme, Review, Quarantäne, Deprecation und
      Entfernung bleiben explizite Adoptionen/Entscheidungen, keine aus
      Metadaten abgeleitete Autorität.
- [ ] Für jeden Fremdmodul-Statuswechsel unveränderliche Pointer auf Upstream,
      Commit, Lizenz-/NOTICE-Beleg, Qualitätsnachweis, verantwortliche Rolle,
      Reviewtermin und Entscheidungsbeleg verlangen. Quelltext und
      Installationszustand bleiben bei ihren jeweiligen Besitzern.
- [ ] Ein Entfernen darf frühere Adoptionsbelege nicht löschen: Status
      `removed`, letzter geprüfter Commit, Grund und Export-/Rollbackbeleg müssen
      weiterhin auflösbar bleiben.
## Rückspiegelung aus sentinel-fleet (T-20260830-294539438, 2026-08-30)

Quelle: `ellmos-ai/sentinel-fleet` @ `e7f9c74` (2026-08-29, unter Judging-Lock, nur gelesen),
`src/sentinel_fleet/core/policy_catalog.py`, `permissions.py`, `binding_rules.py`.
Herkunft bei jeder Übernahme im Code-Kommentar mitführen (Repo, Commit, Datei::Symbol).

- [ ] **Projektion statt Registrierung für code-abgeleitete Einträge** (Vorbild
      `PolicyCatalog._permission_entries` / `_engine_entries` / `list_all`): Regeln, die
      bereits in Code oder Konfiguration leben (z. B. `LOCK.permissions.json`-Regeln via
      lock-master `permissions.evaluate`), werden **bei jedem Lesen** als Einträge mit
      `source="permission-registry"`, `source_ref="<datei>::<symbol>"`, `enforced_by`
      projiziert — nie gespeichert. Gespeichert bleibt nur der Nutzer-Slot. Damit kann die
      Registry nicht in eine zweite Kopie des Rechtesystems driften; `verify()` behält
      seine Rolle nur für **verfasste** Pointer. Entwurfsfrage: Adapter
      `adapters/projected_permissions.py` (read-only), Kennzeichnung `origin: projected`
      im `search/resolve`-Ergebnis, damit Konsumenten Projektion von Verfasstem unterscheiden.
- [ ] **Begründete Verdicts statt nackter Strings** (Vorbild `BindingVerdict`:
      `verdict + reason + triggered_rule + applied_rules + decisive_rule`): `resolve()`
      liefert heute den Gewinner; ergänzen um die Kette der geprüften Kandidaten und die
      entscheidende Regel (Scope-Relation, priority, precedence), damit ein Konflikt oder
      ein Gleichstand erklärbar ist statt nur gemeldet.
- **Verworfen (beitragsspezifisch):** `policies.py::PolicyEngine` (§ 14 UStG
  Rechnungsprüfung, Hackathon-Domäne), Mandanten-/Organisationsmodell (`users.py`,
  `organization_id`, Demo-Tenancy) — gehört nicht in eine local-first Einzelnutzer-Registry.
