from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class StoryPhase(Enum):
    SPEC = "spec"
    DEV = "dev"
    TEST = "test"
    ROLLOUT = "rollout"

    @classmethod
    def get_default_durations(cls) -> Dict[str, int]:
        """
        Gibt Standardwerte für die Dauer jeder Phase zurück.
        Kann als Basis für die Skalierung verwendet werden.
        """
        return {
            StoryPhase.SPEC.value: 2,     # 2 Tage für Spezifikation
            StoryPhase.DEV.value: 5,      # 5 Tage für Entwicklung
            StoryPhase.TEST.value: 3,     # 3 Tage für Tests
            StoryPhase.ROLLOUT.value: 1   # 1 Tag für Rollout
        }

    @classmethod
    def get_next_phase(
        cls, current_phase: 'StoryPhase'
    ) -> Optional['StoryPhase']:
        """
        Gibt die nächste Phase in der Entwicklungsreihenfolge zurück.
        Gibt None zurück wenn es keine nächste Phase gibt (bei ROLLOUT).
        """
        phase_order = {
            cls.SPEC: cls.DEV,
            cls.DEV: cls.TEST,
            cls.TEST: cls.ROLLOUT,
        }
        return phase_order.get(current_phase)


class StoryStatus(Enum):
    PENDING = "pending"      # Wartet auf Bearbeitung
    IN_PROGRESS = "active"   # Wird gerade bearbeitet
    BLOCKED = "blocked"      # Blockiert/Wartet auf andere Story
    DONE = "done"           # Fertig


@dataclass
class UserStory:
    story_id: str
    arrival_day: int
    priority: int = 1  # Niedrigere Zahlen bedeuten höhere Priorität
    size_factor: float = 1.0  # Skalierungsfaktor für die Story-Größe
    phase_durations: Optional[Dict[str, int]] = None

    def __post_init__(self):
        # Validierung der Eingabeparameter
        if self.priority <= 0:
            raise ValueError("Priorität muss positiv sein")
        if self.arrival_day <= 0:
            raise ValueError("Ankunftstag muss positiv sein")
        if self.size_factor <= 0:
            raise ValueError("Größenfaktor muss positiv sein")

        # Validierung der Phasendauern, falls angegeben
        if self.phase_durations is not None:
            # Erst prüfen, ob Dauern positiv sind
            if any(d <= 0 for d in self.phase_durations.values()):
                raise ValueError("Alle Phasendauern müssen positiv sein")

            # Dann prüfen, ob alle Phasen vorhanden sind
            required_phases = {phase.value for phase in StoryPhase}
            if not all(
                phase in self.phase_durations for phase in required_phases
            ):
                raise ValueError("Alle Phasen müssen definiert sein")

        self.current_phase: StoryPhase = StoryPhase.SPEC
        self.status: StoryStatus = StoryStatus.PENDING

        # Falls keine spezifischen Dauern angegeben wurden, verwende die
        # Standardwerte
        if self.phase_durations is None:
            base_durations = StoryPhase.get_default_durations()
            self.phase_durations = {
                phase: int(duration * self.size_factor)
                for phase, duration in base_durations.items()
            }

        self.remaining_days: int = (
            self.phase_durations[self.current_phase.value])
        self.total_wait_time: int = 0
        self.completion_day: Optional[int] = None

    def process_day(self) -> bool:
        """
        Verarbeitet einen Tag für diese Story.

        Returns:
            bool: True wenn die aktuelle Phase abgeschlossen wurde, sonst False
        """
        if self.status != StoryStatus.IN_PROGRESS:
            self.total_wait_time += 1
            return False

        self.remaining_days -= 1

        if self.remaining_days <= 0:
            return True
        return False

    def advance_to_next_phase(self) -> bool:
        """
        Bewegt die Story in die nächste Phase.

        Returns:
            bool: True wenn die Story komplett fertig ist, sonst False
        """
        # Wenn wir im Rollout sind und die Phase abgeschlossen wird,
        # markieren wir die Story als fertig
        if self.current_phase == StoryPhase.ROLLOUT:
            self.status = StoryStatus.DONE
            self.remaining_days = 0
            return True

        # Ansonsten gehen wir zur nächsten Phase
        self.current_phase = StoryPhase.get_next_phase(self.current_phase)
        self.remaining_days = self.phase_durations[self.current_phase.value]
        self.status = StoryStatus.PENDING
        return False

    def start_processing(self) -> None:
        """Markiert die Story als 'in Bearbeitung'"""
        self.status = StoryStatus.IN_PROGRESS

    def block(self) -> None:
        """Markiert die Story als 'blockiert'"""
        self.status = StoryStatus.BLOCKED


# Normale Story (Standardgröße, hohe Priorität)
story1 = UserStory("STORY-1", arrival_day=1, priority=1)

# Große Story (doppelte Dauer in allen Phasen, mittlere Priorität)
story2 = UserStory("STORY-2", arrival_day=1, priority=2, size_factor=2.0)

# Story mit individuell angepassten Dauern, niedrige Priorität
custom_durations = {
    "spec": 1,
    "dev": 8,
    "test": 4,
    "rollout": 2
}
story3 = UserStory(
    "STORY-3",
    arrival_day=1,
    priority=3,
    phase_durations=custom_durations
)
