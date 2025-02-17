import pytest  # noqa: F401
from devcyclesim.src.machines.specification import SpecificationMachine
from devcyclesim.src.machines.user_story import UserStory, StoryPhase


def test_specification_machine_creation():
    """Test basic creation of specification machine"""
    machine = SpecificationMachine(capacity=2)
    assert machine.name == "Specification"
    assert machine.capacity == 2
    assert len(machine.queue) == 0
    assert len(machine.active_stories) == 0


def test_specification_processing():
    """Test that stories are processed correctly"""
    machine = SpecificationMachine(capacity=1)

    # Create a story with 2 days specification time
    story = UserStory(
        story_id="STORY-1",
        arrival_day=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        }
    )

    # Add and start processing
    machine.enqueue(story)
    machine.start_processing()

    # First day
    completed = machine.process_takt()
    assert len(completed) == 0
    assert story.current_phase == StoryPhase.SPEC

    # Second day - should complete
    completed = machine.process_takt()
    assert len(completed) == 1
    assert completed[0].current_phase == StoryPhase.DEV


def test_multiple_stories_processing():
    """Test processing multiple stories simultaneously"""
    machine = SpecificationMachine(capacity=2)

    story1 = UserStory(
        story_id="STORY-1",
        arrival_day=1,
        phase_durations={
            "spec": 1,
            "dev": 5,
            "test": 3,
            "rollout": 1
        }
    )
    story2 = UserStory(
        story_id="STORY-2",
        arrival_day=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        }
    )

    machine.enqueue(story1)
    machine.enqueue(story2)
    machine.start_processing()

    # First day - story1 should complete
    completed = machine.process_takt()
    assert len(completed) == 1
    assert completed[0].story_id == "STORY-1"

    # Second day - story2 should complete
    completed = machine.process_takt()
    assert len(completed) == 1
    assert completed[0].story_id == "STORY-2"
