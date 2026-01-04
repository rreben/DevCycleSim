import pytest
from devcyclesim.src.process import Process
from devcyclesim.src.process_step import ReleasePolicy
from devcyclesim.src.user_story import UserStory, Phase

def test_single_phase_batching_spec():
    """
    Test batch release configuration for a single phase (SPEC).
    Scenario:
    - 3 Stories, all belong to the same feature.
    - Spec phase is set to BATCH_FEATURE.
    - Stories should only progress to DEV once ALL 3 are done in SPEC.
    """
    process = Process(simulation_days=10)
    
    # Create 3 stories for Feature A
    # All are short enough to complete quickly in SPEC
    stories = []
    for i in range(3):
        story = UserStory.from_phase_durations(
            f"STORY-{i}",
            phase_durations={
                Phase.SPEC: 1,
                Phase.DEV: 1,
                Phase.TEST: 1,
                Phase.ROLLOUT: 1
            },
            feature_id="FEATURE-A"
        )
        process.add(story)
        stories.append(story)
        
    # Configure SPEC to be Batch Release
    process.set_step_release_policy(Phase.SPEC, ReleasePolicy.BATCH_FEATURE)
    
    # Initialize process (calculates feature counts)
    feature_counts = process._calculate_feature_story_counts()
    process.spec_step.feature_story_counts = feature_counts
    process.dev_step.feature_story_counts = feature_counts
    process.test_step.feature_story_counts = feature_counts
    process.rollout_step.feature_story_counts = feature_counts
    
    # process.start_of_day_processing(1) - REMOVED: This drains backlog and corrupts count calculation if called before.
    # And if called after, it's redundant to process_day(1).
    
    # Default Capacities: Spec=2, Dev=3.
    # Total work = 3 spec days.
    
    # Day 1:
    process.process_day(1)
    stats1 = process.get_statistics()[-1]
    
    assert stats1.spec_stats.done_count == 2
    assert stats1.dev_stats.input_queue_count == 0 
    assert stats1.dev_stats.work_in_progress_count == 0
    
    # Day 2:
    process.process_day(2)
    stats2 = process.get_statistics()[-1]
    
    assert stats2.spec_stats.done_count == 3
    assert stats2.dev_stats.input_queue_count == 0 
    
    # Day 3:
    process.process_day(3)
    stats3 = process.get_statistics()[-1]
    
    # Stories moved from Spec -> Dev Input -> Dev WIP -> Dev Done (Duration 1)
    assert stats3.spec_stats.done_count == 0
    assert stats3.dev_stats.done_count == 3
    assert stats3.dev_stats.work_in_progress_count == 0
    


def test_multi_phase_batching_spec_and_dev():
    """
    Test batch release configuration for multiple phases (SPEC and DEV).
    Scenario:
    - 3 Stories, all Feature A.
    - Spec AND Dev set to BATCH_FEATURE.
    """
    process = Process(simulation_days=10)
    
    stories = []
    for i in range(3):
        story = UserStory.from_phase_durations(
            f"STORY-{i}",
            phase_durations={
                Phase.SPEC: 1,
                Phase.DEV: 1,
                Phase.TEST: 1,
                Phase.ROLLOUT: 1
            },
            feature_id="FEATURE-A"
        )
        process.add(story)
        stories.append(story)
        
    process.set_step_release_policy(Phase.SPEC, ReleasePolicy.BATCH_FEATURE)
    process.set_step_release_policy(Phase.DEV, ReleasePolicy.BATCH_FEATURE)
    
    # Manual init of counts
    feature_counts = process._calculate_feature_story_counts()
    process.spec_step.feature_story_counts = feature_counts
    process.dev_step.feature_story_counts = feature_counts
    process.test_step.feature_story_counts = feature_counts
    process.rollout_step.feature_story_counts = feature_counts


    # Day 1 & 2: Spec work (Same as previous test)
    process.process_day(1)
    process.process_day(2)
    
    # Day 3: Release from Spec to Dev.
    process.process_day(3)
    stats3 = process.get_statistics()[-1]
    
    assert stats3.spec_stats.done_count == 0
    assert stats3.dev_stats.done_count == 3
    
    assert stats3.test_stats.input_queue_count == 0
    assert stats3.test_stats.work_in_progress_count == 0
    
    # Day 4:
    # Start: move_completed triggers for Dev.
    # Dev Pluck checks. 3/3 done. Release ALL to Test.
    # Test Duration 1. Input -> WIP -> Done.
    process.process_day(4)
    stats4 = process.get_statistics()[-1]
    
    assert stats4.dev_stats.done_count == 0
    assert stats4.test_stats.done_count == 3
    assert stats4.test_stats.work_in_progress_count == 0
