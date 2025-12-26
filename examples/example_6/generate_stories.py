import json
import os

stories = []
for feature_id in range(1, 4):
    for story_id in range(1, 21):
        stories.append({
            "id": f"FEATURE-{feature_id}-STORY-{story_id:02d}",
            "spec": 2,
            "dev": 3,
            "test": 3,
            "rollout": 1,
            "arrival_day": 1,
            "priority": 1
        })

output_file = os.path.join(os.path.dirname(__file__), "three_features.json")
with open(output_file, "w") as f:
    json.dump(stories, f, indent=2)

print(f"Generated {len(stories)} stories in {output_file}")
