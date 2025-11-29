# Analyse: Agilität vs. Wasserfall in DevCycleSim

Du hast absolut recht mit deiner Beobachtung: In der aktuellen Simulation zeigt sich der Vorteil von Agilität primär in der **Lead Time** (Durchlaufzeit), während die **Produktivität** (Durchsatz pro Ressource) oft gleich bleibt oder sogar sinkt, da im Wasserfall-Modell die Ressourcen durch die großen "Batches" (Losgrößen) ständig ausgelastet sind ("Resource Efficiency").

Hier sind die Effekte, die in der Simulation wahrscheinlich fehlen oder nicht stark genug gewichtet sind, um die *wirtschaftliche* Überlegenheit von Agilität vollständig abzubilden:

## 1. Die Kosten von Rework (Feedback-Loops)
Das ist der wichtigste fehlende Faktor.
*   **Im aktuellen Modell:** Ein Fehler führt zu "Rework", was oft einfach als "nochmal 1 Tag Entwicklung + 1 Tag Test" modelliert wird (siehe Example 5). Der Aufwand für den Fix ist konstant, egal wann der Fehler gefunden wird.
*   **In der Realität:** Die Kosten, einen Fehler zu beheben, steigen exponentiell mit der Zeit, die seit der Entstehung vergangen ist (**Defect Cost Increase**).
    *   Findet ein Entwickler den Fehler sofort (Agile/Unit Test): 5 Minuten.
    *   Findet der Tester ihn 2 Tage später: 1 Stunde.
    *   Findet man ihn im "Rollout" nach 3 Monaten (Wasserfall): Oft Tage oder Wochen, weil der Kontext weg ist ("Was habe ich da damals programmiert?") und der Fehler tief im System vergraben ist.

**Vorschlag für die Simulation:**
Wenn ein Fehler in einer späten Phase (z.B. Rollout) gefunden wird, sollte der Rework-Aufwand deutlich höher sein (z.B. 5x oder 10x so viele Tasks) als wenn er früh gefunden wird. Dann würde die Produktivität im Wasserfall massiv einbrechen.

## 2. Cost of Delay (Wert der Geschwindigkeit)
Die Simulation misst "Produktivität" als "erledigte Tasks pro Zeit". Das ist eine rein technische Sicht ("Output").
*   **Agile Sicht (Outcome):** 10 Features, die heute geliefert werden, sind wertvoller als 10 Features, die in 6 Monaten geliefert werden.
*   Wenn du Features früher lieferst, kannst du früher Umsatz generieren oder Feedback einholen.
*   **Missing Link:** Die Simulation gewichtet alle Storys gleich. Wenn man den "Business Value" über die Zeit integrieren würde, wäre Agile weit vorne, auch wenn die Entwickler zwischendurch mal "Leerlauf" haben.

## 3. Context Switching (Rüstkosten)
Du sagtest: *"weil die nicht genutzten Ressourcen ja an anderen 'Bündeln' arbeiten können"*.
*   **Das Problem:** Wenn ein Entwickler zwischen Projekt A (wartet auf Spec) und Projekt B (ist gerade da) springt, entstehen **Context Switching Costs**.
*   Studien zeigen, dass bei 2 parallelen Projekten ca. 20% der Zeit durch den Wechsel verloren geht. Bei 3 Projekten sind es schon 40%.
*   **Im Modell:** Die Simulation nimmt an, dass Ressourcen zu 100% effizient sind, egal woran sie arbeiten. Würde man einen "Malus" für Context Switching einführen, wäre die "hohe Auslastung" im Wasserfall plötzlich sehr ineffizient.

## 4. Integration Hell
Im Wasserfall werden am Ende (Phase "Test" oder "Rollout") alle Komponenten zusammengeworfen.
*   **Realität:** Das Integrieren von 100 User Stories auf einmal führt oft zu chaotischen Fehlern, die schwer zu isolieren sind.
*   **Agile:** Man integriert kontinuierlich kleine Stücke.
*   **Im Modell:** Die Simulation behandelt jede Story isoliert. Es gibt keinen "Integrations-Aufwand", der mit der Menge der gleichzeitigen Änderungen wächst.

## Zusammenfassung
Deine Simulation zeigt korrekt den **Flow-Efficiency** Vorteil von Agile (schnelle Lead Time).
Dass die **Resource-Efficiency** (Produktivität) im Wasserfall höher wirkt, liegt daran, dass das Modell die "versteckten Kosten" von großen Batches (spätes Feedback, teure Bugs, Context Switching) noch nicht abbildet.

Um Agile auch bei der Produktivität gewinnen zu lassen, müsstest du modellieren, dass **späte Fehlerbehebung teurer ist** als frühe.
