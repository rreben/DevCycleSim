import click
import json
from devcyclesim.src.process import Process, ResourcePlan
from devcyclesim.src.user_story import UserStory, Phase
from devcyclesim.src.visualization import plot_simulation_results
import random
import numpy as np
from devcyclesim.src.user_story import Task


@click.group()
def cli():
    """DevCycleSim - A simulation for development processes."""
    pass


@cli.command()
@click.option("-d", "--duration", default=14, help="Simulation duration in days")
@click.option(
    "-r", "--resource-plan", multiple=True,
    help='Format: "start-end:spec,dev,test,rollout"'
)
@click.option(
    "--resource-plans-file",
    type=click.Path(exists=True),
    help="JSON file with resource plans",
)
@click.option(
    "-s", "--stories-file", type=click.Path(exists=True),
    help="JSON file with user stories"
)
@click.option(
    "-g", "--generate-stories", type=int, help="Number of stories to generate"
)
@click.option("--seed", type=int,
              help="Random seed for reproducible results")
@click.option(
    "-t", "--output-format",
    type=click.Choice(["text", "json", "csv"]),
    default="text",
    help="Output format",
)
@click.option("-o", "--output-file", type=click.Path(),
              help="Output file (default: stdout)")
@click.option("-v", "--verbose", is_flag=True, help="Detailed output")
@click.option('-p', '--plot', is_flag=True, help='Plot simulation results')
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
    plot,
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
            try:
                with open(resource_plans_file, 'r') as f:
                    try:
                        plans_data = json.load(f)
                    except json.JSONDecodeError:
                        msg = (
                            "Invalid JSON format in resource plans file: "
                            f"{resource_plans_file}"
                        )
                        raise ValueError(msg)

                    for plan_data in plans_data:
                        try:
                            plan = ResourcePlan(
                                start_day=plan_data['start'],
                                end_day=plan_data['end'],
                                specification_capacity=(
                                    plan_data['resources']['spec']
                                ),
                                development_capacity=(
                                    plan_data['resources']['dev']
                                ),
                                testing_capacity=(
                                    plan_data['resources']['test']
                                ),
                                rollout_capacity=(
                                    plan_data['resources']['rollout']
                                )
                            )
                        except KeyError as e:
                            msg = (
                                f"Missing required field in resource plan: {e}"
                            )
                            raise ValueError(msg)
                        process.add_resource_plan(plan)
            except FileNotFoundError:
                msg = f"Resource plans file not found: {resource_plans_file}"
                raise ValueError(msg)

        if resource_plan:
            for plan_str in resource_plan:
                try:
                    start_end, resources = plan_str.split(':')
                    start, end = map(int, start_end.split('-'))
                    spec, dev, test, rollout = map(int, resources.split(','))
                except ValueError:
                    msg = (
                        f"Invalid resource plan format: {plan_str}. "
                        'Expected format: "start-end:spec,dev,test,rollout"'
                    )
                    raise ValueError(msg)

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
            try:
                with open(stories_file, 'r') as f:
                    try:
                        stories_data = json.load(f)
                    except json.JSONDecodeError:
                        msg = (
                            "Invalid JSON format in stories file: "
                            f"{stories_file}"
                        )
                        raise ValueError(msg)

                    for story_data in stories_data:
                        try:
                            if "tasks" in story_data:
                                # Neue, flexible Variante:
                                # beliebige Reihenfolge
                                # und Wiederholungen
                                task_list = []
                                for task_entry in story_data["tasks"]:
                                    phase = Phase(task_entry["phase"])
                                    count = task_entry.get("count", 1)
                                    task_list.extend(
                                        [Task(phase=phase)
                                         for _ in range(count)])
                                    story = UserStory(
                                        story_id=story_data["id"],
                                        tasks=np.array(
                                            task_list, dtype=object),
                                        arrival_day=story_data.get(
                                            "arrival_day", 1),
                                        priority=story_data.get("priority", 1)
                                    )
                            else:
                                # Alte, klassische Variante: eine Phase pro Typ
                                story = UserStory.from_phase_durations(
                                    story_id=story_data['id'],
                                    phase_durations={
                                        Phase.SPEC: story_data.get(
                                            'spec', random.randint(1, 3)),
                                        Phase.DEV: story_data.get(
                                            'dev', random.randint(2, 4)),
                                        Phase.TEST: story_data.get(
                                            'test', random.randint(1, 3)),
                                        Phase.ROLLOUT: story_data.get(
                                            'rollout', 1)
                                    },
                                    arrival_day=story_data.get(
                                        'arrival_day', 1),
                                    priority=story_data.get('priority', 1)
                                )
                        except KeyError as e:
                            msg = (
                                f"Missing required field in story: "
                                f"'{e.args[0]}'"
                            )
                            raise ValueError(msg)
                        process.add(story)
            except FileNotFoundError:
                msg = f"Stories file not found: {stories_file}"
                raise ValueError(msg)
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

        # Plot erstellen wenn gewünscht
        if plot:
            plot_simulation_results(process.get_statistics())

        # Collect statistics
        stats = process.get_statistics()

        # Prepare statistics for output
        stats_dict = {}
        final_completion_dates = {}

        # Get completion dates from the last day's statistics
        if stats:
            final_completion_dates = stats[-1].task_completion_dates

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
            # Convert Phase objects to strings for JSON serialization
            serializable_completion_dates = {}
            for story_id, dates in final_completion_dates.items():
                completed = [
                    (phase.name, day)
                    for phase, day in dates["completed"]
                ]
                pending = [
                    (phase.name, day)
                    for phase, day in dates["pending"]
                ]
                serializable_completion_dates[story_id] = {
                    "completed": completed,
                    "pending": pending
                }

            # For JSON, include completion dates in a separate section
            output_data = {
                "daily_statistics": stats_dict,
                "task_completion_dates": serializable_completion_dates
            }
            output = json.dumps(output_data, indent=2)
        elif output_format == "csv":
            # Build output string
            output_parts = [
                # Main statistics
                "Queue Statistics",
                stats[0].get_csv_header(),
                *[stat.get_csv_line() for stat in stats],
                "",
                # Task completion summary
                "Task Completion Summary",
                stats[0].get_task_completion_csv_header(),
                *[stat.get_task_completion_csv_line() for stat in stats],
                "",
                # Task completion history
                "Task Completion History",
                "S: Specification, D: Development, T: Testing, R: Rollout",
                stats[0].get_task_completion_history_header(),
                *[stat.get_task_completion_history_line() for stat in stats]
            ]
            output = "\n".join(output_parts)
        else:  # text
            # First add daily statistics
            output = "Simulation Results:\n\n"
            for day, day_stats in stats_dict.items():
                output += f"{day}:\n"
                for metric, value in day_stats.items():
                    output += f"  {metric}: {value}\n"
                output += "\n"

            # Then add completion dates summary at the end
            if final_completion_dates:
                output += "Task Completion Summary:\n"
                output += "-" * 50 + "\n"
                for story_id, dates in final_completion_dates.items():
                    output += f"\nStory {story_id}:\n"
                    if dates["completed"]:
                        output += "  Completed Tasks:\n"
                        for phase, day in dates["completed"]:
                            output += f"    {phase.name}: Day {day}\n"
                    if dates["pending"]:
                        output += "  Pending Tasks:\n"
                        for phase, _ in dates["pending"]:
                            output += f"    {phase.name}: Not completed\n"

        # Save or display output
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(output)
            except IOError:
                msg = f"Could not write to output file: {output_file}"
                raise ValueError(msg)
        else:
            click.echo(output)

        if verbose:
            click.echo("\nSimulation completed!")

    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        raise click.Abort()
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}")
        if verbose:
            import traceback
            click.echo("\nDetailed error information:")
            click.echo(traceback.format_exc())
        raise click.Abort()


if __name__ == "__main__":
    cli()
