import json
import os

stories = []
for feature_id in range(1, 4):
    # Half as many stories: range(1, 11) -> 10 stories instead of 20
    for story_id in range(1, 11):
        stories.append({
            "id": f"FEATURE-{feature_id}-STORY-{story_id:02d}",
            "tasks": [
                # Double the count for each phase
                {"phase": "spec", "count": 4},   # was 2
                {"phase": "dev", "count": 6},    # was 3
                {"phase": "test", "count": 6},   # was 3
                {"phase": "rollout", "count": 2} # was 1
            ],
            "arrival_day": 1,
            "priority": 1,
            "feature_id": f"FEATURE-{feature_id}"
        })

output_file = os.path.join(os.path.dirname(__file__), "three_features.json")
with open(output_file, "w") as f:
    json.dump(stories, f, indent=2)

print(f"Generated {len(stories)} stories in {output_file}")
