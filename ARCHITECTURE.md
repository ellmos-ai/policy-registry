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
          └── optional: system-gap-master als Transportseam
```

Die `.SYNC/_policies`-Struktur wird weiterverwendet. Es entsteht kein zweites
privates Bibliotheks- oder Adoptionsformat. Die Registry ergänzt sie um eine
lokale Auflösungs- und Discovery-Schicht.

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
