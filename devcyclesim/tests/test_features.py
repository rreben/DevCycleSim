import pytest
from devcyclesim.src.user_story import UserStory, Phase
from devcyclesim.src.process import Process
from devcyclesim.src.process_statistic import ProcessStatistic

def test_user_story_feature_id():
    """Test that UserStory stores feature_id correctly"""
    # Test default
    story = UserStory.from_phase_durations(
        story_id="S1",
        phase_durations={Phase.SPEC: 1}
    )
    assert story.feature_id == "default_feature"

    # Test custom feature_id
    story_custom = UserStory.from_phase_durations(
        story_id="S2",
        phase_durations={Phase.SPEC: 1},
        feature_id="Feature-A"
    )
    assert story_custom.feature_id == "Feature-A"

def test_process_feature_statistics():
    """Test that Process collects statistics by feature"""
    process = Process(simulation_days=5)
    
    # Add stories for Feature A
    story_a1 = UserStory.from_phase_durations(
        story_id="A1",
        phase_durations={Phase.SPEC: 1},
        feature_id="Feature-A"
    )
    process.add(story_a1)
    
    # Add stories for Feature B
    story_b1 = UserStory.from_phase_durations(
        story_id="B1",
        phase_durations={Phase.SPEC: 1},
        feature_id="Feature-B"
    )
    process.add(story_b1)
    
    # Run one day
    process.process_day(1)
    
    # Check statistics
    stats = process.get_statistics()[-1]
    
    assert "Feature-A" in stats.feature_stats
    assert "Feature-B" in stats.feature_stats
    
    # Initially both should be in WIP or Backlog depending on capacity
    # With default capacity (2 SPEC), both should be picked up (WIP)
    assert stats.feature_stats["Feature-A"]["wip"] == 1
    assert stats.feature_stats["Feature-B"]["wip"] == 1
