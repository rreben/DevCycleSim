import click


@click.group()
def cli():
    """DevCycleSim - Eine Simulation für Entwicklungsprozesse."""
    pass


@cli.command()
@click.option("--team-size", default=8, help="Größe des Teams")
@click.option("--duration", default=100, help="Simulationsdauer in Tagen")
@click.option(
    "--resource-plan", multiple=True,
    help='Format: "start-end:spec,dev,test,rollout"'
)
@click.option(
    "--resource-plans-file",
    type=click.Path(exists=True),
    help="JSON-Datei mit Resource Plans",
)
@click.option(
    "--stories-file", type=click.Path(exists=True),
    help="JSON-Datei mit User Stories"
)
@click.option(
    "--generate-stories", type=int, help="Anzahl der zu generierenden Stories"
)
@click.option("--seed", type=int,
              help="Zufallsseed für reproduzierbare Ergebnisse")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "csv"]),
    default="text",
    help="Ausgabeformat",
)
@click.option("--output-file", type=click.Path(),
              help="Ausgabedatei (default: stdout)")
@click.option("--verbose", is_flag=True, help="Detaillierte Ausgabe")
def run(
    team_size,
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
    """Führt eine Entwicklungsprozess-Simulation aus."""
    import json
    import random
    from devcyclesim.src.simulation_controller import SimulationController
    from devcyclesim.src.simulation_controller import ResourcePlan
    from devcyclesim.src.user_story import UserStory

    try:
        # Seed setzen falls angegeben
        if seed is not None:
            random.seed(seed)

        # Controller erstellen
        controller = SimulationController(
            total_team_size=team_size,
            simulation_duration=duration
        )

        # Resource Plans verarbeiten
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
                    controller.add_resource_plan(plan)

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
                controller.add_resource_plan(plan)

        # Wenn keine Resource Plans definiert wurden, Standard-Plan verwenden
        if not resource_plans_file and not resource_plan:
            controller = SimulationController.create_with_default_plan(
                team_size=team_size,
                simulation_duration=duration
            )

        # Stories laden oder generieren
        if stories_file:
            with open(stories_file, 'r') as f:
                stories_data = json.load(f)
                for story_data in stories_data:
                    story = UserStory(
                        story_id=story_data['id'],
                        phase_durations={
                            "spec": random.randint(1, 5),
                            "dev": random.randint(1, 5),
                            "test": random.randint(1, 5),
                            "rollout": random.randint(1, 5)
                        }
                    )
                    controller.specification.enqueue(story)
        elif generate_stories:
            for i in range(generate_stories):
                story = UserStory(
                    story_id=f"STORY-{i+1}",
                    phase_durations={
                        "spec": random.randint(1, 5),
                        "dev": random.randint(1, 5),
                        "test": random.randint(1, 5),
                        "rollout": random.randint(1, 5)
                    }
                )
                controller.specification.enqueue(story)

        if verbose:
            click.echo(
                f"Starte Simulation mit {team_size} Teammitgliedern "
                f"für {duration} Tage")

        # Simulation ausführen
        if verbose:
            controller.run_simulation()  # Mit Debug-Ausgaben
        else:
            # Debug-Ausgaben in execute_tick temporär deaktivieren
            original_print = print

            def silent_print(*args, **kwargs):
                pass
            import builtins
            builtins.print = silent_print

            controller.run_simulation()

            # Print-Funktion wiederherstellen
            builtins.print = original_print

        # Statistiken sammeln
        stats = controller.get_statistics()

        # Ausgabe formatieren
        if output_format == "json":
            output = json.dumps(stats, indent=2)
        elif output_format == "csv":
            output = "Metrik,Wert\n" + "\n".join(
                f"{k},{v}" for k, v in stats.items()
            )
        else:  # text
            output = "Simulationsergebnisse:\n" + "\n".join(
                f"- {k}: {v}" for k, v in stats.items()
            )

        # Ausgabe speichern oder anzeigen
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
        else:
            click.echo(output)

        if verbose:
            click.echo("\nSimulation abgeschlossen!")

    except ValueError as e:
        click.echo(str(e))  # Gibt die Fehlermeldung aus
        raise click.Abort()  # Beendet das Programm mit Fehlercode


if __name__ == "__main__":
    cli()
