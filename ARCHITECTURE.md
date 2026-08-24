# Architekturentscheidung [U 2026-07-28]

## Entscheidung

`policy-registry` ist ein eigenständiges LOCAL-FIRST-Modul. Es hängt weder von
OneDrive noch von `system-gap-master` ab. Die lokale Registry ist für
Registry-Metadaten autoritativ; die referenzierte Quelldatei bleibt für den
Regeltext autoritativ.

## Grenzen

```text
kanonische lokale Quellen
          │ Pointer + Hash
          ▼
  lokale policy-registry ── CLI / Python-API / optional MCP
          │
          ├── optional: bestehende .SYNC/_policies-Sicht
          ├── optional: system-gap-master als Transportseam
          └── optional: decision-clicker als Untermodul (importierbarer Seam)
```

Die `.SYNC/_policies`-Struktur wird weiterverwendet. Es entsteht kein zweites
privates Bibliotheks- oder Adoptionsformat. Die Registry ergänzt sie um eine
lokale Auflösungs- und Discovery-Schicht.

## Entscheidungs-Pointer (`adapters/decisions.py`) [U 2026-08-24, F1=A-hybrid]

Nutzerentscheidung 2026-08-24 aus T-20260824-911756255 (Ticket
T-20260824-474639761): `policy-registry` wird der eine Ort, der **weiß**, wo
Entscheidungen liegen — nicht der Ort, der sie enthält. `adapters/decisions.py`
registriert dafür eine feste, bewusst kleine Menge **stabiler Orts-Pointer**
(fünf Einträge, `kind ∈ {decision, evidence, rule}`, `scope="decisions"`):

1. Kopf der globalen `TO-DECIDE-USER.txt`-Kette,
2. das Namensmuster hostbezogener Dateien (`TO-DECIDE-USER-<HOST>.txt`),
3. `DECIDED-AND-DONE.md` (umgesetzte Entscheidungen),
4. der generierte Maschinenindex `decisions.index.json` (kind `evidence`, also
   nicht-autoritativ — kanonisch bleiben die Kettendateien selbst),
5. die projektlokale `DECISIONS.md`-Konvention (kind `rule`, zeigt auf die
   Vorlage in `.AI/_templates/project-docs/DECISIONS.md`).

Bewusst **nicht** registriert wird jede einzelne Entscheidung — das würde die
Registry zu einem zweiten, unsynchronisierten Entscheidungsspeicher machen und
das Pointer-Only-Prinzip verletzen. `policy-registry seed-decisions
--control-center-root <pfad>` seedet/aktualisiert die fünf Einträge; die
Kettendateien selbst bleiben unverändert die alleinige Quelle für den
tatsächlichen Entscheidungstext.

## decision-clicker als Untermodul: Mechanik-Wahl [U 2026-08-24, F2]

Für die strukturelle Führung von `decision-clicker` als Untermodul standen
zwei Mechaniken zur Wahl: eine feste Bundle-Bindung im Manifest oder ein
optionaler Import/Verweis. Gewählt wurde die **leichtgewichtigere**: ein
optionaler, laufzeit-geprüfter Seam (`adapters/decision_clicker.py`,
Funktion `available()`), gespiegelt im Manifest als `type: seam`
(`decision-clicker-v1`, `status: optional`) und als `optional`-Capability
`decision.clicker` — exakt das bereits etablierte Muster von
`system-gap-optional`.

Begründung:

- `decision-clicker` muss laut Nutzerentscheidung weiterhin **eigenständig und
  manuell startbar** bleiben, unabhängig vom Release-Takt dieses Moduls; eine
  feste Bundle-Bindung im Manifest suggeriert das Gegenteil, nämlich dass
  `policy-registry` es zwingend mitzieht oder gemeinsam versioniert.
- Die eigentliche Kopplung ist **Daten-**, nicht Codekopplung: Beide
  Werkzeuge beziehen sich auf dieselbe `_DECISIONS`-Kette — `policy-registry`
  liest/indiziert sie als Pointer (siehe oben), das Untermodul schreibt
  hinein. Diese Beziehung ist bereits durch die gemeinsamen Orts-Pointer in
  `adapters/decisions.py` ausgedrückt; ein Code-Import wäre zusätzliche,
  unnötige Kopplung zwischen zwei unabhängig lebenszyklierten Werkzeugen.
- Eine optionale, laufzeit-geprüfte Verfügbarkeitsprobe kann jederzeit ohne
  Breaking Change zu einer engeren Bindung ausgebaut werden, sobald das
  Untermodul dafür bereit ist -- der umgekehrte Weg (feste Bindung wieder
  lösen) ist teurer.

## Präzedenz und TOM-lm

1. aktive, adoptierte und zeitlich gültige explizite Policy/Regel/Decision;
2. höhere `priority`;
3. höhere `precedence`;
4. Gleichstand an der Spitze bedeutet Konflikt, keine stille Auswahl.

Bei `missing`, `insufficient` oder `conflict` ist TOM-lm ausschließlich
beratender Fallback. Sein Ergebnis ist Evidence oder Decision-Kandidat.
Generalisierung erfordert eine explizite Adoption.

## Hierarchische Scope-Auflösung

`PolicyRegistry.search/resolve` und der signierte `DelegationResolver` verwenden
denselben Matcher in `src/policy_registry/scope.py`:

- Die globalen Aliaswerte `*`, `all`, `global` und `system-wide` gelten für
  jeden nichtleeren Consumer-Scope.
- Ein normaler Scope ist auf sich selbst exakt und wird vererbt auf alle echten
  Nachkommen (`project:alpha` gilt auch für `project:alpha/release`).
- Ein Scope mit `/*` gilt ausschließlich für Nachkommen (`project:alpha/*`),
  nicht für den Parent selbst.
- Die Präzedenz innerhalb derselben Autoritätsklasse ist: exakter Scope,
  `/*`-Wildcard, geerbter Parent, globaler Alias. Bei gleicher Relation gewinnt
  der tiefere Hierarchiepfad; erst danach zählen `priority` und `precedence`.
- Geschwister wie `project:alpha/other` matchen `project:alpha/release` nicht.
  Ein leerer Consumerfilter fragt alle Einträge ab; eine leere Consumerliste oder
  `*` ist universell, sonst muss der Consumer-Code exakt enthalten sein.

Der Matcher entscheidet nur die Kandidatenmenge und Scope-Spezifität. Die
Delegation-Oberfläche behält ihre höhere Authority-Rangfolge und die
hashgebundene, fail-closed Prüfung von stale oder nicht materialisierten Quellen.

## Benennung und Kollisionen

Vor Anlage wurden am 2026-07-28 geprüft:

- lokale Repos unter `C:\_Local_DEV\repos`;
- `.AI/.MODULES` und der generierte Modulkatalog;
- Repositories der Organisationen `ellmos-ai` und `dev-bricks`;
- PyPI-Projektnamen.

Für `policy-registry` wurde keine Kollision gefunden.
