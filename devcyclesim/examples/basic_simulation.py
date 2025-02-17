"""
Example scenarios for the development process simulation.
Shows different resource allocation strategies and their outcomes.

Example scenarios for the development process simulation.
Shows different resource allocation strategies and their outcomes.

Example scenarios for the development process simulation.
Shows different resource allocation strategies and their outcomes.
"""

from devcyclesim.src.simulation_controller import SimulationController
from devcyclesim.src.simulation_controller import ResourcePlan


def run_specification_first_strategy():
    """
    Demonstrates a strategy where the team focuses heavily on specification
    in the beginning, then shifts to development and testing.

    Team size: 8 people
    Duration: 30 days
    Strategy:
    - Days 1-10: Heavy specification focus
    - Days 11-20: Development focus
    - Days 21-30: Testing and rollout focus
    """
    simulation = SimulationController(
        total_team_size=8,
        simulation_duration=30)

    # Initial phase: Focus on specification
    simulation.add_resource_plan(ResourcePlan(
        start_day=0,
        end_day=10,
        specification_capacity=6,  # Most people specifying
        development_capacity=2,    # Small dev team starts
        testing_capacity=0,
        rollout_capacity=0
    ))

    # Middle phase: Development focus
    simulation.add_resource_plan(ResourcePlan(
        start_day=11,
        end_day=20,
        specification_capacity=2,  # Reduced spec team
        development_capacity=4,    # Main development phase
        testing_capacity=2,        # Start testing
        rollout_capacity=0
    ))

    # Final phase: Testing and rollout
    simulation.add_resource_plan(ResourcePlan(
        start_day=21,
        end_day=30,
        specification_capacity=0,  # Specification complete
        development_capacity=2,    # Finishing development
        testing_capacity=4,        # Heavy testing
        rollout_capacity=2        # Start rollout
    ))

    simulation.run_simulation()
    return simulation.get_statistics()


def run_balanced_strategy():
    """
    Demonstrates a more balanced approach where resources are distributed
    more evenly across all phases.

    Team size: 8 people
    Duration: 30 days
    Strategy: Maintain relatively stable allocation throughout
    """
    simulation = SimulationController(
        total_team_size=8,
        simulation_duration=30
    )

    # Consistent balanced allocation
    simulation.add_resource_plan(ResourcePlan(
        start_day=0,
        end_day=30,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=2,
        rollout_capacity=1
    ))

    simulation.run_simulation()
    return simulation.get_statistics()


def compare_strategies():
    """Compare different resource allocation strategies."""
    print("Comparing different resource allocation strategies:\n")
    print("Strategy 1: Specification First")
    print("-" * 40)
    spec_first_results = run_specification_first_strategy()
    for metric, value in spec_first_results.items():
        print(f"{metric}: {value}")

    print("\nStrategy 2: Balanced Approach")
    print("-" * 40)
    balanced_results = run_balanced_strategy()
    for metric, value in balanced_results.items():
        print(f"{metric}: {value}")


if __name__ == "__main__":
    compare_strategies()
