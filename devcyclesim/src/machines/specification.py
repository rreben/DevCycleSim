from devcyclesim.src.machines.base import Machine
from devcyclesim.src.user_story import UserStory


class SpecificationMachine(Machine):
    """
    Machine for the specification phase.
    Simple implementation without error handling.
    """

    def __init__(self, capacity: int):
        super().__init__("Specification", capacity)

    def process_takt(self) -> "list[UserStory]":
        """
        Process one tick for all active stories.
        Overrides the base method but keeps the same basic functionality
        as no special handling is needed for specification.
        """
        completed_stories = super().process_takt()

        # Advance completed stories to next phase
        for story in completed_stories:
            story.advance_to_next_phase()

        return completed_stories
