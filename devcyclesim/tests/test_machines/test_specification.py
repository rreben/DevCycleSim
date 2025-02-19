import pytest  # noqa: F401
from devcyclesim.src.machines.specification import SpecificationMachine
from devcyclesim.src.user_story import (
    UserStory,
    StoryPhase,
    StoryStatus,
    StoryErrors
)


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
        },
        errors=StoryErrors()
    )
    story2 = UserStory(
        story_id="STORY-2",
        arrival_day=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        },
        errors=StoryErrors()
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


def test_specification_queue_processing():
    """Test that stories from queue are processed when capacity
    becomes available
    """
    machine = SpecificationMachine(capacity=2)

    # Create three stories
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
    story2 = UserStory(
        story_id="STORY-2",
        arrival_day=1,
        phase_durations={
            "spec": 3,
            "dev": 5,
            "test": 3,
            "rollout": 1
        },
        errors=StoryErrors()
    )
    story3 = UserStory(
        story_id="STORY-3",
        arrival_day=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        },
        errors=StoryErrors()
    )

    # Initially all stories should be PENDING
    assert story1.status == StoryStatus.PENDING
    assert story2.status == StoryStatus.PENDING
    assert story3.status == StoryStatus.PENDING

    # Add all stories to the machine
    machine.enqueue(story1)
    machine.enqueue(story2)
    machine.enqueue(story3)

    # Start processing - should only take first two stories due to capacity
    machine.start_processing()
    assert len(machine.active_stories) == 2
    assert len(machine.queue) == 1
    assert machine.queue[0].story_id == "STORY-3"

    # First two stories should be IN_PROGRESS, third still PENDING
    assert story1.status == StoryStatus.IN_PROGRESS
    assert story2.status == StoryStatus.IN_PROGRESS
    assert story3.status == StoryStatus.PENDING

    # Process first day - no completions
    completed = machine.process_takt()
    assert len(completed) == 0
    assert len(machine.active_stories) == 2
    assert len(machine.queue) == 1

    # Status should remain the same after first day
    assert story1.status == StoryStatus.IN_PROGRESS
    assert story2.status == StoryStatus.IN_PROGRESS
    assert story3.status == StoryStatus.PENDING

    # Process second day - story1 should complete
    completed = machine.process_takt()
    assert len(completed) == 1
    assert completed[0].story_id == "STORY-1"

    # Story1 should now be in DEV phase and PENDING
    assert story1.current_phase == StoryPhase.DEV
    assert story1.status == StoryStatus.PENDING
    assert story2.status == StoryStatus.IN_PROGRESS
    assert story3.status == StoryStatus.PENDING

    # Story3 should now be moved from queue to active
    machine.start_processing()
    assert len(machine.active_stories) == 2
    assert len(machine.queue) == 0
    assert any(story.story_id == "STORY-3" for story in machine.active_stories)

    # Story2 and Story3 should both be IN_PROGRESS now
    assert story1.status == StoryStatus.PENDING  # Still PENDING in DEV phase
    assert story2.status == StoryStatus.IN_PROGRESS
    assert story3.status == StoryStatus.IN_PROGRESS
