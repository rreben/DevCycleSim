import pytest
from devcyclesim.src.user_story import UserStory


def test_user_story_basic_creation():
    """Test creating a UserStory with default values"""
    story = UserStory(
        "STORY-1",
        arrival_day=1,
        priority=1,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        }
    )
    assert story.story_id == "STORY-1"
    assert story.arrival_day == 1
    assert story.priority == 1  # default priority
    assert story.size_factor == 1.0  # default size factor
    # Check default phase durations
    assert story.phase_durations == {
        "spec": 2,
        "dev": 5,
        "test": 3,
        "rollout": 1
    }


def test_user_story_with_custom_size():
    """Test die Erstellung einer UserStory mit angepasster Größe"""
    story = UserStory(
        "STORY-2",
        arrival_day=2,
        size_factor=2.0,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        }
    )
    assert story.size_factor == 2.0


def test_user_story_with_custom_priority():
    """Test die Erstellung einer UserStory mit angepasster Priorität"""
    story = UserStory(
        "STORY-3",
        arrival_day=1,
        priority=3,
        phase_durations={
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        }
    )
    assert story.priority == 3


def test_user_story_with_phase_durations():
    """Test die Erstellung einer UserStory mit spezifischen Phasendauern"""
    custom_durations = {
        "spec": 1,
        "dev": 8,
        "test": 4,
        "rollout": 2
    }
    story = UserStory(
        "STORY-4",
        arrival_day=1,
        phase_durations=custom_durations
    )
    assert story.phase_durations == custom_durations


def test_user_story_invalid_priority():
    """Test that negative priorities are not allowed"""
    with pytest.raises(ValueError, match="Priority must be positive"):
        UserStory(
            "STORY-5",
            arrival_day=1,
            priority=-1,
            phase_durations={
                "spec": 2,
                "dev": 5,
                "test": 3,
                "rollout": 1
            }
        )


def test_user_story_invalid_arrival_day():
    """Test that negative arrival days are not allowed"""
    with pytest.raises(ValueError, match="Arrival day must be positive"):
        UserStory(
            "STORY-6",
            arrival_day=-1,
            phase_durations={
                "spec": 2,
                "dev": 5,
                "test": 3,
                "rollout": 1
            }
        )


def test_user_story_invalid_size_factor():
    """Test that negative or zero size factors are not allowed"""
    with pytest.raises(ValueError, match="Size factor must be positive"):
        UserStory(
            "STORY-7",
            arrival_day=1,
            size_factor=-0.5,
            phase_durations={
                "spec": 2,
                "dev": 5,
                "test": 3,
                "rollout": 1
            }
        )
    with pytest.raises(ValueError, match="Size factor must be positive"):
        UserStory(
            "STORY-8",
            arrival_day=1,
            size_factor=0,
            phase_durations={
                "spec": 2,
                "dev": 5,
                "test": 3,
                "rollout": 1
            }
        )


def test_user_story_invalid_phase_durations():
    """Test that phase durations must be complete and positive"""
    invalid_durations = {
        "spec": 1,
        "dev": -1,  # Negative duration
        "test": 4
        # Missing 'rollout' phase
    }
    with pytest.raises(
            ValueError, match="All phase durations must be positive"):
        UserStory("STORY-9", arrival_day=1, phase_durations=invalid_durations)


def test_user_story_required_parameters():
    """Test, dass erforderliche Parameter nicht fehlen dürfen"""
    with pytest.raises(TypeError):
        # Keine Parameter angeben
        UserStory(  # type: ignore
            story_id="STORY-10"  # Fehlende phase_durations
        )
    with pytest.raises(TypeError):
        # Nur story_id angeben
        UserStory(  # type: ignore
            phase_durations={  # Fehlender story_id
                "spec": 2,
                "dev": 5,
                "test": 3,
                "rollout": 1
            }
        )


def test_user_story_missing_phases():
    """Test that all phases must be defined"""
    incomplete_durations = {
        "spec": 1,
        "dev": 2,
        "test": 4
        # Missing 'rollout' phase
    }
    with pytest.raises(
        ValueError,
        match="All phases must be defined"
    ):
        UserStory(
            "STORY-9",
            arrival_day=1,
            phase_durations=incomplete_durations
        )


def test_user_story_negative_durations():
    """Test that negative phase durations are not allowed"""
    negative_durations = {
        "spec": 1,
        "dev": -1,  # Negative duration
        "test": 4,
        "rollout": 1
    }
    with pytest.raises(
        ValueError,
        match="All phase durations must be positive"
    ):
        UserStory(
            "STORY-10",
            arrival_day=1,
            phase_durations=negative_durations
        )
