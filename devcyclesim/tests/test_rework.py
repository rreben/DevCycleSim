
import pytest
import numpy as np
from devcyclesim.src.user_story import UserStory, Task, Phase, TaskStatus

class TestRework:

    def setup_method(self):
        self.rework_factor = 0.5
        
    def create_story_with_defect(self, defect_phase: Phase, discovery_phase: Phase, arrival_day: int=1):
        """Helper to create a story with one task in each phase, with a defect."""
        tasks = [
            Task(phase=Phase.SPEC),
            Task(phase=Phase.DEV),
            Task(phase=Phase.TEST),
            Task(phase=Phase.ROLLOUT)
        ]
        
        # Determine index of defect task
        phase_map = {Phase.SPEC: 0, Phase.DEV: 1, Phase.TEST: 2, Phase.ROLLOUT: 3}
        idx = phase_map[defect_phase]
        
        tasks[idx].defect_discovery_phase = discovery_phase
        
        story = UserStory(
            story_id="TEST-1",
            tasks=np.array(tasks, dtype=object),
            arrival_day=arrival_day,
            rework_factor=self.rework_factor
        )
        story.start_user_story()
        return story

    def run_story_until_phase(self, story: UserStory, target_phase: Phase, start_day: int = 1):
        """Runs the story day by day until it reaches the target phase."""
        current_day = start_day
        while story.current_task and story.current_task.phase != target_phase:
            if story.status == "phase_done" or story.status.value == "phase_done":
                # Simulate moving to next phase
                story.status = story.status.__class__.IN_PROGRESS
            elif story.status == "pending" or story.status.value == "pending":
                 story.status = story.status.__class__.IN_PROGRESS
                 
            processed = story.process_day(current_day)
            if processed:
                 current_day += 1
            else:
                 # Verification to prevent infinite loop if stuck
                 if story.status.value == "phase_done":
                     continue
                 current_day += 1 # Advance day anyway if stuck? 
                 # If we are stuck in a state that doesn't process, break to avoid infinite loop
                 if story.status.value not in ["in_progress", "phase_done"]:
                     story.status = story.status.__class__.IN_PROGRESS # Force start
            
            if not story.current_task: # Completed
                break
        return current_day

    def test_rework_chain_spec_to_test(self):
        """
        Scenario: Defect in Spec, found in Test.
        Expected: Rework chain [SPEC, DEV, TEST] inserted.
        """
        story = self.create_story_with_defect(Phase.SPEC, Phase.TEST)
        
        # Run until TEST phase
        day = self.run_story_until_phase(story, Phase.TEST, start_day=1)
        
        # Verify we are at TEST task
        assert story.current_task.phase == Phase.TEST
        assert story.current_task.is_correction == False
        
        # Ensure status is IN_PROGRESS (it might be PHASE_DONE from previous step)
        if story.status != story.status.__class__.IN_PROGRESS:
             story.status = story.status.__class__.IN_PROGRESS
        
        # Process the TEST task (Discovery triggers here)
        # Note: Discovery happens during the task processing
        story.process_day(day) 
        
        # The Current Task (Original Test) should be DONE
        # The NEXT tasks should be the Correction Chain
        
        # Check if correction tasks were inserted
        # Expected chain: SPEC, DEV, TEST (Correction=True)
        
        next_task = story.tasks[story.current_task_index] 
        assert next_task.phase == Phase.SPEC
        assert next_task.is_correction == True
        
        next_next = story.tasks[story.current_task_index + 1] # Or further if duration > 1
        # Calculate expected duration for first rework
        # Age = Day (Discovery) - Spec Completed Day
        # Spec (idx 0) done on Day 1. Dev (idx 1) done Day 2.
        # Test (idx 2) processes Day 3. So Discovery Day = 3.
        # Spec Completed = 1. Age = 3-1 = 2.
        # Cost = 1 + (2 * 0.5) = 2 days.
        
        # So we expect 2 SPEC correction tasks
        assert story.tasks[story.current_task_index + 1].phase == Phase.SPEC
        assert story.tasks[story.current_task_index + 2].phase == Phase.DEV

    def test_rework_cost_calculation(self):
        """
        Test that rework effort scales with age.
        Defect in SPEC (Day 1), Discovery in ROLLOUT (Day 4).
        Age = 4 - 1 = 3.
        Factor = 0.5.
        Effort = 1 + (3 * 0.5) = 2.5 -> Round to 2 or 3? round(2.5) -> 2 (Python rounding to even) or 3?
        Let's check code: int(round(float))
        """
        story = self.create_story_with_defect(Phase.SPEC, Phase.ROLLOUT)
        
        # Run until ROLLOUT
        # Spec(1), Dev(2), Test(3), Rollout(4)
        day = self.run_story_until_phase(story, Phase.ROLLOUT, 1)
        assert day == 4
        
        if story.status != story.status.__class__.IN_PROGRESS:
             story.status = story.status.__class__.IN_PROGRESS

        story.process_day(day) # Trigger rework at Day 4
        
        # Spec Completion = 1
        # Age = 4 - 1 = 3
        # Cost = 1 + 1.5 = 2.5 -> round(2.5) = 2 (Banker's rounding in Python 3)
        
        # Check inserted tasks
        # Chain: SPEC, DEV, TEST, ROLLOUT
        
        # Get correction tasks
        correction_tasks = [t for t in story.tasks if t.is_correction]
        assert len(correction_tasks) > 0
        
        # Check Spec Correction Count
        spec_corr = [t for t in correction_tasks if t.phase == Phase.SPEC]
        # Expected: 2 (from 2.5 rounded to nearest even)
        assert len(spec_corr) == 2

    def test_missing_completed_at_error(self):
        """
        Ensure ValueError is raised if defect origin has no completion date.
        """
        tasks = [
            Task(phase=Phase.SPEC), # Not processed, so completed_at is None
            Task(phase=Phase.DEV)
        ]
        # Hack: Set defect on uncompleted task
        tasks[0].defect_discovery_phase = Phase.DEV
        
        story = UserStory("TEST-ERR", np.array(tasks, dtype=object), arrival_day=1)
        story.start_user_story()
        
        # Manually complete the first task WITHOUT setting completed_at (simulating corrupt state)
        tasks[0].status = TaskStatus.DONE
        tasks[0].completed_at = None 
        
        # Now try to process the second task which triggers discovery
        story.current_task_index = 1
        
        if story.status != story.status.__class__.IN_PROGRESS:
             story.status = story.status.__class__.IN_PROGRESS

        with pytest.raises(ValueError, match="no completion date"):
            story.process_day(2)

    def test_sequential_discovery(self):
        """
        Two defects in same story.
        1. Spec -> Test
        2. Dev -> Rollout
        """
        tasks = [
            Task(phase=Phase.SPEC),
            Task(phase=Phase.DEV),
            Task(phase=Phase.TEST),
            Task(phase=Phase.ROLLOUT)
        ]
        tasks[0].defect_discovery_phase = Phase.TEST
        tasks[1].defect_discovery_phase = Phase.ROLLOUT
        
        story = UserStory("TEST-MULTI", np.array(tasks, dtype=object), rework_factor=0.5)
        story.start_user_story()
        
        # 1. Run to Test (Day 3). Triggers Spec->Test rework.
        self.run_story_until_phase(story, Phase.TEST, 1)
        
        if story.status != story.status.__class__.IN_PROGRESS:
             story.status = story.status.__class__.IN_PROGRESS

        story.process_day(3)
        
        # Check first rework chain inserted
        # Next tasks should be Spec Correction
        assert story.current_task.phase == Phase.SPEC
        assert story.current_task.is_correction
        
        # 2. Run through rework and Test to Rollout
        # Original Dev defect (idx 1) is still there!
        # Original Rollout task is pushed back
        
        self.run_story_until_phase(story, Phase.ROLLOUT, 4)
        
        # We are at Rollout. It should trigger Dev defect.
        current_day = 10 # Arbitrary later day
        
        if story.status != story.status.__class__.IN_PROGRESS:
             story.status = story.status.__class__.IN_PROGRESS

        story.process_day(current_day)
        
        # Should now have Dev correction tasks inserted
        assert story.current_task.phase == Phase.DEV
        assert story.current_task.is_correction
