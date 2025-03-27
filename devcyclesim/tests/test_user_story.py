import pytest
import numpy as np
from devcyclesim.src.user_story import (
    UserStory, Phase, StoryStatus, Task
)


def create_story_with_spec_error() -> UserStory:
    """Creates a user story with rework in the specification phase.

    The story contains:
    - 2 initial specification tasks
    - 3 development tasks
    - 1 rework task in specification
    - 2 additional development tasks
    - 3 test tasks
    - 1 rollout task
    """
    tasks = np.array([
        Task(Phase.SPEC),
        Task(Phase.SPEC),
        Task(Phase.DEV),
        Task(Phase.DEV),
        Task(Phase.DEV),
        Task(Phase.SPEC),  # Rework in specification
        Task(Phase.DEV),   # Remaining development
        Task(Phase.DEV),
        Task(Phase.TEST),
        Task(Phase.TEST),
        Task(Phase.TEST),
        Task(Phase.ROLLOUT)
    ], dtype=object)

    return UserStory(
        "STORY-2",
        tasks=tasks
    )


def create_story_with_test_error() -> UserStory:
    """Creates a user story with errors found during testing.

    The story contains:
    - 2 initial specification tasks
    - 5 initial development tasks
    - 2 test tasks
    - 3 development tasks for bug fixing
    - 2 additional test tasks for retest
    - 1 rollout task
    """
    tasks = np.array([
        Task(Phase.SPEC),
        Task(Phase.SPEC),
        Task(Phase.DEV),
        Task(Phase.DEV),
        Task(Phase.DEV),
        Task(Phase.DEV),
        Task(Phase.DEV),
        Task(Phase.TEST),
        Task(Phase.TEST),
        Task(Phase.DEV),   # Bug fixing
        Task(Phase.DEV),
        Task(Phase.DEV),
        Task(Phase.TEST),  # Retest
        Task(Phase.TEST),
        Task(Phase.ROLLOUT)
    ], dtype=object)

    return UserStory(
        "STORY-3",
        tasks=tasks
    )


# Example of a normal story
story1 = UserStory.from_phase_durations(
    "STORY-1",
    phase_durations={
        Phase.SPEC: 2,
        Phase.DEV: 5,
        Phase.TEST: 3,
        Phase.ROLLOUT: 1
    }
)


def test_user_story_basic_creation():
    """Test creating a UserStory with default values"""
    story = UserStory.from_phase_durations(
        "STORY-1",
        phase_durations={
            Phase.SPEC: 2,
            Phase.DEV: 5,
            Phase.TEST: 3,
            Phase.ROLLOUT: 1}
    )
    assert story.story_id == "STORY-1"
    assert story.arrival_day == 1
    assert story.priority == 1  # default priority
    assert story.get_total_tasks() == 11
    assert story.status == StoryStatus.PENDING

    # Day 1 - Specification
    story.start_user_story()
    assert story.status == StoryStatus.IN_PROGRESS
    assert story.process_day(1)
    work_done = story.get_completed_work()
    assert work_done[Phase.SPEC] == 1
    assert story.current_phase == Phase.SPEC

    # Day 2 - Specification
    assert story.status == StoryStatus.IN_PROGRESS
    assert story.process_day(2)
    work_done = story.get_completed_work()
    assert work_done[Phase.SPEC] == 2

    # Day 3 - Development cannot start automatically
    assert story.status == StoryStatus.PENDING
    assert not story.process_day(3)
    assert story.current_phase == Phase.DEV
    work_done = story.get_completed_work()
    assert work_done[Phase.SPEC] == 2
    assert work_done[Phase.DEV] == 0

    # Day 3-7 - Development
    story.start_user_story()
    for day in range(3, 8):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        # Day 3 = 1 Task, Day 4 = 2 Tasks, etc.
        assert work_done[Phase.DEV] == day - 2
        if day < 7:
            assert story.current_phase == Phase.DEV

    # Day 8 - Testing cannot start automatically
    assert story.status == StoryStatus.PENDING
    assert not story.process_day(8)
    assert story.current_phase == Phase.TEST
    work_done = story.get_completed_work()
    assert work_done[Phase.DEV] == 5

    # Day 8-10 - Testing
    story.start_user_story()
    for day in range(8, 11):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        # Day 8 = 1 Task, Day 9 = 2 Tasks, etc.
        assert work_done[Phase.TEST] == day - 7
        if day < 10:
            assert story.current_phase == Phase.TEST

    # Day 11 - Rollout cannot start automatically
    assert story.status == StoryStatus.PENDING
    assert not story.process_day(11)
    assert story.current_phase == Phase.ROLLOUT
    work_done = story.get_completed_work()
    assert work_done[Phase.TEST] == 3

    # Day 11 - Rollout
    story.start_user_story()
    assert story.status == StoryStatus.IN_PROGRESS
    assert story.process_day(11)
    work_done = story.get_completed_work()
    assert work_done[Phase.ROLLOUT] == 1

    # Story is completely finished
    assert story.status == StoryStatus.DONE
    assert story.current_task is None
    assert story.current_phase is None

    # Check total work done
    final_work = story.get_completed_work()
    assert final_work[Phase.SPEC] == 2
    assert final_work[Phase.DEV] == 5
    assert final_work[Phase.TEST] == 3
    assert final_work[Phase.ROLLOUT] == 1


def test_user_story_with_spec_error():
    """Test a user story with rework in specification phase"""
    # Create story with specification error
    story = create_story_with_spec_error()
    assert story.story_id == "STORY-2"
    assert story.get_total_tasks() == 12
    assert story.status == StoryStatus.PENDING

    # Day 1-2 - Initial specification
    story.start_user_story()
    for day in range(1, 3):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        assert work_done[Phase.SPEC] == day

    # Day 3-5 - First development phase
    story.start_user_story()
    for day in range(3, 6):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        assert work_done[Phase.DEV] == day - 2

    # Day 6 - Back to specification
    assert story.status == StoryStatus.PENDING
    story.start_user_story()
    assert story.process_day(6)
    work_done = story.get_completed_work()
    assert work_done[Phase.SPEC] == 3  # Now 3 spec tasks completed
    assert work_done[Phase.DEV] == 3   # Still 3 dev tasks completed

    # Day 7-8 - Remaining development
    story.start_user_story()
    for day in range(7, 9):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        # Day 7 = 4 Tasks, Day 8 = 5 Tasks
        assert work_done[Phase.DEV] == day - 3

    # Day 9-11 - Testing phase
    story.start_user_story()
    for day in range(9, 12):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        assert work_done[Phase.TEST] == day - 8

    # Day 12 - Rollout
    story.start_user_story()
    assert story.process_day(12)
    work_done = story.get_completed_work()
    assert work_done[Phase.ROLLOUT] == 1

    # Check total work done
    assert story.status == StoryStatus.DONE
    final_work = story.get_completed_work()
    assert final_work[Phase.SPEC] == 3   # 2 initial + 1 rework
    assert final_work[Phase.DEV] == 5    # 3 initial + 2 after spec
    assert final_work[Phase.TEST] == 3
    assert final_work[Phase.ROLLOUT] == 1


def test_user_story_with_test_error():
    """Test a user story with errors found during testing"""
    # Create story with test errors
    story = create_story_with_test_error()
    assert story.story_id == "STORY-3"
    assert story.get_total_tasks() == 15
    assert story.status == StoryStatus.PENDING

    # Day 1-2 - Specification
    story.start_user_story()
    for day in range(1, 3):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        assert work_done[Phase.SPEC] == day

    # Day 3-7 - Initial development
    story.start_user_story()
    for day in range(3, 8):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        assert work_done[Phase.DEV] == day - 2

    # Day 8-9 - First test attempt
    story.start_user_story()
    for day in range(8, 10):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        assert work_done[Phase.TEST] == day - 7

    # Day 10-12 - Bug fixing in development
    story.start_user_story()
    for day in range(10, 13):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        assert work_done[Phase.DEV] == day - 4  # 5 initial + (day-9) fixes

    # Day 13-14 - Retest
    story.start_user_story()
    for day in range(13, 15):
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.process_day(day)
        work_done = story.get_completed_work()
        # 2 initial tests + (day-12) retests
        assert work_done[Phase.TEST] == 2 + (day - 12)

    # Day 15 - Rollout
    story.start_user_story()
    assert story.process_day(15)
    work_done = story.get_completed_work()
    assert work_done[Phase.ROLLOUT] == 1

    # Check total work done
    assert story.status == StoryStatus.DONE
    final_work = story.get_completed_work()
    assert final_work[Phase.SPEC] == 2    # No specification errors
    assert final_work[Phase.DEV] == 8     # 5 initial + 3 bug fixes
    assert final_work[Phase.TEST] == 4    # 2 initial + 2 retest
    assert final_work[Phase.ROLLOUT] == 1


def test_user_story_validation():
    """Test validation of user story parameters"""
    # Test: Negative priority
    with pytest.raises(ValueError, match="Priority must be positive"):
        UserStory.from_phase_durations(
            "STORY-ERR-1",
            phase_durations={
                Phase.SPEC: 1,
                Phase.DEV: 1,
                Phase.TEST: 1,
                Phase.ROLLOUT: 1
            },
            priority=-1
        )

    # Test: Negative arrival day
    with pytest.raises(ValueError, match="Arrival day must be positive"):
        UserStory.from_phase_durations(
            "STORY-ERR-2",
            phase_durations={
                Phase.SPEC: 1,
                Phase.DEV: 1,
                Phase.TEST: 1,
                Phase.ROLLOUT: 1
            },
            arrival_day=-1
        )

    # Test: Empty phase durations
    with pytest.raises(ValueError, match="Phase durations must not be empty"):
        UserStory.from_phase_durations(
            "STORY-ERR-3",
            phase_durations={}
        )

    # Test: Negative phase duration
    with pytest.raises(
            ValueError,
            match="All phase durations must be positive"):
        UserStory.from_phase_durations(
            "STORY-ERR-4",
            phase_durations={
                Phase.SPEC: -1,
                Phase.DEV: 1,
                Phase.TEST: 1,
                Phase.ROLLOUT: 1
            }
        )
