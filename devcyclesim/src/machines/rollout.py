from .base import Machine
from devcyclesim.src.user_story import UserStory, StoryStatus


class RolloutMachine(Machine):
    """
    Machine for the rollout phase.
    Final phase that marks stories as done upon completion.
    """

    def __init__(self, capacity: int):
        super().__init__("Rollout", capacity)

    def process_takt(self) -> "list[UserStory]":
        """
        Process one tick for all active stories.
        Mark completed stories as DONE.
        """
        completed_stories = super().process_takt()

        # Mark completed stories as DONE
        for story in completed_stories:
            story.advance_to_next_phase()
            story.status = StoryStatus.DONE

        return completed_stories
