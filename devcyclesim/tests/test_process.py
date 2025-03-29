from devcyclesim.src.process import Process
from devcyclesim.src.user_story import UserStory, Phase


def test_process_sunny_path():
    """
    Tests the collection and evaluation of process statistics.
    Creates a process with 3 user stories and runs it for 5 days.
    Verifies the state after each simulation day.
    """
    # Create process with 5 simulation days
    process = Process(simulation_days=5)

    # Create three stories with different phase durations
    story1 = UserStory.from_phase_durations(
        "STORY-1",
        phase_durations={
            Phase.SPEC: 1,
            Phase.DEV: 2,
            Phase.TEST: 1,
            Phase.ROLLOUT: 1
        }
    )

    story2 = UserStory.from_phase_durations(
        "STORY-2",
        phase_durations={
            Phase.SPEC: 2,
            Phase.DEV: 1,
            Phase.TEST: 1,
            Phase.ROLLOUT: 1
        }
    )

    story3 = UserStory.from_phase_durations(
        "STORY-3",
        phase_durations={
            Phase.SPEC: 1,
            Phase.DEV: 1,
            Phase.TEST: 2,
            Phase.ROLLOUT: 1
        }
    )

    # Add stories to process
    process.add(story1)
    process.add(story2)
    process.add(story3)

    # Verify default capacities of process steps
    assert process.spec_step.capacity == 2, "SPEC capacity should be 2"
    assert process.dev_step.capacity == 3, "DEV capacity should be 3"
    assert process.test_step.capacity == 3, "TEST capacity should be 3"
    assert process.rollout_step.capacity == 1, "ROLLOUT capacity should be 1"

    # Process each day and verify state
    # After day 1:
    # Story-1 is delivered to SPEC and gets SPEC work done one day
    # Story-1 thus is completed with SPEC and will be moved to dev in the
    # next morning
    # Story-1 Spec 0, Dev 2, Test 1, RO 1; Spec done
    # Story-2 is also delivered to SPEC and gets SPEC work as there
    # is enough capacity. However it requires to days of SPEC.
    # Thus Story_2 stays in Spec.
    # Story-2 Spec 1, Dev 1, Test 1, RO 1; in Spec
    # Story-3 stays in the backlog cause there is no available SPEC
    # Capacity.
    # Story-3 Spec 1, Dev 1, Test 2, RO 1; Still in Backlog due to capa
    # Story-3 will be delivered to Spec the next morning
    process.process_day(1)
    day1_stats = process.get_statistics()[-1]
    assert day1_stats.backlog_count == 1  # Story3
    assert day1_stats.finished_work_count == 0  # No stories finished yet
    assert day1_stats.spec_stats.work_in_progress_count == 1
    assert day1_stats.spec_stats.done_count == 1  # Story1
    assert day1_stats.dev_stats.input_queue_count == 0

    # After day 2:
    # Story-1 is delivered to DEV. It gets work done for one DEV day.
    # Story-1 requires 2 days of Dev so it stays in DEV
    # Story-1 Spec 0, Dev 1, Test 1, RO 1; still in dev
    # Story-2 gets worked on in SPEC for one day
    # Thus Story-2 SPEC is now finished it waits in the done Queue
    # of SPEC to be delivered to DEV the next morning
    # Story-2 Spec 0, Dev 1, Test 1, RO 1; ready for dev
    # Story-3 has been delivered to SPEC, where it has been
    # worked on during the day. As it has only one day of SPEC work
    # it also is ready for dev and will be delivered to dev the next morning
    # Story-3 Spec 1, Dev 1, Test 2, RO 1; ready for dev
    process.process_day(2)
    day2_stats = process.get_statistics()[-1]
    assert day2_stats.backlog_count == 0
    assert day2_stats.finished_work_count == 0  # No stories finished yet
    assert day2_stats.spec_stats.work_in_progress_count == 0
    assert day2_stats.spec_stats.done_count == 2  # Story2
    assert day2_stats.dev_stats.work_in_progress_count == 1
    assert day2_stats.dev_stats.done_count == 0

    # Story-1: wip, and ready for test
    # Story-2: wip, just this day, ready for test
    # Story-3: wip, just this day, ready for test
    process.process_day(3)
    day3_stats = process.get_statistics()[-1]
    assert day3_stats.finished_work_count == 0  # No stories finished yet
    assert day3_stats.spec_stats.done_count == 0
    assert day3_stats.dev_stats.work_in_progress_count == 0
    assert day3_stats.dev_stats.done_count == 3

    # Story-1: test, and ready for rollout
    # Story-2: test, and ready for rollout
    # Story-3: test, and stay in test
    process.process_day(4)
    day4_stats = process.get_statistics()[-1]
    assert day4_stats.finished_work_count == 0  # No stories finished yet
    assert day4_stats.dev_stats.work_in_progress_count == 0
    assert day4_stats.dev_stats.done_count == 0
    assert day4_stats.test_stats.work_in_progress_count == 1
    assert day4_stats.test_stats.done_count == 2

    # Story-1: rollout, and completed
    # Story-2: capa-waiting for rollout
    # Story-3: test, and ready for rollout
    process.process_day(5)
    day5_stats = process.get_statistics()[-1]
    assert day5_stats.finished_work_count == 0  # No stories finished yet
    assert day5_stats.test_stats.work_in_progress_count == 0
    assert day5_stats.test_stats.done_count == 1
    assert day5_stats.rollout_stats.input_queue_count == 1
    assert day5_stats.rollout_stats.work_in_progress_count == 0
    assert day5_stats.rollout_stats.done_count == 1

    # Story-1: moved to finished
    # Story-2: rollout, and completed
    # Story-3: capa-wating for rollout
    process.process_day(5)
    day5_stats = process.get_statistics()[-1]
    assert day5_stats.finished_work_count == 1  # Story1 finished
    assert day5_stats.test_stats.work_in_progress_count == 0
    assert day5_stats.test_stats.done_count == 0
    assert day5_stats.rollout_stats.input_queue_count == 1
    assert day5_stats.rollout_stats.work_in_progress_count == 0
    assert day5_stats.rollout_stats.done_count == 1

    # Story-2: moved to finished
    # Story-3: rollout and completed
    process.process_day(6)
    day6_stats = process.get_statistics()[-1]
    assert day6_stats.finished_work_count == 2  # Story1 and Story2 finished
    assert day6_stats.test_stats.work_in_progress_count == 0
    assert day6_stats.test_stats.done_count == 0
    assert day6_stats.rollout_stats.input_queue_count == 0
    assert day6_stats.rollout_stats.work_in_progress_count == 0
    assert day6_stats.rollout_stats.done_count == 1

    # Story-3: moved to finished
    process.process_day(7)
    day7_stats = process.get_statistics()[-1]
    assert day7_stats.finished_work_count == 3  # All stories finished
    assert day7_stats.test_stats.work_in_progress_count == 0
    assert day7_stats.test_stats.done_count == 0
    assert day7_stats.rollout_stats.input_queue_count == 0
    assert day7_stats.rollout_stats.work_in_progress_count == 0
    assert day7_stats.rollout_stats.done_count == 0
