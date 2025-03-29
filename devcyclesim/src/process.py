from dataclasses import dataclass, field
import numpy as np
from devcyclesim.src.process_step import ProcessStep
from devcyclesim.src.user_story import Phase, UserStory, StoryStatus
from devcyclesim.src.process_statistic import ProcessStatistic


@dataclass
class Process:
    """
    Represents a complete development process with multiple steps.
    Stories flow through the steps in sequence: SPEC -> DEV -> TEST -> ROLLOUT.
    Completed stories are collected in the finished_work queue.

    Args:
        simulation_days: Number of days to simulate (default: 14)
    """
    simulation_days: int = 14
    backlog: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=object)
    )
    finished_work: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=object)
    )
    statistics: 'list[ProcessStatistic]' = field(
        default_factory=list
    )

    def __post_init__(self):
        """Initializes the process steps with their default capacities"""
        self.spec_step = ProcessStep(
            name="Specification",
            phase=Phase.SPEC,
            _capacity=2
        )
        self.dev_step = ProcessStep(
            name="Development",
            phase=Phase.DEV,
            _capacity=3
        )
        self.test_step = ProcessStep(
            name="Testing",
            phase=Phase.TEST,
            _capacity=3
        )
        self.rollout_step = ProcessStep(
            name="Rollout",
            phase=Phase.ROLLOUT,
            _capacity=1
        )

    def add(self, story: UserStory) -> None:
        """
        Adds a user story to the backlog.

        Args:
            story: The user story to be added
        """
        self.backlog = np.append(self.backlog, [story])

    def _move_completed_stories(self) -> None:
        """
        Moves completed stories between process steps and updates their status.
        Stories are moved in reverse order (ROLLOUT -> TEST -> DEV -> SPEC)
        to prevent blocking.
        Also moves stories from backlog to SPEC input queue
        considering available capacity.
        """
        # Move completed stories from ROLLOUT to finished_work
        while (story := self.rollout_step.pluck()) is not None:
            self.finished_work = np.append(self.finished_work, [story])

        # Move completed stories from TEST to ROLLOUT
        while (story := self.test_step.pluck()) is not None:
            story.status = StoryStatus.PENDING
            self.rollout_step.add(story)

        # Move completed stories from DEV to TEST
        while (story := self.dev_step.pluck()) is not None:
            story.status = StoryStatus.PENDING
            self.test_step.add(story)

        # Move completed stories from SPEC to DEV
        while (story := self.spec_step.pluck()) is not None:
            story.status = StoryStatus.PENDING
            self.dev_step.add(story)

        # Move stories from backlog to SPEC input queue considering capacity
        available_capacity = (
            self.spec_step.capacity
            - self.spec_step.count_work_in_progress()
            - self.spec_step.count_input_queue()
        )

        stories_to_move = []
        remaining_stories = []

        # Sort stories into two groups: to be moved and to remain in backlog
        for story in self.backlog:
            if available_capacity > 0:
                stories_to_move.append(story)
                available_capacity -= 1
            else:
                remaining_stories.append(story)

        # Update backlog to contain only remaining stories
        self.backlog = np.array(remaining_stories, dtype=object)

        # Add stories to SPEC input queue
        for story in stories_to_move:
            story.status = StoryStatus.PENDING
            self.spec_step.add(story)

    def start_of_day_processing(self, day: int) -> None:
        """
        Performs the processing at the start of the day.
        Moves completed stories from one step to the next.

        Args:
            day: Current simulation day
        """
        self._move_completed_stories()

    def day_processing(self, day: int) -> None:
        """
        Processes all steps for the current day.

        Args:
            day: Current simulation day
        """
        self.spec_step.process_day(day)
        self.dev_step.process_day(day)
        self.test_step.process_day(day)
        self.rollout_step.process_day(day)

    def end_of_day_processing(self, day: int) -> None:
        """
        Collects statistics at the end of the day.
        Creates a ProcessStatistic object with the current state
        of all queues and adds it to the statistics list.

        Args:
            day: Current simulation day
        """
        # Create statistics for current day
        stats = ProcessStatistic.from_process(self, day)
        self.statistics.append(stats)

    def process_day(self, day: int) -> None:
        """
        Performs the complete daily processing.

        Args:
            day: Current simulation day
        """
        self.start_of_day_processing(day)
        self.day_processing(day)
        self.end_of_day_processing(day)

    def start(self) -> None:
        """
        Starts the process simulation and runs it for the specified
        number of days.
        """
        for day in range(1, self.simulation_days + 1):
            self.process_day(day)

    def get_statistics(self) -> 'list[ProcessStatistic]':
        """
        Returns the collected statistics.

        Returns:
            List of ProcessStatistic objects, one for each simulated day
        """
        return self.statistics
