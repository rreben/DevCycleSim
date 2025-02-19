from dataclasses import dataclass, field
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
    IN_PROGRESS = "in_progress"   # Wird gerade bearbeitet
    BLOCKED = "blocked"      # Blockiert/Wartet auf andere Story
    DONE = "done"           # Fertig


@dataclass
class StoryErrors:
    """Contains information about potential errors in a story"""
    # Requires extra debug day in development
    has_dev_debug_needed: bool = False
    # Requires revision in specification
    has_spec_revision_needed: bool = False


@dataclass
class UserStory:
    story_id: str
    phase_durations: Dict[str, int]
    arrival_day: int = 1
    priority: int = 1
    size_factor: float = 1.0
    errors: StoryErrors = field(default_factory=StoryErrors)
    current_phase: StoryPhase = field(default=StoryPhase.SPEC)
    status: StoryStatus = field(default=StoryStatus.PENDING)
    remaining_days: int = field(init=False)

    def __post_init__(self):
        """Initialize remaining days based on current phase duration."""
        # Validierung der Eingabeparameter
        if self.priority <= 0:
            raise ValueError("Priorität muss positiv sein")
        if self.arrival_day <= 0:
            raise ValueError("Ankunftstag muss positiv sein")
        if self.size_factor <= 0:
            raise ValueError("Größenfaktor muss positiv sein")

        # Validierung der Phasendauern
        # Zuerst prüfen wir die Werte der vorhandenen Phasen
        if any(duration <= 0 for duration in self.phase_durations.values()):
            raise ValueError("Alle Phasendauern müssen positiv sein")

        # Dann prüfen wir, ob alle erforderlichen Phasen vorhanden sind
        required_phases = {phase.value for phase in StoryPhase}
        if not all(phase in self.phase_durations for phase in required_phases):
            raise ValueError("Alle Phasen müssen definiert sein")

        # Initialisierung der remaining_days
        self.remaining_days = self.phase_durations[self.current_phase.value]

    def process_day(self) -> bool:
        """
        Verarbeitet einen Tag für diese Story.

        Returns:
            bool: True wenn die aktuelle Phase abgeschlossen wurde, sonst False
        """
        if self.status != StoryStatus.IN_PROGRESS:
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
        next_phase = StoryPhase.get_next_phase(self.current_phase)
        if next_phase is None:
            return True
        self.current_phase = next_phase
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
story1 = UserStory(
    "STORY-1", phase_durations={"spec": 2, "dev": 5, "test": 3, "rollout": 1})

# Große Story (doppelte Dauer in allen Phasen, mittlere Priorität)
story2 = UserStory(
    "STORY-2", phase_durations={"spec": 4, "dev": 10, "test": 6, "rollout": 2},
    arrival_day=1, priority=2, size_factor=2.0)

# Story mit individuell angepassten Dauern, niedrige Priorität
custom_durations = {
    "spec": 1,
    "dev": 8,
    "test": 4,
    "rollout": 2
}
story3 = UserStory(
    "STORY-3",
    phase_durations=custom_durations,
    arrival_day=1,
    priority=3
)
