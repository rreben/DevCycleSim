import pytest
from devcyclesim.src.simulation_controller import (
    SimulationController, ResourcePlan)
from devcyclesim.src.user_story import UserStory


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


def test_simulation_controller_initialization():
    """
    Tests für die Kontrollerinitialisierung:
    - Korrekte Initialisierung der Maschinen
    - Standardwerte werden korrekt gesetzt
    - create_with_default_plan erstellt valide Konfiguration
    """
    # Test 1: Basis-Initialisierung
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)
    assert controller.total_team_size == 8
    assert controller.simulation_duration == 100
    assert len(controller.resource_plans) == 0

    # Test 2: Default Plan Erstellung
    default_controller = SimulationController.create_with_default_plan(
        team_size=8,
        simulation_duration=100
    )

    assert default_controller.total_team_size == 8
    assert default_controller.simulation_duration == 100
    assert len(default_controller.resource_plans) == 1

    default_plan = default_controller.resource_plans[0]
    assert default_plan.start_day == 0
    assert default_plan.end_day == 100
    assert default_plan.specification_capacity == 2
    assert default_plan.development_capacity == 3
    assert default_plan.testing_capacity == 2
    assert default_plan.rollout_capacity == 1

    # Test 3: Gesamtkapazität entspricht Teamgröße
    total_capacity = (
        default_plan.specification_capacity +
        default_plan.development_capacity +
        default_plan.testing_capacity +
        default_plan.rollout_capacity
    )
    assert total_capacity == default_controller.total_team_size

    # Test 4: Angepasste Teamgröße
    large_controller = SimulationController.create_with_default_plan(
        team_size=16,
        simulation_duration=200
    )
    assert large_controller.total_team_size == 16
    assert large_controller.simulation_duration == 200


def test_capacity_updates():
    """
    Tests für Kapazitätsaktualisierungen:
    - _update_capacities aktualisiert alle Maschinen korrekt
    - Kapazitäten ändern sich an Planübergängen
    - Überlappende Ressourcenpläne werden korrekt gehandhabt
    """
    # Test 1: Einzelner Ressourcenplan
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)
    plan1 = ResourcePlan(
        start_day=0,
        end_day=50,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=2,
        rollout_capacity=1
    )
    controller.add_resource_plan(plan1)

    # Prüfe Kapazitäten während des Plans
    controller.current_day = 25
    controller._update_capacities()
    assert controller.specification.capacity == 2
    assert controller.development.capacity == 3
    assert controller.testing.capacity == 2
    assert controller.rollout.capacity == 1

    # Test 2: Planübergang
    plan2 = ResourcePlan(
        start_day=51,
        end_day=100,
        specification_capacity=1,
        development_capacity=4,
        testing_capacity=2,
        rollout_capacity=1
    )
    controller.add_resource_plan(plan2)

    # Prüfe Kapazitäten vor Übergang
    controller.current_day = 50
    controller._update_capacities()
    assert controller.specification.capacity == 2
    assert controller.development.capacity == 3

    # Prüfe Kapazitäten nach Übergang
    controller.current_day = 51
    controller._update_capacities()
    assert controller.specification.capacity == 1
    assert controller.development.capacity == 4

    # Test 3: Überlappende Pläne
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)

    # Zwei überlappende Pläne
    overlap_plan1 = ResourcePlan(
        start_day=0,
        end_day=60,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=2,
        rollout_capacity=1
    )
    overlap_plan2 = ResourcePlan(
        start_day=40,
        end_day=100,
        specification_capacity=1,
        development_capacity=4,
        testing_capacity=2,
        rollout_capacity=1
    )

    controller.add_resource_plan(overlap_plan1)
    controller.add_resource_plan(overlap_plan2)

    # Prüfe Kapazitäten im Überlappungsbereich (der letzte Plan gilt)
    controller.current_day = 50
    controller._update_capacities()
    assert controller.specification.capacity == 1
    assert controller.development.capacity == 4
    assert controller.testing.capacity == 2
    assert controller.rollout.capacity == 1

    # Test 4: Keine aktiven Pläne
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)
    future_plan = ResourcePlan(
        start_day=50,
        end_day=100,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=2,
        rollout_capacity=1
    )
    controller.add_resource_plan(future_plan)

    # Prüfe Standardkapazitäten wenn kein Plan aktiv
    controller.current_day = 25
    controller._update_capacities()
    assert controller.specification.capacity == 0
    assert controller.development.capacity == 0
    assert controller.testing.capacity == 0
    assert controller.rollout.capacity == 0


def test_story_processing():
    """
    Tests für die Story-Verarbeitung:
    - Stories durchlaufen alle Phasen korrekt
    - Fehlerbehandlung (z.B. Rückführung zur Spezifikation)
    - Korrekte Warteschlangenverwaltung
    """
    # Test 1: Story durchläuft alle Phasen
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)
    controller.add_resource_plan(ResourcePlan(
        start_day=0,
        end_day=100,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=2,
        rollout_capacity=1
    ))

    # Story mit festen Zeiten für deterministisches Testen
    story = UserStory(
        story_id="TEST-1",
        priority=1,
        arrival_day=1,
        size_factor=1.0,
        phase_durations={
            "spec": 2,
            "dev": 3,
            "test": 2,
            "rollout": 1
        }
    )

    # Story in Spezifikation einfügen
    controller.specification.enqueue(story)
    assert controller.specification.get_queue_length() == 1

    # Tag 1-2: Story in Spezifikation
    controller.execute_tick()  # Tag 1
    assert controller.specification.get_active_count() == 1
    controller.execute_tick()  # Tag 2

    # Prüfen ob die Story in der Development-Phase ist
    # (entweder in der Queue oder bereits aktiv)
    story_in_dev = (
        controller.development.get_queue_length() == 1 or
        controller.development.get_active_count() == 1
    )
    assert story_in_dev, "Story sollte in Development sein"

    # Tag 3-5: Story in Entwicklung
    controller.execute_tick()  # Tag 3
    assert controller.development.get_active_count() == 1
    controller.execute_tick()  # Tag 4
    controller.execute_tick()  # Tag 5
    assert controller.testing.get_queue_length() == 1

    # Tag 6-7: Story in Testing
    controller.execute_tick()  # Tag 6
    assert controller.testing.get_active_count() == 1
    controller.execute_tick()  # Tag 7
    assert controller.rollout.get_queue_length() == 1

    # Tag 8: Story in Rollout und Abschluss
    controller.execute_tick()  # Tag 8
    assert len(controller.completed_stories) == 1

    # Test 2: Fehlerbehandlung - Rückführung zur Spezifikation
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)
    controller.add_resource_plan(ResourcePlan(
        start_day=0,
        end_day=100,
        specification_capacity=2,
        development_capacity=3,
        testing_capacity=2,
        rollout_capacity=1
    ))

    error_story = UserStory(
        story_id="TEST-2",
        priority=1,
        arrival_day=1,
        size_factor=1.0,
        phase_durations={
            "spec": 1,
            "dev": 2,
            "test": 2,
            "rollout": 1
        }
    )

    # Story durchläuft Spezifikation
    controller.specification.enqueue(error_story)
    controller.execute_tick()  # Tag 1
    assert controller.development.get_queue_length() == 1

    # Story geht in Entwicklung und erhält Spezifikationsfehler
    controller.execute_tick()  # Tag 2
    # Prüfe, ob die Story aktiv ist
    assert controller.development.get_active_count() == 1

    # Wichtig: Setze den Fehler VOR dem nächsten execute_tick
    error_story.errors.has_spec_revision_needed = True

    # Führe erst danach den nächsten Tick aus
    controller.execute_tick()  # Tag 3

    # Story sollte zurück in Spezifikation sein
    assert controller.specification.get_queue_length() == 1
    assert controller.development.get_queue_length() == 0

    # Test 3: Warteschlangenverwaltung
    controller = SimulationController(
        total_team_size=8, simulation_duration=100)
    controller.add_resource_plan(ResourcePlan(
        start_day=0,
        end_day=100,
        specification_capacity=1,  # Nur 1 Story gleichzeitig
        development_capacity=3,
        testing_capacity=2,
        rollout_capacity=1
    ))

    # Mehrere Stories in die Warteschlange
    for i in range(3):
        story = UserStory(
            story_id=f"TEST-QUEUE-{i}",
            priority=1,
            arrival_day=1,
            size_factor=1.0,
            phase_durations={
                "spec": 2,
                "dev": 2,
                "test": 2,
                "rollout": 1
            }
        )
        controller.specification.enqueue(story)

    # Prüfe Warteschlangenlänge
    assert controller.specification.get_queue_length() == 3

    # Prüfe FIFO-Verarbeitung
    controller.execute_tick()
    assert controller.specification.get_active_count() == 1
    assert controller.specification.get_queue_length() == 2

# def test_simulation_execution():
#     """
#     Tests für den Simulationsablauf:
#     - execute_tick funktioniert korrekt
#     - run_simulation läuft vollständig durch
#     - Simulationsdauer wird eingehalten
#     """

# def test_statistics():
#     """
#     Tests für die Statistikerfassung:
#     - get_statistics liefert korrekte Werte
#     - Zählung abgeschlossener Stories
#     - Korrekte Erfassung der Stories in jeder Phase
#     """

# def test_edge_cases():
#     """
#     Tests für Randfälle:
#     - Leeres Team
#     - Maximale Teamgröße
#     - Keine ResourcePlans
#     - Ungültige Story-Eigenschaften
#     """
