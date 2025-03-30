from dataclasses import dataclass, field
from typing import List

import numpy as np
from devcyclesim.src.process_step import ProcessStep
from devcyclesim.src.user_story import Phase, UserStory, StoryStatus
from devcyclesim.src.process_statistic import ProcessStatistic


@dataclass
class ResourcePlan:
    """
    Defines resource allocation for a specific time period.

    Args:
        start_day: First day of the plan
        end_day: Last day of the plan
        specification_capacity: Capacity for SPEC
        development_capacity: Capacity for DEV
        testing_capacity: Capacity for TEST
        rollout_capacity: Capacity for ROLLOUT
    """
    start_day: int
    end_day: int
    specification_capacity: int
    development_capacity: int
    testing_capacity: int
    rollout_capacity: int

    def __post_init__(self):
        """Validates the ResourcePlan after initialization."""
        if (self.specification_capacity < 0 or
                self.development_capacity < 0 or
                self.testing_capacity < 0 or
                self.rollout_capacity < 0):
            raise ValueError("Capacities cannot be negative")

        if self.start_day > self.end_day:
            raise ValueError("Start day must not be after end day")


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
    statistics: List[ProcessStatistic] = field(
        default_factory=list
    )
    resource_plans: List[ResourcePlan] = field(
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

    def add_resource_plan(self, plan: ResourcePlan) -> None:
        """
        Adds a ResourcePlan to the list of resource plans.

        Args:
            plan: The ResourcePlan to be added
        """
        self.resource_plans.append(plan)

    def _get_phase_step_mapping(self) -> dict:
        """
        Creates a mapping from phases to ProcessSteps.

        Returns:
            Dictionary with Phase -> ProcessStep mapping
        """
        return {
            Phase.SPEC: self.spec_step,
            Phase.DEV: self.dev_step,
            Phase.TEST: self.test_step,
            Phase.ROLLOUT: self.rollout_step
        }

    def _move_story_to_target(
        self,
        story: UserStory,
        current_step: ProcessStep,
        target_step: ProcessStep
    ) -> None:
        """
        Moves a story to the target step.
        Uses add_in_front for backwards movements, add otherwise.

        Args:
            story: The story to be moved
            current_step: Current ProcessStep
            target_step: Target ProcessStep
        """
        # Reset story status
        story.status = StoryStatus.PENDING

        # Determine if this is a step backwards in the process
        phase_order = [
            Phase.SPEC,
            Phase.DEV,
            Phase.TEST,
            Phase.ROLLOUT
        ]
        current_idx = phase_order.index(current_step.phase)
        next_idx = phase_order.index(target_step.phase)

        if next_idx < current_idx:
            # Moving backwards - prioritize with add_in_front
            target_step.add_in_front(story)
        else:
            # Normal flow (same phase or forward) - use regular add
            target_step.add(story)

    def _process_completed_stories(self) -> None:
        """
        Processes completed stories from all process steps.
        Moves stories according to their next phase.
        """
        phase_to_step = self._get_phase_step_mapping()
        steps = [
            self.rollout_step,
            self.test_step,
            self.dev_step,
            self.spec_step
        ]

        for current_step in steps:
            stories_to_process = []
            while (story := current_step.pluck()) is not None:
                stories_to_process.append(story)

            for story in stories_to_process:
                if story.current_phase is None:
                    # Story is completely done
                    if current_step == self.rollout_step:
                        self.finished_work = np.append(
                            self.finished_work, [story]
                        )
                    continue

                # Move story to its next phase
                next_phase = story.current_phase
                target_step = phase_to_step[next_phase]
                self._move_story_to_target(story, current_step, target_step)

    def _move_from_backlog_to_spec(self) -> None:
        """
        Moves stories from backlog to SPEC input queue,
        considering available capacity.
        """
        available_capacity = (
            self.spec_step.capacity
            - self.spec_step.count_work_in_progress()
            - self.spec_step.count_input_queue()
        )

        stories_to_move = []
        remaining_stories = []

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

    def _move_completed_stories(self) -> None:
        """
        Moves completed stories between process steps.
        Processes steps in reverse order (ROLLOUT -> SPEC)
        to prevent blocking.

        Special handling for stories that need rework:
        - Identifies stories that need to go back to an earlier phase
        - Uses add_in_front to prioritize these cases
        - Supports jumps across multiple phases (e.g. ROLLOUT to SPEC)
        """
        self._process_completed_stories()
        self._move_from_backlog_to_spec()

    def _update_capacities(self, day: int) -> None:
        """
        Updates the capacities of all steps based on the ResourcePlan.
        Uses default values if no plan exists.

        Args:
            day: Current simulation day
        """
        # Default capacities
        spec_capacity = 2
        dev_capacity = 3
        test_capacity = 3
        rollout_capacity = 1

        # Search for an active ResourcePlan for the current day
        for plan in self.resource_plans:
            if plan.start_day <= day <= plan.end_day:
                spec_capacity = plan.specification_capacity
                dev_capacity = plan.development_capacity
                test_capacity = plan.testing_capacity
                rollout_capacity = plan.rollout_capacity
                break

        # Update step capacities
        self.spec_step.capacity = spec_capacity
        self.dev_step.capacity = dev_capacity
        self.test_step.capacity = test_capacity
        self.rollout_step.capacity = rollout_capacity

    def start_of_day_processing(self, day: int) -> None:
        """
        Performs the processing at the start of the day.
        Updates capacities and moves completed stories.

        Args:
            day: Current simulation day
        """
        self._update_capacities(day)
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

    def get_statistics(self) -> "list[ProcessStatistic]":
        """
        Returns the collected statistics.

        Returns:
            List of ProcessStatistic objects, one for each simulated day
        """
        return self.statistics
