from devcyclesim.src.process_step import ProcessStep
from devcyclesim.src.user_story import (
    UserStory, Phase, StoryStatus
)


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
