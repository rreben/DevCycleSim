
import json
import os
import random
import argparse
from typing import List, Dict, Optional

# Constants for Defect Rates (as proposed/agreed)
# Injection Rates
RATE_SPEC_DEFECT = 0.15
RATE_DEV_DEFECT = 0.25
RATE_TEST_DEFECT = 0.05

# Discovery Latency Distributions
# Spec Defect found in:
SPEC_DEFECT_DISCOVERY = {
    "dev": 0.40,
    "test": 0.40,
    "rollout": 0.20
}

# Dev Defect found in:
DEV_DEFECT_DISCOVERY = {
    "test": 0.80,
    "rollout": 0.20
}

# Test Defect found in: (100% in Rollout)
TEST_DEFECT_DISCOVERY = {
    "rollout": 1.00
}

def get_weighted_choice(distribution: Dict[str, float]) -> str:
    phases = list(distribution.keys())
    weights = list(distribution.values())
    return random.choices(phases, weights=weights, k=1)[0]

def generate_story(id: str, feature_id: str, arrival_day: int, size_profile: Dict[str, int]) -> Dict:
    tasks = []
    
    # Create base tasks from size profile
    # Order: spec, dev, test, rollout
    for phase_name in ["spec", "dev", "test", "rollout"]:
        count = size_profile.get(phase_name, 1)
        
        # We need to distribute defects onto specific ONE-DAY tasks within the phase count
        # For simplicity, we'll attach defects to the LAST task of the phase logic-wise
        # or randomly. Let's do random.
        
        phase_tasks = []
        for _ in range(count):
            phase_tasks.append({"phase": phase_name, "count": 1})
            
        tasks.extend(phase_tasks)

    # Inject Defects
    # We modify the 'phase_tasks' in place? No, we modify the `tasks` list.
    # We need to find indices for phases.
    
    spec_indices = [i for i, t in enumerate(tasks) if t["phase"] == "spec"]
    dev_indices = [i for i, t in enumerate(tasks) if t["phase"] == "dev"]
    test_indices = [i for i, t in enumerate(tasks) if t["phase"] == "test"]
    
    # 1. Spec Defects
    if random.random() < RATE_SPEC_DEFECT:
        # Pick a random spec task to carry the defect
        target_idx = random.choice(spec_indices)
        discovery = get_weighted_choice(SPEC_DEFECT_DISCOVERY)
        tasks[target_idx]["defect_discovery_phase"] = discovery

    # 2. Dev Defects
    if random.random() < RATE_DEV_DEFECT:
        target_idx = random.choice(dev_indices)
        discovery = get_weighted_choice(DEV_DEFECT_DISCOVERY)
        # Avoid overwriting if multiple defects hit same task (rare but possible)
        # In this model, 1 task = 1 potential defect trigger.
        # If we overwrite, it just means the "last" defect wins, which is acceptable for simple model
        tasks[target_idx]["defect_discovery_phase"] = discovery

    # 3. Test Defects
    if random.random() < RATE_TEST_DEFECT:
        target_idx = random.choice(test_indices)
        discovery = get_weighted_choice(TEST_DEFECT_DISCOVERY)
        tasks[target_idx]["defect_discovery_phase"] = discovery

    return {
        "id": id,
        "feature_id": feature_id,
        "arrival_day": arrival_day,
        "priority": 1,
        "tasks": tasks
    }

def generate_scenario(
    output_dir: str, 
    filename: str, 
    num_features: int, 
    stories_per_feature: int, 
    size_profile: Dict[str, int]
):
    all_stories = []
    current_day = 1
    
    for f in range(1, num_features + 1):
        feature_id = f"FEATURE-{f}"
        for s in range(1, stories_per_feature + 1):
            story_id = f"{feature_id}-STORY-{s:02d}"
            # Scatter arrival days slightly
            arrival = current_day + random.randint(0, 2)
            
            story = generate_story(story_id, feature_id, arrival, size_profile)
            all_stories.append(story)
            
            # Stagger arrivals slightly (e.g., 1 story every 2 days on average?)
            # Or burst? Let's do batches.
            # Flatten arrival for now: all at 1 for max contention? 
            # Or staggered. Let's start all at 1 to see throughput purely.
            # User example 6 starts all at 1. Let's do that.
            all_stories[-1]["arrival_day"] = 1

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(all_stories, f, indent=2)
    
    print(f"Generated {len(all_stories)} stories in {filepath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    # 1. Example 10: Small Stories (agile micro-tasks)
    # Profile: Spec 1, Dev 2, Test 2, Rollout 1 (Total 6)
    # 60 Stories (3 Features x 20 Stories)
    generate_scenario(
        "examples/example_10_small",
        "small_stories.json",
        num_features=3,
        stories_per_feature=20,
        size_profile={"spec": 1, "dev": 2, "test": 2, "rollout": 1}
    )
    
    # 2. Example 11: Large Stories (controlled comparison)
    # Profile: Exactly double of Small (Spec 2, Dev 4, Test 4, Rollout 2 = 12 tasks)
    # Total Tasks should be equal to Example 10 (360 tasks)
    # 360 / 12 = 30 Stories. (3 Features x 10 Stories)
    generate_scenario(
        "examples/example_11_large",
        "large_stories.json",
        num_features=3,
        stories_per_feature=10,
        size_profile={"spec": 2, "dev": 4, "test": 4, "rollout": 2}
    )

if __name__ == "__main__":
    main()
