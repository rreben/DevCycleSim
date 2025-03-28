from dataclasses import dataclass, field
import numpy as np
from devcyclesim.src.user_story import Phase


@dataclass
class ProcessStep:
    """
    Ein Prozessschritt im Entwicklungsprozess.
    Verwaltet Aufgaben in drei Listen:
    - Eingangs-Queue
    - Work in Progress
    - Done-Liste
    """
    name: str
    phase: Phase
    _capacity: int
    input_queue: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=object)
    )
    work_in_progress: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=object)
    )
    done: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=object)
    )

    def __post_init__(self):
        """Validiert die Eingabeparameter"""
        if self._capacity <= 0:
            raise ValueError("Kapazität muss positiv sein")

    @property
    def capacity(self) -> int:
        """Gibt die aktuelle Kapazität zurück"""
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        """Setzt die Kapazität auf einen neuen Wert"""
        if value <= 0:
            raise ValueError("Kapazität muss positiv sein")
        self._capacity = value
