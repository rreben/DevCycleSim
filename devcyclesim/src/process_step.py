from dataclasses import dataclass, field
import numpy as np
from devcyclesim.src.user_story import Phase, UserStory, StoryStatus
from typing import Optional, Dict, Set
from enum import Enum

class ReleasePolicy(Enum):
    CONTINUOUS = "continuous"
    BATCH_FEATURE = "batch_feature"



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
    release_policy: "ReleasePolicy" = field(default="continuous") # type: ignore
    feature_story_counts: Dict[str, int] = field(default_factory=dict)
    released_features: set[str] = field(default_factory=set)
    
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
        if self._capacity < 0:
            raise ValueError("Capacity must not be negative")
        
        # Ensure release_policy is an instance of ReleasePolicy
        if isinstance(self.release_policy, str):
            if self.release_policy == "continuous":
                self.release_policy = ReleasePolicy.CONTINUOUS
            elif self.release_policy == "batch_feature":
                self.release_policy = ReleasePolicy.BATCH_FEATURE
            else:
                 self.release_policy = ReleasePolicy.CONTINUOUS

    @property
    def capacity(self) -> int:
        """Returns the current capacity"""
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        """
        Sets the capacity to a new value.
        Validates that the new capacity is not negative.

        Args:
            value: New capacity value

        Raises:
            ValueError: If capacity is not not negative
        """
        if value < 0:
            raise ValueError("Capacity must not be negative")
        self._capacity = value

    def add(self, story: UserStory) -> None:
        """
        Adds a user story to the input queue (FIFO).

        Args:
            story: The user story to be added
        """
        self.input_queue = np.append(self.input_queue, [story])

    def add_in_front(self, story: UserStory) -> None:
        """
        Adds a user story to the front of the input queue.
        Used for high priority stories that need immediate attention.

        Args:
            story: The user story to be added at the front
        """
        self.input_queue = np.insert(self.input_queue, 0, story)

    def pluck(self) -> Optional[UserStory]:
        """
        Removes and returns the first user story from the done queue.
        
        If release_policy is BATCH_FEATURE, it only returns a story if all
        stories of the corresponding feature are in the done queue (or already released).

        Returns:
            Optional[UserStory]: The first story from the done queue or None
            if the queue is empty
        """
        if len(self.done) == 0:
            return None

        if self.release_policy == ReleasePolicy.CONTINUOUS:
            # Standard behavior: take the first one
            story: UserStory = self.done[0]  # type: ignore
            self.done = self.done[1:]
            return story
        
        elif self.release_policy == ReleasePolicy.BATCH_FEATURE:
            # Batch behavior: find a story that belongs to a completed feature
            
            # 1. Identify stories in Done queue by feature
            done_counts_by_feature = {}
            for s in self.done:
                fid = s.feature_id
                done_counts_by_feature[fid] = done_counts_by_feature.get(fid, 0) + 1
            
            candidate_index = -1
            
            for i, story in enumerate(self.done):
                fid = story.feature_id
                
                # Check if feature is already being released
                if fid in self.released_features:
                    candidate_index = i
                    break
                
                # Check if feature is complete in Done queue
                # We need the total count of stories for this feature
                total_count = self.feature_story_counts.get(fid, 0)
                
                # If we don't know the total count, we assume it's 1 (safe fallback) or treat as continuous?
                # Let's assume strict batching: if unknown, we might be stuck. 
                # But Process should populate this. 
                
                current_done_count = done_counts_by_feature.get(fid, 0)
                
                if total_count > 0 and current_done_count >= total_count:
                    # Feature is complete! Start releasing.
                    self.released_features.add(fid)
                    candidate_index = i
                    break
            
            if candidate_index != -1:
                story: UserStory = self.done[candidate_index] # type: ignore
                # Remove specific element
                self.done = np.delete(self.done, candidate_index)
                
                # Check if this was the last one for this feature in the done queue
                # Re-check counts to see if we should remove from released_features
                # Actually, if we just removed one, we are still releasing.
                # We stop "released_features" status only when no more stories of that feature are in done?
                # Or we keep it forever? simpler: keep it forever in this set is fine, 
                # or remove it when count becomes 0.
                
                # Let's check remaining count
                remaining_count = 0
                for s in self.done:
                    if s.feature_id == story.feature_id:
                        remaining_count += 1
                
                if remaining_count == 0:
                    self.released_features.remove(story.feature_id)
                    
                return story
            
            return None
            
        return None

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

            # Reset story status to pending
            story.status = StoryStatus.PENDING

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
