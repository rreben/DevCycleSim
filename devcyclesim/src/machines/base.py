from dataclasses import dataclass, field
from typing import List
from devcyclesim.src.user_story import UserStory


@dataclass
class Machine:
    """Basisklasse für alle Verarbeitungsmaschinen im Entwicklungsprozess."""

    name: str
    capacity: int
    queue: List[UserStory] = field(default_factory=list)
    active_stories: List[UserStory] = field(default_factory=list)

    def enqueue(self, story: UserStory) -> None:
        """Fügt eine UserStory zur Warteschlange hinzu."""
        self.queue.append(story)

    def start_processing(self) -> None:
        """Verschiebt Stories von der Queue in die aktive Verarbeitung."""
        while (
            len(self.active_stories) < self.capacity
            and len(self.queue) > 0
        ):
            story = self.queue.pop(0)  # FIFO-Prinzip
            story.start_processing()
            self.active_stories.append(story)

    def process_takt(self) -> List[UserStory]:
        """
        Verarbeitet einen Zeittakt für alle aktiven Stories.
        Returns:
            List[UserStory]: Liste der in diesem Takt fertiggestellten Stories
        """
        completed_stories = []
        for story in self.active_stories:
            if story.process_day():  # Story ist fertig
                completed_stories.append(story)
        # Entferne fertige Stories aus active_stories
        for story in completed_stories:
            self.active_stories.remove(story)
        return completed_stories

    def get_active_count(self) -> int:
        """Gibt die Anzahl der aktiv verarbeiteten Stories zurück."""
        return len(self.active_stories)

    def get_queue_length(self) -> int:
        """Gibt die Länge der Warteschlange zurück."""
        return len(self.queue)

    def get_stories_with_errors(self) -> List[UserStory]:
        """
        Returns stories that have errors.
        This base implementation returns an empty list.
        Specialized machines should override this method.
        """
        return []
