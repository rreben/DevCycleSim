from click.testing import CliRunner
import json
from devcyclesim.src.cli import cli


def test_cli_bottleneck_scenario():
    """
    Test for a bottleneck scenario via CLI.
    Checks:
    - Processing of multiple stories
    - Correct JSON output
    - Bottleneck in testing phase
      (capacity = 1 leads to reduced throughput)
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '40',
        '--resource-plan', '1-40:2,3,1,2',  # Testing as bottleneck
        '--generate-stories', '5',
        '--output-format', 'json',
        '--seed', '42'  # For reproducibility
    ])

    # Debug output - immer ausgeben
    print("\n=== Debug Information ===")
    print(f"Exit Code: {result.exit_code}")
    print(f"Exception Type: {type(result.exception)}")
    print(f"Exception: {result.exception}")
    print("Output:")
    print(result.output)
    print("=== End Debug Information ===\n")

    # Check successful execution
    assert result.exit_code == 0, f"CLI failed with: {result.output}"

    # Parse JSON output
    data = json.loads(result.output)
    assert "daily_statistics" in data
    stats = data["daily_statistics"]

    # Check results for the last day
    last_day = max(stats.keys())
    last_day_stats = stats[last_day]

    assert last_day_stats["Finished Stories"] == 2, (
        "With testing bottleneck (cap=1), 2 stories should be finished"
    )
    assert "TEST WIP" in last_day_stats, (
        "Testing phase should have processed stories"
    )


def test_cli_resource_plans_file(tmp_path):
    """
    Test for loading resource plans from a JSON file.
    """
    # Create resource plans JSON
    plans_file = str(tmp_path / "resource_plans.json")
    plans_data = [
        {
            "start": 1,
            "end": 20,
            "resources": {
                "spec": 2,
                "dev": 3,
                "test": 2,
                "rollout": 1
            }
        }
    ]
    with open(plans_file, 'w') as f:
        json.dump(plans_data, f)

    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '30',
        '--resource-plans-file', plans_file,
        '--generate-stories', '3',
        '--output-format', 'text'
    ])

    assert result.exit_code == 0
    assert "Simulation Results:" in result.output
    assert "Finished Stories" in result.output


def test_cli_invalid_resource_plan():
    """
    Test for invalid resource plan inputs.
    Verifies validation of negative capacities.
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '30',
        '--resource-plan', '1-30:-1,3,3,1'  # Negative capacity
    ])

    assert result.exit_code != 0
    assert "Error: Capacities cannot be negative" in str(result.output)


def test_cli_default_values():
    """
    Test for running simulation with default values.
    Verifies that the simulation runs successfully without any parameters.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ['run'])

    assert result.exit_code == 0
    assert "Simulation Results:" in result.output


def test_cli_stories_file(tmp_path):
    """
    Test for loading stories from a JSON file.
    """
    # Create stories JSON
    stories_file = str(tmp_path / "stories.json")
    stories_data = [
        {
            "id": "STORY-1",
            "spec": 2,
            "dev": 5,
            "test": 3,
            "rollout": 1
        },
        {
            "id": "STORY-2",
            "spec": 3,
            "dev": 8,
            "test": 4,
            "rollout": 2
        }
    ]
    with open(stories_file, 'w') as f:
        json.dump(stories_data, f)

    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '30',
        '--stories-file', stories_file,
        '--output-format', 'text'
    ])

    assert result.exit_code == 0
    assert "Simulation Results:" in result.output


def test_cli_csv_output():
    """
    Test for CSV output format.
    Verifies that the output contains the correct CSV headers and format.
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '10',
        '--generate-stories', '3',
        '--output-format', 'csv'
    ])

    assert result.exit_code == 0
    expected_header = (
        "Day,Backlog,Finished,"
        "SPEC_Input,SPEC_InProgress,SPEC_Done,SPEC_Capacity,"
        "DEV_Input,DEV_InProgress,DEV_Done,DEV_Capacity,"
        "TEST_Input,TEST_InProgress,TEST_Done,TEST_Capacity,"
        "ROLLOUT_Input,ROLLOUT_InProgress,ROLLOUT_Done,ROLLOUT_Capacity"
    )
    assert expected_header in result.output


def test_cli_multiple_resource_plans():
    """
    Test for multiple resource plans as shown in the README example.
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '50',
        '--resource-plan', '1-25:3,4,2,1',
        '--resource-plan', '26-50:2,5,2,1',
        '--generate-stories', '5',
        '--output-format', 'json'
    ])

    assert result.exit_code == 0
    stats = json.loads(result.output)
    assert len(stats) > 0


def test_cli_verbose_output():
    """
    Test for verbose output option.
    Verifies that additional information is displayed.
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '10',
        '--generate-stories', '2',
        '--verbose'
    ])

    assert result.exit_code == 0
    assert "Starting simulation for 10 days" in result.output
    assert "Simulation completed!" in result.output


def test_cli_overlapping_resource_plans():
    """
    Test for overlapping resource plans.
    Verifies that overlapping plans are correctly detected and rejected.
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '30',
        '--resource-plan', '1-15:2,3,2,1',
        '--resource-plan', '10-20:3,4,2,1'  # Overlaps with first plan
    ])

    assert result.exit_code != 0
    assert "overlaps with existing plan" in str(result.output)
    assert "1-15" in str(result.output)
    assert "10-20" in str(result.output)


def test_cli_incomplete_story():
    """
    Test for incomplete user story definition.
    Verifies that stories with missing required fields are rejected.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create stories JSON with missing required field (id)
        with open('incomplete_stories.json', 'w') as f:
            json.dump([
                {
                    # "id" field is missing
                    "spec": 2,
                    "dev": 5,
                    "test": 3,
                    "rollout": 1
                }
            ], f)

        result = runner.invoke(cli, [
            'run',
            '--duration', '30',
            '--stories-file', 'incomplete_stories.json'
        ])

        assert result.exit_code != 0
        assert "Missing required field in story: 'id'" in str(result.output)


def test_cli_negative_story_duration():
    """
    Test for user story with negative duration.
    Verifies that stories with negative phase durations are rejected.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create stories JSON with negative duration in dev phase
        with open('negative_duration.json', 'w') as f:
            json.dump([
                {
                    "id": "STORY-1",
                    "spec": 2,
                    "dev": -3,  # Negative duration
                    "test": 2,
                    "rollout": 1
                }
            ], f)

        result = runner.invoke(cli, [
            'run',
            '--duration', '30',
            '--stories-file', 'negative_duration.json'
        ])

        assert result.exit_code != 0
        assert "All phase durations must be positive" in str(result.output)


def test_cli_task_completion_summary():
    """
    Test für die Task Completion Summary und History.
    Überprüft:
    - Korrekte Anzeige der Task Completion Summary
    - Korrekte Anzeige der Task Completion History mit Kapazitäten
    - Format der Ausgabe für verschiedene Output-Formate
    """
    runner = CliRunner()

    # Test für CSV-Format mit zwei Stories
    csv_result = runner.invoke(cli, [
        'run',
        '--duration', '20',
        '--generate-stories', '2',
        '--seed', '42',  # Für Reproduzierbarkeit
        '--resource-plan', '1-20:2,3,2,1',  # Feste Kapazitäten für Test
        '--output-format', 'csv'
    ])

    assert csv_result.exit_code == 0
    csv_output = csv_result.output

    # Prüfe Queue Statistics Header
    assert "Queue Statistics" in csv_output

    # Prüfe Task Completion Summary
    assert "Task Completion Summary" in csv_output
    assert "Day,STORY-1,STORY-2" in csv_output
    # Prüfe auf mindestens einen abgeschlossenen Task
    assert ",1," in csv_output or ",1\n" in csv_output

    # Prüfe Task Completion History
    assert "Task Completion History" in csv_output
    assert ("S: Specification, D: Development, T: Testing, "
           "R: Rollout") in csv_output

    # Prüfe History Header
    history_header_parts = [
        "Day",
        "SPEC_Capacity,DEV_Capacity,TEST_Capacity,ROLLOUT_Capacity",
        "SPEC_completed,DEV_completed,TEST_completed,ROLLOUT_completed",
        "STORY-1,STORY-2"
    ]
    history_header = ",".join(history_header_parts)
    assert history_header in csv_output

    # Prüfe Kapazitäten in der History
    assert " 2, 3, 2, 1," in csv_output  # Prüfe konfigurierte Kapazitäten

    # Prüfe Task Completion Indikatoren und Counts
    lines = csv_output.split('\n')
    found_completion = False
    in_history_section = False

    for line in lines:
        # Identifiziere den Start der History-Sektion
        if "Task Completion History" in line:
            in_history_section = True
            continue

        # Überspringe Zeilen bis zur History-Sektion
        if not in_history_section:
            continue

        # Überspringe Header-Zeilen
        if not line.strip() or "Day" in line or ":" in line:
            continue

        # Verarbeite nur Zeilen mit Daten
        if line.strip() and any(x in line for x in ['S', 'D', 'T', 'R']):
            parts = line.split(',')
            if len(parts) >= 9:  # Tag + 8 Metriken vor Stories
                try:
                    # Prüfe, ob mindestens ein Count > 0 ist
                    counts = [int(x.strip()) for x in parts[5:9]]
                    assert sum(counts) > 0
                    found_completion = True
                    break
                except ValueError:
                    continue  # Überspringe Zeilen, die keine gültigen Zahlen
                    # enthalten

    assert found_completion, "Keine Task Completion gefunden"
