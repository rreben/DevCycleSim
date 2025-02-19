from typing import List
from .machine import Machine
from .user_story import UserStory


class DevelopmentMachine(Machine):
    """Machine for development phase with error detection."""

    def __init__(self, capacity: int):
        super().__init__("Development", capacity)
        self.error_queue: List[UserStory] = []  # Stories that need to go back

    def process_takt(self) -> List[UserStory]:
        """Process one tick for all active stories."""
        completed_stories = []

        for story in self.active_stories[:]:  # Copy list as we might modify it
            if story.errors.has_spec_revision_needed:
                # Story needs to go back to specification
                self.error_queue.append(story)
                self.active_stories.remove(story)
                continue

            if story.errors.has_dev_debug_needed:
                # Add an extra day of development time
                story.remaining_days += 1
                story.errors.has_dev_debug_needed = False  # Reset flag

            if story.process_day():
                completed_stories.append(story)

        return completed_stories

    def get_error_stories(self) -> List[UserStory]:
        """Return and clear the error queue"""
        stories = self.error_queue[:]
        self.error_queue.clear()
        return stories
