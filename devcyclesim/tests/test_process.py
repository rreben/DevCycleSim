from numpy import array
from devcyclesim.src.process import Process, ResourcePlan
from devcyclesim.src.user_story import UserStory, Phase, Task


def test_process_sunny_path():
    """
    Tests the collection and evaluation of process statistics.
    Creates a process with 3 user stories and runs it for 5 days.
    Verifies the state after each simulation day.
    """
    # Create process with 5 simulation days
    process = Process(simulation_days=7)

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
    assert day1_stats.spec_stats.capacity == 2
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


def test_process_with_drop_in_dev_capacity_path():
    """
    Tests the collection and evaluation of process statistics
    with a capacity drop in the DEV phase.
    """
    # Create process with 7 simulation days
    process = Process(simulation_days=7)

    # Create three stories with different phase durations
    story1 = UserStory.from_phase_durations(
        "STORY-1",
        phase_durations={
            Phase.SPEC: 1,
            Phase.DEV: 3,
            Phase.TEST: 2,
            Phase.ROLLOUT: 1
        }
    )

    story2 = UserStory.from_phase_durations(
        "STORY-2",
        phase_durations={
            Phase.SPEC: 2,
            Phase.DEV: 3,
            Phase.TEST: 3,
            Phase.ROLLOUT: 1
        }
    )

    story3 = UserStory.from_phase_durations(
        "STORY-3",
        phase_durations={
            Phase.SPEC: 1,
            Phase.DEV: 2,
            Phase.TEST: 2,
            Phase.ROLLOUT: 1
        }
    )

    # Add stories to process
    process.add(story1)
    process.add(story2)
    process.add(story3)

    # Define resource plans for different capacity phases
    # Normal capacity for days 1-3
    normal_capacity = ResourcePlan(
        start_day=1,
        end_day=3,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=3,
        rollout_capacity=1
    )

    # Reduced capacity for days 4-5
    reduced_capacity = ResourcePlan(
        start_day=4,
        end_day=5,
        specification_capacity=2,
        development_capacity=1,
        testing_capacity=3,
        rollout_capacity=1
    )

    # No dev capacity for day 6
    no_dev_capacity = ResourcePlan(
        start_day=6,
        end_day=6,
        specification_capacity=2,
        development_capacity=0,
        testing_capacity=3,
        rollout_capacity=1
    )

    # Back to normal capacity for day 7
    final_capacity = ResourcePlan(
        start_day=7,
        end_day=7,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=3,
        rollout_capacity=1
    )

    # Add resource plans to process
    process.add_resource_plan(normal_capacity)
    process.add_resource_plan(reduced_capacity)
    process.add_resource_plan(no_dev_capacity)
    process.add_resource_plan(final_capacity)

    # Array für die Statistiken
    daily_stats = []

    # day 1
    # Story-1: Spec 1/1, ready for dev
    # Story-2: Spec 1/2, not ready
    # Story-3: wait in Backlog
    process.process_day(1)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 1
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 1
    assert stats.spec_stats.done_count == 1
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 2
    # Story-1: Dev 1/3, not ready
    # Story-2: Spec 2/2, ready for dev
    # Story-3: Spec 1/1, redy for dev
    process.process_day(2)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 2
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 1
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 3
    # Story-1: Dev 2/3, not ready
    # Story-2: Dev 1/3, not ready
    # Story-3: Dev 1/2, not ready
    process.process_day(3)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 3
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 4
    # Now we reduce the capacity in development to 1
    # Story-1: Dev 3/3, ready for test
    # Story-2: capa-wating dev still 1/3
    # Story-3: capa-waitng dev still 1/2
    process.process_day(4)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 1  # Using ResourcePlan
    assert stats.dev_stats.input_queue_count == 2
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 1
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 5
    # Still reduced capacity in development
    # Story-1: Test 1/2
    # Story-2: Dev 2/3
    # Story-3: capa-waitng dev still 1/2
    process.process_day(5)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 1  # Using ResourcePlan
    assert stats.dev_stats.input_queue_count == 1
    assert stats.dev_stats.work_in_progress_count == 1
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 1
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 6
    # capacity reduced to zero. So dev stops
    # Story-1: Test 2/2 ready for rollout
    # Story-2: capa-wating Dev still 2/3
    # Story-3: capa-waitng dev still 1/2
    process.process_day(6)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 0  # Using ResourcePlan
    assert stats.dev_stats.input_queue_count == 2
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 1
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 7
    # dev capacity back to 3 againg
    # Story-1: Rollout 1/1 ready for rollout
    # Story-2: Dev 3/3 ready for test
    # Story-3: Dev 2/2 ready for test
    process.process_day(7)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3  # Using ResourcePlan
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 2
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 1
    assert stats.finished_work_count == 0


def test_process_with_errors_in_user_story():
    """
    Tests the collection and evaluation of process statistics
    with a capacity drop in the DEV phase.
    """
    # Create process with 7 simulation days
    process = Process(simulation_days=12)

    # Create three stories with different phase durations
    story1 = UserStory.from_phase_durations(
        "STORY-1",
        phase_durations={
            Phase.SPEC: 1,
            Phase.DEV: 4,
            Phase.TEST: 3,
            Phase.ROLLOUT: 1},
    )

    tasks = array(
        [
            Task(Phase.SPEC),
            Task(Phase.DEV),
            Task(Phase.DEV),
            Task(Phase.SPEC),  # Rework in specification
            Task(Phase.DEV),  # Remaining development
            Task(Phase.DEV),
            Task(Phase.TEST),
            Task(Phase.DEV),  # Rework in Dev
            Task(Phase.TEST),
            Task(Phase.ROLLOUT),
        ],
        dtype=object,
    )

    story2 = UserStory("STORY-2", tasks=tasks)

    story3 = UserStory.from_phase_durations(
        "STORY-3",
        phase_durations={
            Phase.SPEC: 1,
            Phase.DEV: 4,
            Phase.TEST: 3,
            Phase.ROLLOUT: 1},
    )

    # Add stories to process
    process.add(story1)
    process.add(story2)
    process.add(story3)

    # Array für die Statistiken
    daily_stats = []

    # day 0
    # Story-1: Spec 0/1, Dev 0/4, Test 0/3, RO 0/1
    # Story-2: Spec_1 0/1, Dev_1 0/2, Spec_2 0/1,
    #          Dev_2 0/2, Test_1 0/1, Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: Spec 0/1, Dev 0/4, Test 0/3, RO 0/1

    # day 1
    # Story-1: Spec 1/1, ready for Dev 0/4, Test 0/3, RO 0/1
    # Story-2: Spec_1 1/1, ready dev Dev_1 0/2, Spec_2 0/1,
    #          Dev_2 0/2, Test_1 0/1, Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: watitng in backlog Spec 0/1, Dev 0/4, Test 0/3, RO 0/1
    process.process_day(1)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 1
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 2
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 2
    # Story-1: Dev 1/4, Test 0/3, RO 0/1
    # Story-2: Dev_1 1/2, Spec_2 0/1,
    #          Dev_2 0/2, Test_1 0/1, Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: Spec 1/1, ready for Dev 0/4, Test 0/3, RO 0/1
    process.process_day(2)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 1
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 2
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 3
    # Story-1: Dev 2/4, Test 0/3, RO 0/1
    # Story-2: Dev_1 2/2, ready for Spec_2 0/1,
    #          Dev_2 0/2, Test_1 0/1, Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: Dev 1/4, Test 0/3, RO 0/1
    process.process_day(3)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 2
    assert stats.dev_stats.done_count == 1
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 4
    # Story-1: Dev 3/4, Test 0/3, RO 0/1
    # Story-2: Spec_2 1/1, ready
    #          Dev_2 0/2, Test_1 0/1, Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: Dev 2/4, Test 0/3, RO 0/1
    process.process_day(4)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 1
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 2
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 5
    # Story-1: Dev 4/4, ready for Test 0/3, RO 0/1
    # Story-2: Dev_2 1/2, Test_1 0/1, Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: Dev 3/4, Test 0/3, RO 0/1
    process.process_day(5)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 2
    assert stats.dev_stats.done_count == 1
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 6
    # Story-1: Test 1/3, RO 0/1
    # Story-2: Dev_2 2/2,
    #          reday for Test_1 0/1, Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: Dev 4/4, ready for Test 0/3, RO 0/1
    process.process_day(6)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 2
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 1
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 7
    # Story-1: Test 2/3, RO 0/1
    # Story-2: Test_1 1/1, ready for Dev_3 0/1 Test_2 0/1, Rollout 0/1
    # Story-3: Test 1/3, RO 0/1
    process.process_day(7)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 2
    assert stats.test_stats.done_count == 1
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 8
    # Story-1: Test 3/3, ready for RO 0/1
    # Story-2: Dev_3 1/1 ready for Test_2 0/1, Rollout 0/1
    # Story-3: Test 2/3, RO 0/1
    process.process_day(8)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 1
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 1
    assert stats.test_stats.done_count == 1
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 0

    # day 9
    # Story-1: RO 1/1 complete
    # Story-2: Test_2 1/1 ready fro Rollout 0/1
    # Story-3: Test 3/3, ready for  RO 0/1
    process.process_day(9)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 2
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 1
    assert stats.finished_work_count == 0

    # day 10
    # Story-1: finished
    # Story-2: Rollout 1/1 completed
    # Story-3: cap wating RO 0/1
    process.process_day(10)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 1
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 1
    assert stats.finished_work_count == 1

    # day 11
    # Story-1: finished
    # Story-2: finshed
    # Story-3: RO 1/1 completed
    process.process_day(11)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 1
    assert stats.finished_work_count == 2

    # day 12
    # Story-1: finished
    # Story-2: finshed
    # Story-3: finished
    process.process_day(12)
    stats = process.get_statistics()[-1]
    daily_stats.append(stats)
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 3


def test_process_with_automation():
    """
    Tests the collection and evaluation of process statistics
    with a capacity drop in the DEV phase.
    """
    # Create process with 7 simulation days
    process = Process(simulation_days=12)

    # Create three stories with different phase durations
    story1 = UserStory.from_phase_durations(
        "STORY-1",
        phase_durations={
            Phase.SPEC: 1, Phase.DEV: 4, Phase.TEST: 3, Phase.ROLLOUT: 1},
    )

    tasks = array(
        [
            Task(Phase.SPEC),
            Task(Phase.DEV),
            Task(Phase.DEV),
            Task(Phase.SPEC),  # Rework in specification
            Task(Phase.DEV),  # Remaining development
            Task(Phase.DEV),
            Task(Phase.TEST),
            Task(Phase.DEV),  # Rework in Dev
            Task(Phase.TEST),
            Task(Phase.ROLLOUT),
        ],
        dtype=object,
    )

    story2 = UserStory("STORY-2", tasks=tasks)

    story3 = UserStory.from_phase_durations(
        "STORY-3",
        phase_durations={
            Phase.SPEC: 1, Phase.DEV: 4, Phase.TEST: 3, Phase.ROLLOUT: 1},
    )

    # Add stories to process
    process.add(story1)
    process.add(story2)
    process.add(story3)

    process.start()

    stats = process.get_statistics()[-1]
    assert stats.backlog_count == 0
    assert stats.spec_stats.capacity == 2
    assert stats.spec_stats.input_queue_count == 0
    assert stats.spec_stats.work_in_progress_count == 0
    assert stats.spec_stats.done_count == 0
    assert stats.dev_stats.capacity == 3
    assert stats.dev_stats.input_queue_count == 0
    assert stats.dev_stats.work_in_progress_count == 0
    assert stats.dev_stats.done_count == 0
    assert stats.test_stats.capacity == 3
    assert stats.test_stats.input_queue_count == 0
    assert stats.test_stats.work_in_progress_count == 0
    assert stats.test_stats.done_count == 0
    assert stats.rollout_stats.capacity == 1
    assert stats.rollout_stats.input_queue_count == 0
    assert stats.rollout_stats.work_in_progress_count == 0
    assert stats.rollout_stats.done_count == 0
    assert stats.finished_work_count == 3


def test_resource_plan_validation():
    """
    Tests the validation of overlapping resource plans.
    Verifies that overlapping plans are rejected.
    """
    process = Process(simulation_days=10)

    # Base plan for days 3-5
    base_plan = ResourcePlan(
        start_day=3,
        end_day=5,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=3,
        rollout_capacity=1
    )
    process.add_resource_plan(base_plan)

    # Test 1: Plan starting within base plan
    overlapping_start = ResourcePlan(
        start_day=4,
        end_day=6,
        specification_capacity=1,
        development_capacity=2,
        testing_capacity=2,
        rollout_capacity=1
    )
    try:
        process.add_resource_plan(overlapping_start)
        assert False, "Should raise ValueError for overlapping start"
    except ValueError as e:
        assert "overlaps with existing plan" in str(e)

    # Test 2: Plan ending within base plan
    overlapping_end = ResourcePlan(
        start_day=2,
        end_day=4,
        specification_capacity=1,
        development_capacity=2,
        testing_capacity=2,
        rollout_capacity=1
    )
    try:
        process.add_resource_plan(overlapping_end)
        assert False, "Should raise ValueError for overlapping end"
    except ValueError as e:
        assert "overlaps with existing plan" in str(e)

    # Test 3: Plan completely containing base plan
    containing_plan = ResourcePlan(
        start_day=2,
        end_day=6,
        specification_capacity=1,
        development_capacity=2,
        testing_capacity=2,
        rollout_capacity=1
    )
    try:
        process.add_resource_plan(containing_plan)
        assert False, "Should raise ValueError for containing plan"
    except ValueError as e:
        assert "overlaps with existing plan" in str(e)

    # Test 4: Non-overlapping plan should be accepted
    valid_plan = ResourcePlan(
        start_day=6,
        end_day=8,
        specification_capacity=1,
        development_capacity=2,
        testing_capacity=2,
        rollout_capacity=1
    )
    try:
        process.add_resource_plan(valid_plan)
    except ValueError:
        assert False, "Should accept non-overlapping plan"

    # Verify that both valid plans are in the list
    assert len(process.resource_plans) == 2
    assert process.resource_plans[0] == base_plan
    assert process.resource_plans[1] == valid_plan
