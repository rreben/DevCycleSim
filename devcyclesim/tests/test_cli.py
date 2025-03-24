import pytest
from click.testing import CliRunner
from cli import cli


def test_cli_bottleneck_scenario():
    """
    Test für ein Bottleneck-Szenario über das CLI.
    Prüft:
    - Verarbeitung mehrerer Stories
    - Korrekte Ausgabe im JSON-Format
    - Bottleneck in der Testing-Phase
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--team-size', '8',
        '--duration', '40',
        '--resource-plan', '0-40:2,3,1,2',  # Testing als Bottleneck
        '--generate-stories', '5',
        '--output-format', 'json',
        '--seed', '42'  # Für Reproduzierbarkeit
    ])

    # Prüfe erfolgreiche Ausführung
    assert result.exit_code == 0

    # Parse JSON-Ausgabe
    import json
    stats = json.loads(result.output)

    # Prüfe Ergebnisse
    assert stats["Completed Stories"] == 5, (
        "Alle 5 Stories sollten abgeschlossen sein"
    )
    assert stats["Stories in Testing"] >= 0, (
        "Testing-Phase sollte Stories verarbeitet haben"
    )


def test_cli_resource_plans_file(tmp_path: pytest.TempPathFactory):
    """
    Test für das Laden von Resource Plans aus einer JSON-Datei.
    """
    import json
    # Resource Plans JSON erstellen
    plans_file = str(tmp_path) + "/resource_plans.json"
    plans_data = [
        {
            "start": 0,
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
        '--team-size', '8',
        '--duration', '30',
        '--resource-plans-file', str(plans_file),
        '--generate-stories', '3',
        '--output-format', 'text'
    ])

    assert result.exit_code == 0
    assert "Simulationsergebnisse:" in result.output
    assert "Completed Stories" in result.output


def test_cli_invalid_resource_plan():
    """
    Test für ungültige Resource Plan Eingaben.
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--team-size', '8',
        '--duration', '30',
        '--resource-plan', '0-30:3,3,3,3'  # Summe > team_size
    ])

    assert result.exit_code != 0
    assert "Total capacity exceeds team size" in result.output
