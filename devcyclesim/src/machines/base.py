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
            List[UserStory]: Liste der Stories,
            die in dieser Phase fertig wurden
        """
        completed_stories = []

        # Erst Stories aus der Queue in active_stories verschieben
        self.start_stories()

        # Dann aktive Stories verarbeiten
        still_active = []
        for story in self.active_stories:
            is_complete = story.process_day()
            if is_complete:
                # Story als fertig markieren, aber nicht
                # zur nächsten Phase wechseln
                # (das macht simulation_controller.py)
                completed_stories.append(story)
            else:
                still_active.append(story)

        self.active_stories = still_active
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
        Base implementation checks for error flags directly.
        """
        error_stories = []
        for story in self.active_stories:
            if (hasattr(story, 'errors') and
                (story.errors.has_spec_revision_needed or
                 story.errors.has_dev_debug_needed)):
                error_stories.append(story)
        return error_stories

    def start_stories(self) -> None:
        """Start processing stories from queue if capacity available."""
        while (len(self.active_stories) < self.capacity and
               len(self.queue) > 0):
            story = self.queue.pop(0)  # FIFO
            story.start_processing()
            self.active_stories.append(story)
