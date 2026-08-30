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
          └── erforderlich im Entscheidungsbundle: decision-clicker als Writer/UI
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
4. der generierte Maschinenindex `_DECISIONS/_tools/decisions.index.json`
   (kind `evidence`, also
   nicht-autoritativ — kanonisch bleiben die Kettendateien selbst),
5. die projektlokale `DECISIONS.md`-Konvention (kind `rule`, zeigt auf die
   Vorlage in `.AI/_templates/project-docs/DECISIONS.md`).

Bewusst **nicht** registriert wird jede einzelne Entscheidung — das würde die
Registry zu einem zweiten, unsynchronisierten Entscheidungsspeicher machen und
das Pointer-Only-Prinzip verletzen. `policy-registry seed-decisions
--control-center-root <pfad>` seedet/aktualisiert die fünf Einträge; die
Kettendateien selbst bleiben unverändert die alleinige Quelle für den
tatsächlichen Entscheidungstext.

## decision-clicker als fester Bundle-Baustein [U 2026-08-27]

Für die strukturelle Führung von `decision-clicker` als Untermodul standen
zwei Mechaniken zur Wahl: eine feste Bundle-Bindung im Manifest oder ein
optionaler Import/Verweis. Am 2026-08-24 wurde zunächst die leichtgewichtigere
Variante gewählt. Die Nutzerentscheidung vom 2026-08-27 ersetzt diese
Kompositionsentscheidung: `decision-clicker` ist nun fester Bestandteil des
Entscheidungssystems. Das Manifest von `policy-registry` führt deshalb
`decision.clicker` unter `requires`; der Adapter `decision-clicker-v1` trägt
den Status `required`.

Dabei bleiben zwei Ebenen bewusst getrennt:

- **Komposition:** Ein vollständiges Entscheidungsbundle enthält immer
  `policy-registry` als Pointer-/Index-Leser und `decision-clicker` als
  kontrollierten menschlichen Writer und UI. Ein fehlender Clicker ist daher
  ein unvollständiges Bundle, nicht mehr bloß eine optionale Erweiterung.
- **Laufzeitkopplung:** Die eigentliche Kopplung bleibt **Daten-**, nicht
  Codekopplung. Beide
  Werkzeuge beziehen sich auf dieselbe `_DECISIONS`-Kette — `policy-registry`
  liest/indiziert sie als Pointer (siehe oben), das Untermodul schreibt
  hinein. Deshalb bleibt `adapters/decision_clicker.py` eine guarded
  Verfügbarkeitsprobe statt eines Imports auf Modulebene. Decision Clicker
  bleibt für Wartung und Wiederherstellung direkt startbar; das widerspricht
  seiner festen Bundle-Mitgliedschaft nicht.

Historischer Beleg: Die optionale Wahl vom 2026-08-24 bleibt in Git-Historie
und Changelog nachvollziehbar, ist aber für die aktuelle Komposition nicht
mehr maßgeblich.

## Präzedenz und TOM-lm

1. aktive, adoptierte und zeitlich gültige explizite Policy/Regel/Decision;
2. höhere `priority`;
3. höhere `precedence`;
4. Gleichstand an der Spitze bedeutet Konflikt, keine stille Auswahl.

Bei `missing`, `insufficient` oder `conflict` ist TOM-lm ausschließlich
beratender Fallback. Sein Ergebnis ist Evidence oder Decision-Kandidat.
Generalisierung erfordert eine explizite Adoption.

## BYUM-v2-Pointer-Seam (`adapters/byum.py`) [U 2026-08-26]

`build-your-users-mind` (BYUM) bleibt Eigentümer seines privaten, append-only
Prediction-/Feedback-Journals. `policy-registry` importiert weder BYUM noch
liest oder parst es Ereignisdateien. Der optionale Seam nimmt ausschließlich
einen **bereits durch BYUM validierten** Pointer-Umschlag nach
`schemas/byum-decision-candidate-pointer.v1.schema.json` an.

Der geschlossene Umschlag enthält nur:

- BYUM-Protokoll `byum.decision-prediction.v2` und `prediction_id`;
- den strukturierten `decision_ref` aus Decision-ID, Index-Key, Scope,
  Quellpfad, Block-ID und SHA-256 der Entscheidungsquelle;
- lokalen Pointer, SHA-256 und redigierten Status der BYUM-Projektion.

Optionen, Empfehlungen, Begründungen, Ereignisgründe, Prompts,
Entscheidungstexte, Secure-Text-/Avatar-Payloads, Action-/Execution-Payloads
und Receipts sind nicht Teil dieser Schnittstelle und scheitern wegen des
geschlossenen Vertrags fail-closed.
Prediction-, Decision-, Index- und Block-IDs sind auf stabile ID-Tokens ohne
Leer-/Zeilenfreitext begrenzt; Remote-Projektions-URIs werden ebenfalls
abgewiesen.

`candidate_entry()` projiziert den Umschlag ausschließlich als
`kind=decision-candidate`, `adoption=pending`,
`authority=advisory-pointer`. `source.uri` und der Registry-Hash zeigen auf
die externe BYUM-Projektion; der `decision_ref` bleibt reine Provenienz. Der
Eintrag ist über Prediction-ID und den vollständigen Projektionshash
content-addressed. Eine unveränderte Wiederholung scheitert als Dublette; ein
neuer Projektionsstand erzeugt eine neue append-only Candidate-ID statt einen
Vorgänger zu überschreiben. Der Eintrag ist suchbar, aber
`PolicyRegistry.resolve()` betrachtet weiterhin nur
`policy`, `rule` und `decision`. Selbst eine nachträgliche Manipulation von
Adoption oder Authority macht den Candidate daher nicht zur Norm.

Eine Generalisierung oder Policy-Adoption benötigt weiterhin einen getrennten,
ausdrücklichen menschlichen Vorgang. Dieser Seam ist nicht der im TODO offene
TOM-lm-Connector und entscheidet dessen Schnittstelle nicht vor.

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

## D2-R2 Stufe 1: Audit-Pflichtfelder, Append-only für Rules, Autoritäts-Schalter
[U 2026-08-25, T-20260825-601850637 Option C]

Vorgeschichte: Eine Analyse (T-20260824-244932811) fand, dass 12 von 46
USMC-Facts inhaltlich normative Regeln statt Systemmechanik waren — u. a.
weil es bisher keinen leichten, disziplinierten Weg gab, eine kurze Regel
audit-fähig abzulegen, ohne gleich eine ganze `P-XXX`-Datei anzulegen. Eine
Folgeanalyse (D2-R2) prüfte, ob `policy-registry` selbst zu einer Datenbank
mit expliziten Typen werden sollte, und empfahl eine **gestufte** Umsetzung
(Option C): Stufe 1 sofort und risikoarm, Stufe 2 (physischer Speicherort)
als eigenes, spätere Folgeticket. **Kein DB-Umzug, keine Zwangsmigration
bestehender Einträge** — beides bleibt Stufe 2/3.

### 1. Audit-Pflichtfelder für `kind=rule` — nur im neuen Append-only-Pfad

`kind=policy` trägt Audit-/Driftschutz-Felder (`hash`, `valid_from`) schon in
der Praxis, weil jedes `P-XXX` sie mitbringt. Für `kind=rule` galt das
bisher nur als Konvention. `Registry.register_rule()` (`registry.py`) macht
`hash` und `valid_from` dort strukturell verpflichtend
(`model.RULE_AUDIT_REQUIRED`) — **bewusst nicht** im allgemeinen
`validate_entry()`/`register()`/`register_many()`, weil bestehende leichte
`kind=rule`-Pointer (z. B. `decisions.py`s `project-local-convention`) nie
für diese Disziplin gebaut wurden und durch eine rückwirkende Pflicht
gebrochen wären (empirisch bestätigt: ein erster Versuch, die Pflicht in
`validate_entry()` global zu erzwingen, brach 6 bestehende Tests).

### 2. Append-only / Supersede — `register_rule()`

Vorbild: `session-checkpoint`s ADR-003/004/005-Muster (immutable rows +
Hash-Verifikation + konservative destruktive Operationen), hier auf das
bestehende `registry.json` übertragen statt eine neue Storage-Schicht zu
bauen (Stufe-1-Vorgabe: "unabhängig vom physischen Speicherort").

- **Kein Überschreiben per gleicher `id`.** Ein Aufruf mit bereits
  vorhandener `id` schlägt immer fehl, auch mit `replace`-artiger Absicht —
  eine neue Version braucht eine neue `id` (Konvention: `<basis-id>@vN`).
- **Supersede statt Löschen.** `register_rule(neu, supersedes=alt_id)`
  markiert die Vorgänger-Zeile (`status="superseded"`,
  `superseded_by=<neue id>`), ohne ihren übrigen Inhalt zu verändern —
  `hash`/`source`/`version`/alle anderen Felder bleiben byte-identisch zum
  Registrierungszeitpunkt. Die alte Regel bleibt vollständig auditierbar,
  nichts wird nachträglich umgeschrieben oder gelöscht.
- **`resolve()` filtert automatisch.** Da eine supersedete Zeile
  `status="superseded"` trägt, greift die bestehende `is_valid_now()`-Prüfung
  in `resolve()` ohne jede Änderung dort — nur die jeweils aktuelle
  Rule-Version erscheint in `candidates`/`selected`.

### 3. Resolver-Rolle: bestehende `policy.registry`-Rolle nutzen, keine neue bauen

Empirisch geprüft (`source-resolver`, Stand 2026-08-25): Es gibt **keine**
separate Rolle namens `policy.source` — die einzige registrierte Rolle für
Policy-Herkunft ist `policy.registry`
(`KNOWN_MODULE_PROVIDERS["policy.registry"]`, mit vollem Adapter
`adapters/policy_registry.py`, der auf die `resolve()`-CLI dieses Moduls
delegiert). Diese Rolle **ist** der "policy.source"-Resolver — Stufe 1 baut
hier bewusst **nichts Neues**, sondern dokumentiert nur den bestehenden Weg:
Wer "wo kommt Policy X her" fragen will, ruft `source_resolver.resolve
("policy.registry", ...)` auf, nicht eine eigene Logik.

### 4. `POLICY_AUTHORITY_MODE` — vorbereiteter, wirkungsloser Schalter

`authority.py` liest die Umgebungsvariable `POLICY_AUTHORITY_MODE`
(`policy-only` Default/Status quo, `memory-only` und `memory+policy` als
für Stufe 2/3 vorgemerkte, heute inaktive Werte) und prüft nur lesend, ob
`usmc` auf dem Host importierbar ist und dessen DB existiert
(`usmc_present()`). **`describe()["effective"]` ist heute immer
`policy-only`**, unabhängig vom konfigurierten Modus — der Schalter existiert,
damit Stufe 2 keinen neuen Modusnamen erfinden muss, verändert aber in
Stufe 1 kein Verhalten. Kein USMC-Umbau, keine Handover-Logik.

### CLI-Ergänzungen

`register-rule <entry.json> [--supersedes <id>]` und `authority-status`
(siehe `cli.py`).

Für `policy-registry` wurde keine Kollision gefunden.

## Autoritätsmodi — zweite Achse `POLICY_INTERACTION_MODE` (Stufe 1)
[U 2026-08-30, T-20260830-167725484]

`POLICY_AUTHORITY_MODE` beantwortet, **wo** Normen liegen (Registry/USMC). Die
Nutzervorgabe vom 2026-08-30 fragt etwas anderes: **wer rangiert** — die laufende
Chat-Anweisung, die gespeicherte Governance oder der aktuelle Nutzerwille. Dafür
gibt es einen zweiten, unabhängigen Schalter mit drei Werten:
`chat-authority-only` (Chat allein, Ausnahmemodus), `governance-bound` (Default:
Policies/Entscheidungen > Chat, Änderung nur per transparenter Decision-Change-
Aktion) und `user-sovereign` (aktuelle Nutzeranweisung > Governance > Vorhersage
des Decision-Avatars; Hintergrund-Reconciler zieht Alteinträge nach). Harte
Außenwirkungs-Gates bleiben in allen Modi beim Nutzer.

Stufe 1 benennt nur: Konstanten, `current_interaction_mode()` (fail-closed auf
`governance-bound`), `describe()` mit `interaction_mode`/`interaction_effective`
— wirksam ist weiterhin ausschließlich der Status quo. Rangfolge in `resolve()`,
`propose-change`, Reconciler und Projekt-Ebene sind eigene Folgestufen. Konzept,
Namensbegründung und Bausteintabelle: `docs/AUTORITAETS-MODI.md`.
