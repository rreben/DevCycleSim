from dataclasses import dataclass, field
import numpy as np
from devcyclesim.src.user_story import Phase, UserStory, StoryStatus
from typing import Optional


@dataclass
class ProcessStep:
    """
    A process step in the development process.
    Manages tasks in three queues:
    - Input Queue
    - Work in Progress
    - Done List
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
        """Validates the input parameters"""
        if self._capacity <= 0:
            raise ValueError("Capacity must be positive")

    @property
    def capacity(self) -> int:
        """Returns the current capacity"""
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        """Sets the capacity to a new value"""
        if value <= 0:
            raise ValueError("Capacity must be positive")
        self._capacity = value

    def add(self, story: UserStory) -> None:
        """
        Adds a user story to the input queue (FIFO).

        Args:
            story: The user story to be added
        """
        self.input_queue = np.append(self.input_queue, [story])

    def pluck(self) -> Optional[UserStory]:
        """
        Removes and returns the first user story from the done queue.

        Returns:
            Optional[UserStory]: The first story from the done queue or None
            if the queue is empty
        """
        if len(self.done) == 0:
            return None

        # Since we know that only UserStories are stored,
        # the type cast is safe
        story: UserStory = self.done[0]  # type: ignore

        # Remove the first element
        self.done = self.done[1:]

        return story

    def adjust_workload_to_capacity(self) -> None:
        """
        Adjusts the number of user stories in work_in_progress to match
        the capacity.

        When capacity is exceeded (e.g., due to capacity reduction),
        stories are moved back from work_in_progress to the input queue.
        These stories are placed at the beginning of the input queue since
        work has already been done on them. This ensures they will be
        picked up next when capacity becomes available.
        """
        current_load = len(self.work_in_progress)

        # Case 1: More capacity than work -> get stories from input queue
        while current_load < self._capacity and len(self.input_queue) > 0:
            # Take first story from input queue
            story: UserStory = self.input_queue[0]  # type: ignore
            self.input_queue = self.input_queue[1:]

            # Add story to work in progress
            self.work_in_progress = np.append(self.work_in_progress, [story])
            current_load += 1

        # Case 3: Less capacity than work -> move stories back to input queue
        while current_load > self._capacity:
            # Take last story from work in progress
            story: UserStory = self.work_in_progress[-1]  # type: ignore
            self.work_in_progress = self.work_in_progress[:-1]

            # Place story at the beginning of input queue
            self.input_queue = np.insert(self.input_queue, 0, story)
            current_load -= 1

    def start_of_day_processing(self, day: int) -> None:
        """
        Performs the processing at the start of the day.

        Args:
            day: Current simulation day
        """
        # Perform capacity adjustment
        self.adjust_workload_to_capacity()

        # Start all stories in work in progress
        for story in self.work_in_progress:
            if story.status != StoryStatus.IN_PROGRESS:
                story.start_user_story()

    def day_processing(self, day: int) -> None:
        """
        Performs the processing during the day.
        Ensures that all stories are in the correct phase for this step.

        Args:
            day: Current simulation day

        Raises:
            ValueError: If a story's current phase does not match the
                process step's phase, indicating a simulation error
        """
        # Process all stories in work in progress
        for story in self.work_in_progress:
            # Validate that story is in the correct phase
            if story.current_phase != self.phase:
                msg = (
                    f"Story {story.story_id} in wrong phase: "
                    f"{story.current_phase}, expected: {self.phase}. "
                    f"Simulation error detected."
                )
                raise ValueError(msg)
            story.process_day(day)

    def end_of_day_processing(self, day: int) -> None:
        """
        Performs the processing at the end of the day.

        Args:
            day: Current simulation day
        """
        # Identify completed stories
        stories_to_move = []
        remaining_stories = []

        for story in self.work_in_progress:
            if story.status in [StoryStatus.DONE, StoryStatus.PHASE_DONE]:
                stories_to_move.append(story)
            else:
                remaining_stories.append(story)

        # Move completed stories to done queue
        self.done = np.append(self.done, stories_to_move)

        # Update work in progress
        self.work_in_progress = np.array(remaining_stories, dtype=object)

    def process_day(self, day: int) -> None:
        """
        Performs the complete daily processing.

        Args:
            day: Current simulation day
        """
        self.start_of_day_processing(day)
        self.day_processing(day)
        self.end_of_day_processing(day)

    def count_input_queue(self) -> int:
        """
        Returns the number of user stories in the input queue.

        Returns:
            int: Number of stories in input queue
        """
        return len(self.input_queue)

    def count_work_in_progress(self) -> int:
        """
        Returns the number of user stories currently in work.

        Returns:
            int: Number of stories in work in progress
        """
        return len(self.work_in_progress)

    def count_done(self) -> int:
        """
        Returns the number of completed user stories.

        Returns:
            int: Number of stories in done queue
        """
        return len(self.done)
