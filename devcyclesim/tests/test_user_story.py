import pytest
from src.machines.user_story import UserStory


def test_user_story_basic_creation():
    """Test die Erstellung einer UserStory mit Standardwerten"""
    story = UserStory("STORY-1", arrival_day=1)
    assert story.story_id == "STORY-1"
    assert story.arrival_day == 1
    assert story.priority == 1  # Standardpriorität
    assert story.size_factor == 1.0  # Standard-Größenfaktor
    # Prüfe die Standard-Phasendauern
    assert story.phase_durations == {
        "spec": 2,
        "dev": 5,
        "test": 3,
        "rollout": 1
    }


def test_user_story_with_custom_size():
    """Test die Erstellung einer UserStory mit angepasster Größe"""
    story = UserStory("STORY-2", arrival_day=2, size_factor=2.0)
    assert story.size_factor == 2.0


def test_user_story_with_custom_priority():
    """Test die Erstellung einer UserStory mit angepasster Priorität"""
    story = UserStory("STORY-3", arrival_day=1, priority=3)
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
    """Test, dass negative Prioritäten nicht erlaubt sind"""
    with pytest.raises(ValueError, match="Priorität muss positiv sein"):
        UserStory("STORY-5", arrival_day=1, priority=-1)


def test_user_story_invalid_arrival_day():
    """Test, dass negative Ankunftstage nicht erlaubt sind"""
    with pytest.raises(ValueError, match="Ankunftstag muss positiv sein"):
        UserStory("STORY-6", arrival_day=-1)


def test_user_story_invalid_size_factor():
    """Test, dass negative oder Null-Größenfaktoren nicht erlaubt sind"""
    with pytest.raises(ValueError, match="Größenfaktor muss positiv sein"):
        UserStory("STORY-7", arrival_day=1, size_factor=-0.5)
    with pytest.raises(ValueError, match="Größenfaktor muss positiv sein"):
        UserStory("STORY-8", arrival_day=1, size_factor=0)


def test_user_story_invalid_phase_durations():
    """Test, dass Phasendauern vollständig und positiv sein müssen"""
    invalid_durations = {
        "spec": 1,
        "dev": -1,  # Negative Dauer
        "test": 4
        # Fehlende 'rollout' Phase
    }
    with pytest.raises(
            ValueError, match="Alle Phasendauern müssen positiv sein"):
        UserStory("STORY-9", arrival_day=1, phase_durations=invalid_durations)


def test_user_story_required_parameters():
    """Test, dass erforderliche Parameter nicht fehlen dürfen"""
    with pytest.raises(TypeError):
        UserStory()  # Keine Parameter
    with pytest.raises(TypeError):
        UserStory(story_id="STORY-10")  # Fehlender arrival_day


def test_user_story_missing_phases():
    """Test, dass alle Phasen definiert sein müssen"""
    incomplete_durations = {
        "spec": 1,
        "dev": 2,
        "test": 4
        # Fehlende 'rollout' Phase
    }
    with pytest.raises(
        ValueError,
        match="Alle Phasen müssen definiert sein"
    ):
        UserStory(
            "STORY-9",
            arrival_day=1,
            phase_durations=incomplete_durations
        )


def test_user_story_negative_durations():
    """Test, dass keine negativen Phasendauern erlaubt sind"""
    negative_durations = {
        "spec": 1,
        "dev": -1,  # Negative Dauer
        "test": 4,
        "rollout": 1
    }
    with pytest.raises(
        ValueError,
        match="Alle Phasendauern müssen positiv sein"
    ):
        UserStory(
            "STORY-10",
            arrival_day=1,
            phase_durations=negative_durations
        )
