import numpy as np
from devcyclesim.src.user_story import UserStory, Phase, Task


def test_user_story_from_flexible_task_list():
    """
    Testet das Einlesen einer User Story
    mit beliebiger Task-Reihenfolge aus JSON.
    """
    # Beispiel für das neue JSON-Format
    story_data = {
        "id": "STORY-FLEX",
        "tasks": [
            {"phase": "spec", "count": 2},
            {"phase": "dev", "count": 3},
            {"phase": "test", "count": 2},
            {"phase": "dev", "count": 1},
            {"phase": "test", "count": 1},
            {"phase": "rollout", "count": 1},
        ],
        "arrival_day": 1,
        "priority": 1,
    }

    # Manuelles Nachbauen wie im Patch
    task_list = []
    for task_entry in story_data["tasks"]:
        phase = Phase(task_entry["phase"])
        count = task_entry.get("count", 1)
        task_list.extend([Task(phase=phase) for _ in range(count)])
    story = UserStory(
        story_id=story_data["id"],
        tasks=np.array(task_list, dtype=object),
        arrival_day=story_data.get("arrival_day", 1),
        priority=story_data.get("priority", 1),
    )

    # Erwartete Reihenfolge der Phasen
    expected_phases = (
        [Phase.SPEC] * 2
        + [Phase.DEV] * 3
        + [Phase.TEST] * 2
        + [Phase.DEV] * 1
        + [Phase.TEST] * 1
        + [Phase.ROLLOUT] * 1
    )
    actual_phases = [task.phase for task in story.tasks]
    assert actual_phases == expected_phases
    assert story.story_id == "STORY-FLEX"
    assert story.arrival_day == 1
    assert story.priority == 1
    assert len(story.tasks) == 10


def test_user_story_from_phase_durations_compatibility():
    """
    Testet das Einlesen einer User Story im alten Format (abwärtskompatibel).
    """
    # Beispiel für das alte JSON-Format
    story_data = {
        "id": "STORY-OLD",
        "spec": 2,
        "dev": 3,
        "test": 2,
        "rollout": 1,
        "arrival_day": 2,
        "priority": 5,
    }

    # Nachbauen wie im Patch
    phase_durations = {
        Phase.SPEC: story_data.get("spec", 1),
        Phase.DEV: story_data.get("dev", 1),
        Phase.TEST: story_data.get("test", 1),
        Phase.ROLLOUT: story_data.get("rollout", 1),
    }
    story = UserStory.from_phase_durations(
        story_id=story_data["id"],
        phase_durations=phase_durations,
        arrival_day=story_data.get("arrival_day", 1),
        priority=story_data.get("priority", 1),
    )

    # Erwartete Reihenfolge der Phasen
    expected_phases = (
        [Phase.SPEC] * 2 + [Phase.DEV] * 3
        + [Phase.TEST] * 2 + [Phase.ROLLOUT] * 1
    )
    actual_phases = [task.phase for task in story.tasks]
    assert actual_phases == expected_phases
    assert story.story_id == "STORY-OLD"
    assert story.arrival_day == 2
    assert story.priority == 5
    assert len(story.tasks) == 8
