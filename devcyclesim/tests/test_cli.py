from click.testing import CliRunner
from cli import cli


def test_cli_bottleneck_scenario():
    """
    Test für ein Bottleneck-Szenario über das CLI.
    Prüft:
    - Verarbeitung mehrerer Stories
    - Korrekte Ausgabe im JSON-Format
    - Bottleneck in der Testing-Phase
      (Kapazität = 1 führt zu verlangsamtem Durchsatz)
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '40',
        '--resource-plan', '1-40:2,3,1,2',  # Testing als Bottleneck
        '--generate-stories', '5',
        '--output-format', 'json',
        '--seed', '42'  # Für Reproduzierbarkeit
    ])

    # Prüfe erfolgreiche Ausführung
    assert result.exit_code == 0

    # Parse JSON-Ausgabe
    import json
    stats = json.loads(result.output)

    # Prüfe Ergebnisse für den letzten Tag
    last_day = max(stats.keys())
    last_day_stats = stats[last_day]

    assert last_day_stats["Fertige Stories"] == 2, (
        "Mit Testing-Bottleneck (Kap.=1) sollten 2 Stories fertig sein"
    )
    assert "TEST WIP" in last_day_stats, (
        "Testing-Phase sollte Stories verarbeitet haben"
    )


def test_cli_resource_plans_file(tmp_path):
    """
    Test für das Laden von Resource Plans aus einer JSON-Datei.
    """
    import json
    # Resource Plans JSON erstellen
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
    assert "Simulationsergebnisse:" in result.output
    assert "Fertige Stories" in result.output


def test_cli_invalid_resource_plan():
    """
    Test für ungültige Resource Plan Eingaben.
    Prüft die Validierung negativer Kapazitäten.
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '--duration', '30',
        '--resource-plan', '1-30:-1,3,3,1'  # Negative Kapazität
    ])

    assert result.exit_code != 0
    assert "Fehler: Capacities cannot be negative" in str(result.output)
