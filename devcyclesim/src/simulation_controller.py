from dataclasses import dataclass, field
from typing import Dict, List
from .machines.base import Machine
from .user_story import UserStory


@dataclass
class ResourcePlan:
    """Defines resource allocation for a specific time period."""

    start_day: int
    end_day: int
    specification_capacity: int
    development_capacity: int
    testing_capacity: int
    rollout_capacity: int

    def __post_init__(self):
        """Validate the resource plan after initialization."""
        if (self.specification_capacity < 0 or self.development_capacity < 0 or
                self.testing_capacity < 0 or self.rollout_capacity < 0):
            raise ValueError("Capacities cannot be negative")
        
        if self.start_day >= self.end_day:
            raise ValueError("Start day must be before end day")


@dataclass
class SimulationController:
    """Main controller for the development process simulation."""

    total_team_size: int
    simulation_duration: int
    resource_plans: List[ResourcePlan] = field(default_factory=list)

    # Machines for different phases
    specification: Machine = field(init=False)
    development: Machine = field(init=False)
    testing: Machine = field(init=False)
    rollout: Machine = field(init=False)

    # Statistics
    completed_stories: List[UserStory] = field(default_factory=list)
    current_day: int = 0

    def __post_init__(self):
        """Initialize machines with initial capacities."""
        self.specification = Machine("Specification", 0)
        self.development = Machine("Development", 0)
        self.testing = Machine("Testing", 0)
        self.rollout = Machine("Rollout", 0)

    def add_resource_plan(self, plan: ResourcePlan) -> None:
        """Add a new resource plan."""
        if (
            plan.specification_capacity
            + plan.development_capacity
            + plan.testing_capacity
            + plan.rollout_capacity
            > self.total_team_size
        ):
            raise ValueError("Total capacity exceeds team size!")
        self.resource_plans.append(plan)

    def _update_capacities(self) -> None:
        """Update machine capacities based on current day."""
        for plan in self.resource_plans:
            if plan.start_day <= self.current_day <= plan.end_day:
                self.specification.capacity = plan.specification_capacity
                self.development.capacity = plan.development_capacity
                self.testing.capacity = plan.testing_capacity
                self.rollout.capacity = plan.rollout_capacity

    def generate_story(self) -> UserStory:
        """Generate a new UserStory with random properties."""
        # Generiere eine neue UserStory mit zufälligen Eigenschaften
        import uuid
        import random

        story = UserStory(
            story_id=str(uuid.uuid4()),
            phase_durations={
                "specification": random.randint(1, 5),
                "development": random.randint(1, 5),
                "testing": random.randint(1, 5),
                "rollout": random.randint(1, 5)
            }
        )
        return story

    def execute_tick(self) -> None:
        """Execute one simulation tick."""
        self._update_capacities()
        # Process development errors first
        error_stories = self.development.get_stories_with_errors()
        for story in error_stories:
            if story.errors.has_spec_revision_needed:
                self.specification.enqueue(story)

        # Normal processing
        completed_specs = self.specification.process_takt()
        for story in completed_specs:
            self.development.enqueue(story)

        completed_dev = self.development.process_takt()
        for story in completed_dev:
            self.testing.enqueue(story)

        completed_tests = self.testing.process_takt()
        for story in completed_tests:
            self.rollout.enqueue(story)

        completed_rollouts = self.rollout.process_takt()
        self.completed_stories.extend(completed_rollouts)

        self.current_day += 1

    def run_simulation(self) -> None:
        """Run the complete simulation."""
        while self.current_day < self.simulation_duration:
            self.execute_tick()

    def get_statistics(self) -> Dict:
        """Return simulation statistics."""
        return {
            "Completed Stories": len(self.completed_stories),
            "Stories in Specification": (
                self.specification.get_queue_length()
                + self.specification.get_active_count()
            ),
            "Stories in Development": (
                self.development.get_queue_length()
                + self.development.get_active_count()
            ),
            "Stories in Testing": (
                self.testing.get_queue_length()
                + self.testing.get_active_count()
            ),
            "Stories in Rollout": (
                self.rollout.get_queue_length()
                + self.rollout.get_active_count()
            ),
        }

    @classmethod
    def create_with_default_plan(
        cls,
        team_size: int = 8,
        simulation_duration: int = 100
    ) -> "SimulationController":
        """
        Erstellt einen SimulationController mit Standardressourcenverteilung
        basierend auf dem klassischen Wasserfallmodell.

        Args:
            team_size: Größe des Entwicklungsteams (Standard: 8)
            simulation_duration: Dauer der Simulation in Tagen (Standard: 100)
        """
        controller = cls(
            total_team_size=team_size,
            simulation_duration=simulation_duration
        )

        # Standardressourcenplan für das gesamte Projekt
        default_plan = ResourcePlan(
            start_day=0,
            end_day=simulation_duration,
            specification_capacity=2,  # 25% von 8
            development_capacity=3,    # 40% von 8
            testing_capacity=2,        # 25% von 8
            rollout_capacity=1         # 10% von 8
        )

        controller.add_resource_plan(default_plan)
        return controller
