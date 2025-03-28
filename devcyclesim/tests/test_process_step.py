from devcyclesim.src.process_step import ProcessStep
from devcyclesim.src.user_story import (
    UserStory, Phase, StoryStatus
)
import pytest


def test_process_step_spec_phase():
    """
    Tests a ProcessStep in SPEC phase processing a simple user story.
    The story requires:
    - 2 days in SPEC
    - 3 days in DEV
    - 3 days in TEST
    - 1 day in ROLLOUT
    After 2 days, the story should be in the done queue of the SPEC step.
    """
    # Create process step for specification phase
    spec_step = ProcessStep(
        name="Specification",
        phase=Phase.SPEC,
        _capacity=1
    )

    # Create a user story with defined phase durations
    story = UserStory.from_phase_durations(
        "STORY-1",
        phase_durations={
            Phase.SPEC: 2,
            Phase.DEV: 3,
            Phase.TEST: 3,
            Phase.ROLLOUT: 1
        }
    )

    # Add story to process step
    spec_step.add(story)

    # Initial state checks
    assert spec_step.count_input_queue() == 1
    assert spec_step.count_work_in_progress() == 0
    assert spec_step.count_done() == 0

    # Process day 1
    spec_step.process_day(1)
    assert spec_step.count_input_queue() == 0
    assert spec_step.count_work_in_progress() == 1
    assert spec_step.count_done() == 0

    # Process day 2
    spec_step.process_day(2)
    assert spec_step.count_input_queue() == 0
    assert spec_step.count_work_in_progress() == 0
    assert spec_step.count_done() == 1

    # Verify story state
    completed_story = spec_step.pluck()
    assert completed_story is not None
    assert completed_story.status == StoryStatus.PHASE_DONE

    # Verify completed work
    completed_work = completed_story.get_completed_work()
    assert completed_work[Phase.SPEC] == 2  # Both SPEC tasks done
    assert completed_work[Phase.DEV] == 0   # No DEV tasks started
    assert completed_work[Phase.TEST] == 0  # No TEST tasks started
    assert completed_work[Phase.ROLLOUT] == 0  # No ROLLOUT tasks started


def test_process_step_capacity_reduction():
    """
    Tests the behavior when capacity is reduced while stories are in progress.
    Three stories, each requiring 3 days in SPEC phase, with initial capacity
    of 2 that gets reduced to 1 on day 2.

    Expected behavior:
    - Initially 2 stories move to work in progress
    - On day 2, capacity reduction forces one story back to input queue
    - The returned story should be at the start of the input queue
    - The returned story should be in PENDING status
    - All stories should eventually complete after 8 days

    Story progression:
    Story 1: Days 1-3 (continuous work)
    Story 2: Day 1 + Days 4-5 (interrupted, keeps 1 day of progress)
    Story 3: Days 6-8 (starts after others complete)
    """
    # Create process step for specification phase with capacity 2
    spec_step = ProcessStep(
        name="Specification",
        phase=Phase.SPEC,
        _capacity=2
    )

    # Create three identical stories
    stories = []
    for i in range(3):
        story = UserStory.from_phase_durations(
            f"STORY-{i+1}",
            phase_durations={
                Phase.SPEC: 3,
                Phase.DEV: 2,
                Phase.TEST: 2,
                Phase.ROLLOUT: 1
            }
        )
        spec_step.add(story)
        stories.append(story)

    # Initial state checks
    assert spec_step.count_input_queue() == 3
    assert spec_step.count_work_in_progress() == 0
    assert spec_step.count_done() == 0

    # Process day 1 - should move 2 stories to work in progress
    spec_step.process_day(1)
    assert spec_step.count_input_queue() == 1
    assert spec_step.count_work_in_progress() == 2
    assert spec_step.count_done() == 0

    # Verify that first two stories are in progress
    for story in spec_step.work_in_progress:
        story_obj: UserStory = story  # type: ignore
        assert story_obj.status == StoryStatus.IN_PROGRESS
        work_done = story_obj.get_completed_work()
        assert work_done[Phase.SPEC] == 1

    # Reduce capacity to 1 and process day 2
    spec_step.capacity = 1
    spec_step.process_day(2)

    # Verify that one story was moved back to input queue
    assert spec_step.count_input_queue() == 2
    assert spec_step.count_work_in_progress() == 1
    assert spec_step.count_done() == 0

    # The story that was moved back should be at the start of the input queue
    returned_story: UserStory = spec_step.input_queue[0]  # type: ignore
    assert returned_story.status == StoryStatus.PENDING
    work_done = returned_story.get_completed_work()
    assert work_done[Phase.SPEC] == 1  # One day of work was completed

    # The story still in work should continue progressing
    active_story: UserStory = spec_step.work_in_progress[0]  # type: ignore
    assert active_story.status == StoryStatus.IN_PROGRESS
    work_done = active_story.get_completed_work()
    assert work_done[Phase.SPEC] == 2  # Two days of work completed

    # Process day 3 - first story completes
    spec_step.process_day(3)
    # Both stories remain: the returned one and the original third
    assert spec_step.count_input_queue() == 2
    assert spec_step.count_work_in_progress() == 0
    assert spec_step.count_done() == 1

    # First completed story checks
    completed_story: UserStory = spec_step.done[0]  # type: ignore
    assert completed_story.status == StoryStatus.PHASE_DONE
    work_done = completed_story.get_completed_work()
    assert work_done[Phase.SPEC] == 3

    # Process day 4 - next story starts (the one with prior work)
    spec_step.process_day(4)
    assert spec_step.count_input_queue() == 1  # One story waiting
    assert spec_step.count_work_in_progress() == 1
    assert spec_step.count_done() == 1

    # Check progress of restarted story
    active_story: UserStory = spec_step.work_in_progress[0]  # type: ignore
    work_done = active_story.get_completed_work()
    assert work_done[Phase.SPEC] == 2  # One day from before + one new day

    # Process day 5 - second story completes (had 1 day done before)
    spec_step.process_day(5)
    assert spec_step.count_input_queue() == 1
    assert spec_step.count_work_in_progress() == 0
    assert spec_step.count_done() == 2

    # Process day 6 - third story starts
    spec_step.process_day(6)
    assert spec_step.count_input_queue() == 0
    assert spec_step.count_work_in_progress() == 1
    assert spec_step.count_done() == 2

    # Process day 7 - third story continues
    spec_step.process_day(7)
    active_story: UserStory = spec_step.work_in_progress[0]  # type: ignore
    work_done = active_story.get_completed_work()
    assert work_done[Phase.SPEC] == 2  # Two days completed

    # Process day 8 - third story completes
    spec_step.process_day(8)
    assert spec_step.count_input_queue() == 0
    assert spec_step.count_work_in_progress() == 0
    assert spec_step.count_done() == 3

    # Final verification - all stories completed SPEC phase
    for story in spec_step.done:
        story_obj: UserStory = story  # type: ignore
        assert story_obj.status == StoryStatus.PHASE_DONE
        work_done = story_obj.get_completed_work()
        assert work_done[Phase.SPEC] == 3  # All SPEC work completed
        assert work_done[Phase.DEV] == 0   # No DEV work started
        assert work_done[Phase.TEST] == 0  # No TEST work started
        assert work_done[Phase.ROLLOUT] == 0  # No ROLLOUT work started


def test_process_step_wrong_phase():
    """
    Tests that a ValueError is raised when trying to process a story
    in the wrong phase.

    Scenario:
    - Create a story that starts in SPEC phase
    - Try to process it in a DEV process step
    - Should raise ValueError with appropriate message
    - Story should remain in work_in_progress as the error occurs during
      day_processing, after the story has been moved from input_queue
    """
    # Create process step for development phase
    dev_step = ProcessStep(
        name="Development",
        phase=Phase.DEV,
        _capacity=1
    )

    # Create a story that starts in SPEC phase
    story = UserStory.from_phase_durations(
        "STORY-1",
        phase_durations={
            Phase.SPEC: 2,
            Phase.DEV: 3,
            Phase.TEST: 2,
            Phase.ROLLOUT: 1
        }
    )

    # Add story to process step
    dev_step.add(story)

    # Initial state checks
    assert dev_step.count_input_queue() == 1
    assert dev_step.count_work_in_progress() == 0

    # Try to process the story - should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        dev_step.process_day(1)

    # Verify the error message
    expected_msg = (
        "Story STORY-1 in wrong phase: Phase.SPEC, expected: Phase.DEV. "
        "Simulation error detected."
    )
    assert str(exc_info.value) == expected_msg

    # Verify that story is in work_in_progress
    # (moved there by start_of_day_processing before the phase validation)
    assert dev_step.count_input_queue() == 0
    assert dev_step.count_work_in_progress() == 1
    assert dev_step.count_done() == 0

    # Verify story state
    story_obj: UserStory = dev_step.work_in_progress[0]  # type: ignore
    assert story_obj.status == StoryStatus.IN_PROGRESS
    assert story_obj.current_phase == Phase.SPEC
