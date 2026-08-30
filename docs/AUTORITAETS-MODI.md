# Autoritätsmodi — wer hat das letzte Wort: Chat, Governance oder Nutzerwille?

Stand: 2026-08-30 · Ticket T-20260830-167725484 (Folgevorgang zu D2-R2, T-20260825-601850637) ·
Status: **Stufe 1 — Namen, Rangfolgen und Bausteine festgelegt; kein Verhalten geändert.**

Die Nutzervorgabe vom 2026-08-30 ist maßgeblich und liegt wörtlich im Ticket. Dieses Dokument
übersetzt sie in Begriffe der Registry, benennt die Modi und zerlegt die vier Design-Konsequenzen
in Bausteine — es ersetzt die Vorgabe nicht.

## Zwei Achsen, nicht eine

`policy-registry` kennt seit D2-R2 Stufe 1 den Schalter `POLICY_AUTHORITY_MODE`
(`policy-only` / `memory-only` / `memory+policy`). Der beantwortet **wo Normen liegen**
(Registry, USMC, beide). Die Modi dieses Dokuments beantworten eine andere Frage:
**wer rangiert über wem** — die laufende Chat-Anweisung, die gespeicherte Governance
(Policies + Entscheidungen) oder der aktuelle Nutzerwille samt Vorhersage. Beide Achsen sind
unabhängig; deshalb ein zweiter Schalter, `POLICY_INTERACTION_MODE`, statt drei neuer Werte im
ersten.

## Die drei Modi

| Modus | Name (Vorschlag) | Rangfolge | Wann |
|---|---|---|---|
| 1 | `chat-authority-only` (Name vom Nutzer) | Chat — sonst nichts. Governance wird weder gelesen noch geschrieben. | Bewusst gewählter Ausnahmemodus: Sandbox, Einzelprojekt ohne Governance. Nie Default. |
| 2 | `governance-bound` **(Default)** | Policies/Entscheidungen **>** Chat | Regelbetrieb. Eine Chat-Anweisung kann Governance nicht außer Kraft setzen — nur eine **Decision-Change-Aktion** (transparent, mit Datum und Begründung) ändert sie. Sitzungs- und modellübergreifend. |
| 3 | `user-sovereign` | **aktuelle** Nutzeranweisung **>** vergangene Entscheidungen/Policies **>** Vorhersage (Decision-Avatar) | Der Avatar (BYUM/tom-lm) füllt Autoritätslücken per Vorhersage. Greift der Nutzer ein, gilt das über der Vorhersage und fließt zurück (Lernschleife); widersprechende Alteinträge zieht ein **Hintergrund-Reconciler** transparent nach. Nur rote (sehr unsichere) Vorhersagen werden vorgelegt. |

**Kernunterschied 2 ↔ 3 (aus der Vorgabe):** In 2 steht die Governance über dem Chat, Änderung
nur explizit. In 3 steht der aktuelle Nutzerwille über der Governance, und die Governance zieht
im Hintergrund nach.

**In allen Modi beim Nutzer:** harte Außenwirkungs-Gates (Veröffentlichen, Push auf geschützte
Branches, Geld, Löschen ohne Vorschau). Sie werden nicht vom Modus, sondern von lock-master /
`LOCK.permissions.json` und den Hausregeln erzwungen — ein Modus kann sie nicht lockern.

### Warum diese Namen

- **Modus 2 `governance-bound`** statt des Arbeitsnamens *history-guided-organisational-
  systemwide-aware*: Der Modus ist an *beides* gebunden, Policies **und** Entscheidungen
  (Ledger). `policy-governed` und `ledger-governed` benennen je nur die Hälfte;
  `org-governed` verschweigt den Mechanismus (die Bindung), `governance` deckt beide Quellen
  ab und ist die Vokabel, die Bundles und Stacks bereits benutzen (Governance-Bundle).
- **Modus 3 `user-sovereign`** statt `sovereign-predictive` / `avatar-guided`: Die
  Autorität ist der aktuelle Nutzerwille; Vorhersage und Avatar sind nur der Lückenfüller.
  Ein Name soll die Autorität nennen, nicht das Hilfsmittel. „Sovereign" schließt an die
  Sovereign-Produktlinie an (Datensouveränität = der Nutzer hat das letzte Wort).
- **Modus 1 `chat-authority-only`** bleibt, wie vom Nutzer benannt.

Die Namen sind Vorschlag und liegen dem Nutzer mit diesem Stand zur Bestätigung vor
(Optionen im Ticket). Bis zur Bestätigung tragen die Konstanten diese Namen; eine
Umbenennung ist ein Einzeiler pro Konstante plus Alias-Zeile.

## Die vier Design-Konsequenzen als Bausteine

| Vorgabe | Baustein | Nutzt Vorhandenes | Stufe |
|---|---|---|---|
| (a) Modus 2 braucht eine **Decision-Change-Aktion** | `propose-change`: Chat-Anweisung → `decision-candidate` (`adoption=pending`, Quelle = Sitzung/Zitat/Zeit) → explizite Adoption → gültig. | `decision-candidate`/Adoption existieren; `register_rule(supersedes=…)` für die Ablösung des Vorgängers; Audit-Pflichtfelder `hash`/`valid_from`. | 2 |
| (b) Modus 3 braucht einen **Hintergrund-Reconciler** | Erkennt Widersprüche zwischen neuer Anweisung und Alteinträgen (gleicher Scope, gegensätzliche Aussage), legt `superseded`-Kette mit Beleg an, meldet ins BYUM-Feedback (`WHAT-LUKAS-SAID`). Nie löschen, nie still: jeder Eingriff ist ein Ledger-Eintrag. | Append-only/Supersede aus D2-R2 Stufe 1; TOM-lm-Fallback von `resolve()` als Vorhersagequelle. Verwandt, aber nicht dasselbe: der Konvergenz-Reconciler (T-20260830-803579390) gleicht **Implementierungen** ab, dieser gleicht **Normen** ab — gemeinsam ist nur das Muster „abgleichen mit Beleg". | 3 |
| (c) **Dasselbe Autoritäts-Register** als Lesequelle | Keine zweite Quelle. `resolve()` liest weiterhin Registry + BYUM-Pointer + `_DECISIONS` + Projekt-`DECISIONS.md` über den Scope-Vertrag; der Modus wird ein **Ranking-Parameter** von `resolve()`, kein zweiter Store. | Scope-Matcher (`scope.py`), Präzedenz exakter Scope > Nachkommen > Priorität. | 2 |
| (d) **Modus-Wahl pro Projekt/Session**, Default 2 | Auflösung: Sitzung (`POLICY_INTERACTION_MODE`) > Projekt (Eintrag in Projekt-`DECISIONS.md` bzw. `.policy-registry.toml` im Projekt-Root) > global `governance-bound`. Unbekannter Wert → Default (fail-closed, wie beim ersten Schalter). | Muster von `current_mode()`; `describe()` zeigt beide Achsen. | 1 (Sitzung/Default) · 2 (Projekt) |

## Was Stufe 1 (dieses Ticket) enthält — und was nicht

Enthalten: die drei Modusnamen als Konstanten (`authority.py`), `current_interaction_mode()`
mit Default `governance-bound` und Fallback auf Default bei unbekanntem Wert, `describe()`
berichtet beide Achsen, dieses Dokument, Tests. **Nicht enthalten, bewusst:** kein Ranking in
`resolve()`, keine `propose-change`-CLI, kein Reconciler, keine Projekt-Datei — jeder dieser
Bausteine ist ein eigener Vorgang mit eigener Abnahme. `describe()["interaction_effective"]`
ist heute deshalb **immer** `governance-bound`: das ist der Status quo (Governance gilt, Chat
ändert sie nicht), nur jetzt benannt.

## Offene Nutzerentscheidungen

1. Namen bestätigen oder wählen (Modus 2: `governance-bound` · Alternativen `org-governed`,
   `policy-governed`, `ledger-governed`; Modus 3: `user-sovereign` · Alternativen
   `sovereign-predictive`, `avatar-guided`).
2. Reihenfolge der Folgestufen: erst (a)+(c) (Decision-Change + Ranking, Modus 2 wird
   wirksam) oder erst (b) (Reconciler, Modus 3)? Empfehlung: (a)+(c) zuerst — Modus 2 ist
   Default und trägt den Alltag; Modus 3 baut auf derselben Supersede-Kette auf.
