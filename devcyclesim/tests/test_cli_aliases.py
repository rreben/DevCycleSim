from click.testing import CliRunner
import json
from devcyclesim.src.cli import cli

def test_cli_aliases_basic():
    """
    Test basic aliases: -d (duration), -g (generate-stories), -t (output-format)
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '-d', '10',
        '-g', '2',
        '-t', 'json',
        '--seed', '42'
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "daily_statistics" in data

def test_cli_aliases_resource_plan():
    """
    Test resource plan alias: -r
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '-d', '10',
        '-r', '1-10:2,3,2,1',
        '-g', '2'
    ])
    
    assert result.exit_code == 0
    assert "Simulation Results:" in result.output

def test_cli_aliases_stories_file(tmp_path):
    """
    Test stories file alias: -s
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
        }
    ]
    with open(stories_file, 'w') as f:
        json.dump(stories_data, f)

    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '-d', '10',
        '-s', stories_file
    ])

    assert result.exit_code == 0
    assert "Simulation Results:" in result.output

def test_cli_aliases_verbose():
    """
    Test verbose alias: -v
    """
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '-d', '5',
        '-g', '1',
        '-v'
    ])
    
    assert result.exit_code == 0
    assert "Starting simulation" in result.output

def test_cli_aliases_output_file(tmp_path):
    """
    Test output file alias: -o
    """
    output_file = str(tmp_path / "output.txt")
    runner = CliRunner()
    result = runner.invoke(cli, [
        'run',
        '-d', '5',
        '-g', '1',
        '-o', output_file
    ])
    
    assert result.exit_code == 0
    with open(output_file, 'r') as f:
        content = f.read()
        assert "Simulation Results:" in content
