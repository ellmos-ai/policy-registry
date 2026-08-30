# Autoritätsmodi: Chat, Governance und aktueller Nutzerwille

Stand: 2026-08-30 · Ticket T-20260830-501665949 · Status: **Stufe 2 wirksam**

Die verbindliche Nutzervorgabe liegt im Vorgängerticket T-20260830-167725484.
Der dortige Commit `3f297f9` war am Arbeitsbeginn kein Vorfahr von `main`; die
Stufe-1-Grundlage wurde deshalb aus dem Commit, `ARCHITECTURE.md` und dem
Changelog rekonstruiert und hier mit Stufe 2 zusammengeführt.

## Zwei unabhängige Achsen

`POLICY_AUTHORITY_MODE` (`policy-only`, `memory-only`, `memory+policy`) beschreibt,
**wo** Normen perspektivisch liegen. Dieser Quellen-Schalter bleibt vorbereitet;
`policy-registry` ist weiterhin die wirksame Registry-Autorität.

Der Interaktionsmodus beschreibt dagegen, **wer rangiert**: aktueller Chat,
gespeicherte Governance oder aktueller Nutzerwille. Diese Achse ist in Stufe 2
wirksam und ändert weder Außenwirkungs-Gates noch den Beratungsstatus von
TOM-lm/BYUM.

## Die drei Modi

| Modus | Wirksame Rangfolge | Verhalten |
|---|---|---|
| `chat-authority-only` | aktuelle Chat-Anweisung; Registry nur beobachtbar | Bewusster Ausnahmemodus ohne Governance-Bindung. Ohne aktuelle Anweisung lautet das Ergebnis `missing`, selbst wenn Registry-Normen vorhanden sind. |
| `governance-bound` **(Default)** | Registry/Ledger > aktuelle Chat-Anweisung > beratender Fallback | Eine gültige Governance-Norm gewinnt. Ein Registry-Konflikt wird nie durch Chat gebrochen. Abweichungen laufen über `propose-change` und explizite Adoption. Fehlt Governance vollständig, kann die aktuelle Chat-Anweisung gelten. |
| `user-sovereign` | aktueller Nutzerwille > Registry/Ledger > beratender Fallback | Die aktuelle Nutzeranweisung gewinnt. Vorhandene oder widersprüchliche Governance wird als Reconciliation-Kandidat gemeldet, aber Stufe 2 ändert sie nicht automatisch. |

`resolve()` liest für alle drei Modi dieselbe Registry-Kandidatenmenge. Das
Ergebnis enthält sie unverändert in `candidates` und fasst ihren Zustand unter
`governance` zusammen. Nur Bindung und Rangfolge unterscheiden sich.

Harte Außenwirkungs-Gates bleiben in allen Modi beim Nutzer. Das Ergebnisfeld
`external_effect_gates="user-controlled"` erinnert Konsumenten daran; der Modus
erteilt keine Push-, Veröffentlichungs-, Lösch- oder Zahlungsfreigabe.

## Moduswahl: Sitzung vor Projekt vor Default

Die Auflösung ist:

1. expliziter API-/CLI-Sitzungsparameter `mode` / `--mode`;
2. Sitzungsvariable `POLICY_INTERACTION_MODE`;
3. `.policy-registry.toml` im ausdrücklich angegebenen Projekt-Root oder im
   aktuellen Arbeitsverzeichnis;
4. Default `governance-bound`.

Projektdatei:

```toml
[policy_registry]
interaction_mode = "user-sovereign"
```

Unbekannte, mehrdeutige oder syntaktisch defekte Sitzungs-/Projektwerte fallen
nicht auf eine niedrigere Ebene durch. Sie werden als `interaction_issue`
gemeldet und fail-closed zu `governance-bound` aufgelöst. `describe()` und
`authority-status` berichten den tatsächlich wirksamen Wert als
`interaction_effective` sowie seine Quelle.

## Decision-Change: Vorschlag und explizite Adoption

`propose-change` speichert eine Chat-Anweisung zunächst ausschließlich als
`kind=decision-candidate`, `adoption=pending`. Die Provenienz enthält Sitzung,
ein auf 4096 Zeichen begrenztes Zitat und einen expliziten UTC-Zeitpunkt; das
Zitat wird per SHA-256 gebunden. Der Kandidat ist suchbar, aber nie allein eine
auflösbare Norm.

```powershell
policy-registry --registry registry.json propose-change `
  --id change:alpha-mode --title "Use alpha mode" --scope project:alpha `
  --owner LG --session session-501 --quote "Use alpha mode from now on." `
  --at 2026-08-30T18:45:00Z
```

Der getrennte Befehl `adopt` prüft Provenienz und Hash, materialisiert eine
aktive, adoptierte `kind=rule` mit `valid_from` am Adoptionstag und markiert den
Kandidaten mit `adopted_as`/`adopted_at`. Eine Vorgängerregel wird ausschließlich
über den vorhandenen Append-only-Vertrag abgelöst:

```powershell
policy-registry --registry registry.json adopt change:alpha-mode `
  --rule-id rule:alpha-mode@v2 --supersedes rule:alpha-mode@v1 `
  --at 2026-08-30T19:00:00Z
```

`register_rule()` verlangt für die neue Regel weiterhin `hash` und `valid_from`,
verweigert identische IDs und erhält die Vorgängerzeile mit
`status=superseded`/`superseded_by` auditierbar.

Python-API:

```python
candidate = registry.propose_change(
    change_id="change:alpha-mode",
    title="Use alpha mode",
    scope="project:alpha",
    owner="LG",
    session="session-501",
    quote="Use alpha mode from now on.",
    captured_at="2026-08-30T18:45:00Z",
)
adoption = registry.adopt_change(
    candidate["id"],
    rule_id="rule:alpha-mode@v2",
    supersedes="rule:alpha-mode@v1",
    adopted_at="2026-08-30T19:00:00Z",
)
```

## Resolver-Ergebnis und Grenzen von Stufe 2

Mit `current_instruction` (CLI: `--instruction`) wird die aktuelle Anweisung
nur für diesen Aufruf übergeben; sie wird nicht automatisch gespeichert.
`reconciliation.required=true` in `user-sovereign` ist ausschließlich ein
transparenter Hinweis. `automatic=false` ist bindend: Der Norm-Reconciler und
die BYUM-Feedbackschleife gehören zu Stufe 3 und sind nicht Teil dieses Pakets.

TOM-lm und BYUM bleiben beratende Fallbacks bzw. Pointer-Quellen. Weder ein
Prediction-Kandidat noch ein nachträglich manipuliertes `decision-candidate`
wird durch `resolve()` zur Authority.
