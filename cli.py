import click
import json
import random
from devcyclesim.src.process import Process, ResourcePlan
from devcyclesim.src.user_story import UserStory, Phase


@click.group()
def cli():
    """DevCycleSim - A simulation for development processes."""
    pass


@cli.command()
@click.option("--duration", default=14, help="Simulation duration in days")
@click.option(
    "--resource-plan", multiple=True,
    help='Format: "start-end:spec,dev,test,rollout"'
)
@click.option(
    "--resource-plans-file",
    type=click.Path(exists=True),
    help="JSON file with resource plans",
)
@click.option(
    "--stories-file", type=click.Path(exists=True),
    help="JSON file with user stories"
)
@click.option(
    "--generate-stories", type=int, help="Number of stories to generate"
)
@click.option("--seed", type=int,
              help="Random seed for reproducible results")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "csv"]),
    default="text",
    help="Output format",
)
@click.option("--output-file", type=click.Path(),
              help="Output file (default: stdout)")
@click.option("--verbose", is_flag=True, help="Detailed output")
def run(
    duration,
    resource_plan,
    resource_plans_file,
    stories_file,
    generate_stories,
    seed,
    output_format,
    output_file,
    verbose,
):
    """Runs a development process simulation."""
    try:
        # Set seed if specified
        if seed is not None:
            random.seed(seed)

        # Create process
        process = Process(simulation_days=duration)

        # Process resource plans
        if resource_plans_file:
            with open(resource_plans_file, 'r') as f:
                plans_data = json.load(f)
                for plan_data in plans_data:
                    plan = ResourcePlan(
                        start_day=plan_data['start'],
                        end_day=plan_data['end'],
                        specification_capacity=plan_data['resources']['spec'],
                        development_capacity=plan_data['resources']['dev'],
                        testing_capacity=plan_data['resources']['test'],
                        rollout_capacity=plan_data['resources']['rollout']
                    )
                    process.add_resource_plan(plan)

        if resource_plan:
            for plan_str in resource_plan:
                start_end, resources = plan_str.split(':')
                start, end = map(int, start_end.split('-'))
                spec, dev, test, rollout = map(int, resources.split(','))
                plan = ResourcePlan(
                    start_day=start,
                    end_day=end,
                    specification_capacity=spec,
                    development_capacity=dev,
                    testing_capacity=test,
                    rollout_capacity=rollout
                )
                process.add_resource_plan(plan)

        # Load or generate stories
        if stories_file:
            with open(stories_file, 'r') as f:
                stories_data = json.load(f)
                for story_data in stories_data:
                    story = UserStory.from_phase_durations(
                        story_id=story_data['id'],
                        phase_durations={
                            Phase.SPEC: story_data.get(
                                'spec', random.randint(1, 3)),
                            Phase.DEV: story_data.get(
                                'dev', random.randint(2, 4)),
                            Phase.TEST: story_data.get(
                                'test', random.randint(1, 3)),
                            Phase.ROLLOUT: story_data.get('rollout', 1)
                        },
                        arrival_day=story_data.get('arrival_day', 1),
                        priority=story_data.get('priority', 1)
                    )
                    process.add(story)
        elif generate_stories:
            for i in range(generate_stories):
                story = UserStory.from_phase_durations(
                    story_id=f"STORY-{i+1}",
                    phase_durations={
                        Phase.SPEC: random.randint(1, 3),
                        Phase.DEV: random.randint(2, 4),
                        Phase.TEST: random.randint(1, 3),
                        Phase.ROLLOUT: 1
                    }
                )
                process.add(story)

        if verbose:
            click.echo(f"Starting simulation for {duration} days")

        # Run simulation
        process.start()

        # Collect statistics
        stats = process.get_statistics()

        # Prepare statistics for output
        stats_dict = {}
        for day_stat in stats:
            stats_dict[f"Day {day_stat.day}"] = {
                "Backlog": day_stat.backlog_count,
                "SPEC Input": day_stat.spec_stats.input_queue_count,
                "SPEC WIP": day_stat.spec_stats.work_in_progress_count,
                "SPEC Done": day_stat.spec_stats.done_count,
                "DEV Input": day_stat.dev_stats.input_queue_count,
                "DEV WIP": day_stat.dev_stats.work_in_progress_count,
                "DEV Done": day_stat.dev_stats.done_count,
                "TEST Input": day_stat.test_stats.input_queue_count,
                "TEST WIP": day_stat.test_stats.work_in_progress_count,
                "TEST Done": day_stat.test_stats.done_count,
                "ROLLOUT Input": day_stat.rollout_stats.input_queue_count,
                "ROLLOUT WIP": day_stat.rollout_stats.work_in_progress_count,
                "ROLLOUT Done": day_stat.rollout_stats.done_count,
                "Finished Stories": day_stat.finished_work_count
            }

        # Format output
        if output_format == "json":
            output = json.dumps(stats_dict, indent=2)
        elif output_format == "csv":
            # Create header
            headers = ["Day"] + list(next(iter(stats_dict.values())).keys())
            rows = [",".join(headers)]

            # Add data
            for day, day_stats in stats_dict.items():
                row = [day] + [str(v) for v in day_stats.values()]
                rows.append(",".join(row))

            output = "\n".join(rows)
        else:  # text
            output = "Simulation Results:\n\n"
            for day, day_stats in stats_dict.items():
                output += f"{day}:\n"
                for metric, value in day_stats.items():
                    output += f"  {metric}: {value}\n"
                output += "\n"

        # Save or display output
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
        else:
            click.echo(output)

        if verbose:
            click.echo("\nSimulation completed!")

    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
