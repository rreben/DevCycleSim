
import json
import os

def generate_stories():
    stories = []
    
    # Configuration based on example_6
    num_features = 5
    stories_per_feature = 20
    arrival_day = 1
    priority = 1
    
    # Task efforts from example_6
    task_structure = [
        {"phase": "spec", "count": 2},
        {"phase": "dev", "count": 3},
        {"phase": "test", "count": 3},
        {"phase": "rollout", "count": 1}
    ]
    
    for feature_num in range(1, num_features + 1):
        feature_id = f"FEATURE-{feature_num}"
        
        for story_num in range(1, stories_per_feature + 1):
            story_id = f"{feature_id}-STORY-{story_num:02d}"
            
            story = {
                "id": story_id,
                "tasks": task_structure,
                "arrival_day": arrival_day,
                "priority": priority,
                "feature_id": feature_id
            }
            stories.append(story)
            
    return stories

def main():
    output_dir = "examples/example_8"
    output_file = os.path.join(output_dir, "five_features.json")
    
    # Ensure directory exists (redundant if mkdir already run, but safe)
    os.makedirs(output_dir, exist_ok=True)
    
    data = generate_stories()
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Generated {len(data)} stories in {output_file}")

if __name__ == "__main__":
    main()
