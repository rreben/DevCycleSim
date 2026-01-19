from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List
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
    
    # Rework / Defect properties
    is_correction: bool = False
    defect_discovery_phase: Optional[Phase] = None
    completed_at: Optional[int] = None  # To track "Age" of the task/code

    def complete(self, day: int) -> None:
        """Marks the task as completed"""
        self.status = TaskStatus.DONE
        self.completed_on_day = day
        self.completed_at = day


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
    feature_id: str = "default_feature"
    status: StoryStatus = field(default=StoryStatus.PENDING)
    current_task_index: int = field(default=0)
    
    # Configuration
    # rework_factor defines how much the rework effort increases with defect age (days since origin completion).
    rework_factor: float = 0.1

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
        priority: int = 1,
        feature_id: str = "default_feature"
    ) -> 'UserStory':
        """
        Creates a UserStory from phase durations.
        For each day in a phase, a separate task is created.

        Args:
            story_id: ID of the story
            phase_durations: Dict with Phase -> number of days
            arrival_day: Arrival day of the story
            priority: Priority of the story
            feature_id: str = "default_feature"

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
            priority=priority,
            feature_id=feature_id
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

    def _calculate_correction_chain(self, origin_task: Task, current_day: int) -> List[Task]:
        """
        Calculates the sequence of correction tasks needed when a defect is found.
        
        Logic:
        1. Identify path from Origin Phase to Discovery Phase (current phase).
           Example: Origin=SPEC, Discovery=TEST -> Path=[SPEC, DEV, TEST]
        2. For each phase in path, calculate number of correction tasks based on defect age.
        """
        origin_phase = origin_task.phase
        # Use the phase directly from the current task if available, or the planned discovery phase
        discovery_phase = origin_task.defect_discovery_phase
        
        if not discovery_phase:
             return []

        # Define standard phase order
        phase_order = [Phase.SPEC, Phase.DEV, Phase.TEST, Phase.ROLLOUT]
        
        try:
            start_idx = phase_order.index(origin_phase)
            end_idx = phase_order.index(discovery_phase)
        except ValueError:
            # Should not happen if phases are valid
            return []
            
        # The chain includes all phases from origin up to (and including?) discovery?
        # Requirement: "Spec error found in Test: Chain [SPEC, DEV, TEST]"
        # So yes, inclusive.
        correction_phases = phase_order[start_idx : end_idx + 1]
        
        # Calculate Age
        # "Code Rot" starts when the defective task was completed.
        completed_at = origin_task.completed_at
        if completed_at is None:
            raise ValueError(
                f"Defect found in task {origin_task} but it has no completion date. "
                "This indicates a logic error in defect triggering."
            )
            
        age = max(0, current_day - completed_at)
        
        new_tasks = []
        for phase in correction_phases:
            # Formula: effort = max(1, round(base + (age * factor)))
            # Base cost for a correction step is 1 day.
            base_cost = 1.0
            effort_float = base_cost + (age * self.rework_factor)
            effort_days = int(round(effort_float))
            effort_days = max(1, effort_days)
            
            for _ in range(effort_days):
                new_tasks.append(Task(
                    phase=phase,
                    is_correction=True
                ))
                
        return new_tasks

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
            
        # 1. Check for Defect Discovery TRIGGER (Before completion? Or after?)
        # Requirement: "Defect discovery phase... triggered when the story enters the specified phase"
        # Since we process task-by-task, "entering the phase" happens when we start processing the FIRST task of that phase.
        # However, checking every task is also fine. Let's check if the CURRENT task triggers discovery of a PAST defect.
        
        # We need to iterate over ALL previous tasks to see if any have a latent defect 
        # that triggers in the current task's phase.
        # Optimization: We could store latent defects in a list, but iterating current tasks is fast enough.
        
        rework_triggered = False
        
        # Only check for defects if we are strictly proceeding (not already reworking?)
        # Or can a rework task also trigger a defect? Let's assume only original tasks have defined defects for now.
        
        # Find latent defects
        current_phase = task.phase
        
        # Scan all completed tasks for defects that trigger in this phase
        for i, past_task in enumerate(self.tasks):
            if (past_task.status == TaskStatus.DONE and 
                past_task.defect_discovery_phase == current_phase):
                 
                if past_task.completed_at is None:
                     raise ValueError(f"Task {i} has defect but no completion date.")

                # Trigger Rework!
                correction_chain = self._calculate_correction_chain(past_task, current_day)
                
                # Consumed: Clear the defect trigger so it doesn't trigger again for the next task in the same phase
                past_task.defect_discovery_phase = None 
                
                if correction_chain:
                    # Insert correction chain IMMEDIATELY after current position
                    # We utilize numpy's insert.
                    # Note: We insert at current_task_index (pushing current task back?)
                    # OR do we finish current task?
                    # "If a Spec error found in Test... we insert Spec Correction..."
                    # Usually discovery happens DURING the performing of a task.
                    # So we stop the current task (it's blocked/failed).
                    # Actually, simulation step says "process_day" completes the task.
                    # If we find a bug, maybe we DON'T complete the current task?
                    # But the "Discovery" itself effectively takes time.
                    # Let's say: We catch it NOW. We insert tasks BEFORE the next step?
                    # Ideally: The current task reveals the bug. The current task is "Investigating".
                    # Simplest model: Complete current task (Day spent finding bug). 
                    # Then insert cleanup tasks.
                    
                    # Insert at index + 1
                    insert_pos = self.current_task_index + 1
                    self.tasks = np.insert(self.tasks, insert_pos, correction_chain)
                    
                    # Since we added tasks 'ahead', the next task in next loop will be the first correction task.
                    # If the first correction task is DIFFERENT phase, status updates to PHASE_DONE automatically below.
                    rework_triggered = True
                    
                    # We only process ONE defect discovery per day to avoid chaos?
                    # Yes, break after first discovery.
                    break
        
        # Complete current task (whether we found a bug or not, time passed)
        current_phase_before_complete = task.phase
        task.complete(current_day)

        # Move to next task
        self.current_task_index += 1

        # Check if all tasks are completed
        if self.current_task_index >= len(self.tasks):
            self.status = StoryStatus.DONE
            return True

        # Check if the next task belongs to the same phase
        next_task = self.current_task
        if next_task and next_task.phase != current_phase_before_complete:
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
        
    def get_value_tasks_count(self) -> int:
        """
        Returns number of tasks that are NOT correction tasks.
        Used for Burndown (Value) calculation.
        """
        return sum(1 for t in self.tasks if not t.is_correction)

    def get_task_completion_dates(
        self
    ) -> "dict[str, list[tuple[Phase, int, bool]]]":
        """
        Returns the completion dates of all tasks.

        Returns:
            Dict with task completion information:
            {
                "completed": [(phase, completion_day, is_correction), ...],
                "pending": [(phase, None, is_correction), ...]
            }
        """
        completed = []
        pending = []

        for task in self.tasks:
            if task.status == TaskStatus.DONE:
                completed.append((task.phase, task.completed_on_day, task.is_correction))
            else:
                pending.append((task.phase, None, task.is_correction))

        return {
            "completed": completed,
            "pending": pending
        }
