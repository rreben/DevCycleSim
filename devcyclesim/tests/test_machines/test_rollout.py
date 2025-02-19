import pytest  # noqa: F401
from devcyclesim.src.machines.rollout import RolloutMachine
from devcyclesim.src.user_story import (
    UserStory, StoryPhase, StoryStatus, StoryErrors
)


def test_rollout_machine_creation():
    """Test basic creation of rollout machine"""
    machine = RolloutMachine(capacity=2)
    assert machine.name == "Rollout"
    assert machine.capacity == 2
    assert len(machine.queue) == 0
    assert len(machine.active_stories) == 0


def test_rollout_processing():
    """Test that stories are processed correctly and marked as done"""
    machine = RolloutMachine(capacity=1)

    story = UserStory(
        story_id="STORY-1",
        arrival_day=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        },
        errors=StoryErrors()
    )
    story.current_phase = StoryPhase.ROLLOUT
    story.remaining_days = story.phase_durations[
        "rollout"
    ]  # Set remaining days explicitly

    # Add and start processing
    machine.enqueue(story)
    machine.start_processing()

    # Process the single day
    completed = machine.process_takt()
    assert len(completed) == 1
    assert completed[0].status == StoryStatus.DONE


def test_multiple_rollout_processing():
    """Test processing multiple stories simultaneously"""
    machine = RolloutMachine(capacity=2)

    # Create story1 with 1 day rollout duration
    story1 = UserStory(
        story_id="STORY-1",
        arrival_day=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        },
        errors=StoryErrors()
    )
    story1.current_phase = StoryPhase.ROLLOUT
    story1.remaining_days = story1.phase_durations["rollout"]

    # Create story2 with 2 days rollout duration
    story2 = UserStory(
        story_id="STORY-2",
        arrival_day=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 2
        },
        errors=StoryErrors()
    )
    story2.current_phase = StoryPhase.ROLLOUT
    story2.remaining_days = story2.phase_durations["rollout"]

    machine.enqueue(story1)
    machine.enqueue(story2)
    machine.start_processing()

    # First day - only story1 should complete (1 day duration)
    # completed list only contains stories finished in this specific takt
    completed = machine.process_takt()
    assert len(completed) == 1
    assert completed[0].story_id == "STORY-1"
    assert completed[0].status == StoryStatus.DONE

    # Second day - only story2 should complete (2 day duration)
    # New completed list for this takt
    completed = machine.process_takt()
    assert len(completed) == 1
    assert completed[0].story_id == "STORY-2"
    assert completed[0].status == StoryStatus.DONE
