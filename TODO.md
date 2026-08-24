# TODO

- [x] Metadata-only Schema und lokale atomare Speicherung.
- [x] CLI und Python-API für Register, Suche, Auflösung und Prüfung.
- [x] Optionaler MCP-Seam.
- [x] Import bestehender `.SYNC/_policies`-Pointer.
- [x] Optionaler system-gap-/`.SYNC`-Exportseam.
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
