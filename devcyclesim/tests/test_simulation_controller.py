import pytest
from devcyclesim.src.simulation_controller import (
    SimulationController, ResourcePlan)


def test_resource_plan_validation():
    """Tests for resource plan validation."""
    # Arrange
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)

    # Test 1: Gesamtkapazität übersteigt Team-Größe
    with pytest.raises(ValueError, match="Total capacity exceeds team size!"):
        invalid_plan = ResourcePlan(
            start_day=0,
            end_day=10,
            specification_capacity=3,
            development_capacity=3,
            testing_capacity=3,
            rollout_capacity=3  # Summe = 12 > team_size (8)
        )
        controller.add_resource_plan(invalid_plan)

    # Test 2: Negative Kapazitäten
    with pytest.raises(ValueError, match="Capacities cannot be negative"):
        invalid_plan = ResourcePlan(
            start_day=0,
            end_day=10,
            specification_capacity=-1,
            development_capacity=2,
            testing_capacity=2,
            rollout_capacity=1
        )
        controller.add_resource_plan(invalid_plan)

    # Test 3: Start-Tag nach End-Tag
    with pytest.raises(ValueError, match="Start day must be before end day"):
        invalid_plan = ResourcePlan(
            start_day=10,
            end_day=5,
            specification_capacity=2,
            development_capacity=2,
            testing_capacity=2,
            rollout_capacity=1
        )
        controller.add_resource_plan(invalid_plan)
