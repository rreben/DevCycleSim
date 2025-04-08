from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
import numpy as np


class Phase(Enum):
    SPEC = "spec"
    DEV = "dev"
    TEST = "test"
    ROLLOUT = "rollout"


class TaskStatus(Enum):
    OPEN = "open"
    DONE = "done"


class StoryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PHASE_DONE = "phase_done"
    DONE = "done"


@dataclass
class Task:
    """
    Represents a single work step in a user story.
    Each task takes exactly one day.
    """
    phase: Phase
    status: TaskStatus = TaskStatus.OPEN
    completed_on_day: Optional[int] = None

    def complete(self, day: int) -> None:
        """Marks the task as completed"""
        self.status = TaskStatus.DONE
        self.completed_on_day = day


@dataclass
class UserStory:
    """
    A user story consisting of a sequence of tasks.
    Each task belongs to a phase and takes exactly one day.
    """
    story_id: str
    # A numpy array of Task objects
    tasks: np.ndarray
    arrival_day: int = 1
    priority: int = 1
    status: StoryStatus = field(default=StoryStatus.PENDING)
    current_task_index: int = field(default=0)

    def __post_init__(self):
        """Validates the input parameters"""
        if len(self.tasks) == 0:
            raise ValueError("User Story must have at least one task")
        if self.arrival_day <= 0:
            raise ValueError("Arrival day must be positive")
        if self.priority <= 0:
            raise ValueError("Priority must be positive")

    @classmethod
    def from_phase_durations(
        cls,
        story_id: str,
        phase_durations: Dict[Phase, int],
        arrival_day: int = 1,
        priority: int = 1
    ) -> 'UserStory':
        """
        Creates a UserStory from phase durations.
        For each day in a phase, a separate task is created.

        Args:
            story_id: ID of the story
            phase_durations: Dict with Phase -> number of days
            arrival_day: Arrival day of the story
            priority: Priority of the story

        Returns:
            A new UserStory with corresponding tasks
        """
        # Validate inputs
        if not phase_durations:
            raise ValueError("Phase durations must not be empty")
        if any(duration <= 0 for duration in phase_durations.values()):
            raise ValueError("All phase durations must be positive")

        # Create tasks array
        total_days = sum(phase_durations.values())
        tasks = np.empty(total_days, dtype=object)

        current_index = 0
        for phase, duration in phase_durations.items():
            for _ in range(duration):
                tasks[current_index] = Task(phase=phase)
                current_index += 1

        return cls(
            story_id=story_id,
            tasks=tasks,
            arrival_day=arrival_day,
            priority=priority
        )

    @property
    def current_task(self) -> Optional[Task]:
        """
        Returns the current task or None if all tasks are completed
        """
        if self.current_task_index >= len(self.tasks):
            return None
        return self.tasks[self.current_task_index]  # type: ignore

    @property
    def current_phase(self) -> Optional[Phase]:
        """
        Returns the current phase or None if all tasks are completed
        """
        task = self.current_task
        return task.phase if task else None

    def process_day(self, current_day: int) -> bool:
        """
        Processes a day for the current task and moves to the next one.
        Since each task takes exactly one day, it is completed directly.

        Args:
            current_day: The current simulation day

        Returns:
            bool: True if the task was completed, False otherwise
        """
        if self.status != StoryStatus.IN_PROGRESS:
            return False

        task = self.current_task
        if not task or task.status == TaskStatus.DONE:
            return False

        # Complete current task
        current_phase = task.phase
        task.complete(current_day)

        # Move to next task
        self.current_task_index += 1

        # Check if all tasks are completed
        if self.current_task_index >= len(self.tasks):
            self.status = StoryStatus.DONE
            return True

        # Check if the next task belongs to the same phase
        next_task = self.current_task
        if next_task and next_task.phase != current_phase:
            self.status = StoryStatus.PHASE_DONE

        return True

    def start_user_story(self) -> None:
        """Marks the story as 'in progress'"""
        self.status = StoryStatus.IN_PROGRESS

    def get_phase_durations(self) -> "dict[Phase, int]":
        """
        Calculates the total duration per phase.
        Useful for statistics and analysis.
        """
        durations = {phase: 0 for phase in Phase}
        for task in self.tasks:
            durations[task.phase] += 1  # Each task takes exactly one day
        return durations

    def get_completed_work(self) -> "dict[Phase, int]":
        """
        Calculates the number of already completed tasks per phase.

        Returns:
            Dict with Phase -> number of completed tasks
        """
        completed_work = {phase: 0 for phase in Phase}
        for task in self.tasks:
            if task.status == TaskStatus.DONE:
                completed_work[task.phase] += 1
        return completed_work

    def get_total_tasks(self) -> int:
        """
        Returns the total number of tasks in the user story.

        Returns:
            int: Total number of tasks
        """
        return len(self.tasks)

    def get_task_completion_dates(
        self
    ) -> "dict[str, list[tuple[Phase, int]]]":
        """
        Returns the completion dates of all tasks.

        Returns:
            Dict with task completion information:
            {
                "completed": [(phase, completion_day), ...],
                "pending": [(phase, None), ...]
            }
        """
        completed = []
        pending = []

        for task in self.tasks:
            if task.status == TaskStatus.DONE:
                completed.append((task.phase, task.completed_on_day))
            else:
                pending.append((task.phase, None))

        return {
            "completed": completed,
            "pending": pending
        }
