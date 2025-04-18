import matplotlib.pyplot as plt
import pandas as pd
from typing import List
from .process_statistic import ProcessStatistic


def get_finished_tasks_per_day(
        statistics: List[ProcessStatistic]) -> List[int]:
    """Calculates the cumulative number of tasks in finished stories per day.

    Args:
        statistics: List of ProcessStatistic objects

    Returns:
        List of integers with number of tasks in finished stories per day
    """
    finished_tasks = []

    for stat in statistics:
        # Sum up tasks in all finished stories for this day
        tasks_in_finished_stories = sum(
            story.get_total_tasks()
            for story in stat.finished_work
        )
        finished_tasks.append(tasks_in_finished_stories)

    return finished_tasks


def plot_simulation_results(statistics: List[ProcessStatistic]) -> None:
    """Creates a stacked bar chart of daily tasks.

    Tasks are stacked per day, starting with SPEC (bottom),
    followed by DEV, TEST, and ROLLOUT (top). Additionally shows the
    cumulative number of completed tasks as a line.

    Args:
        statistics: List of ProcessStatistic objects containing the
                  simulation results
    """
    # Prepare data for DataFrame
    data = {
        'Day': [],
        'SPEC': [],
        'DEV': [],
        'TEST': [],
        'ROLLOUT': [],
        'Cumulated': []
    }

    # Get total number of tasks from last day's data
    last_day = statistics[-1].get_task_completion_history_line().split(',')
    # Tasks finished cumulated is at index 11
    total_tasks = int(last_day[11])

    # Calculate finished tasks per day
    finished_tasks = get_finished_tasks_per_day(statistics)

    for stat in statistics:
        # Get task completion data from history line
        completion_data = stat.get_task_completion_history_line().split(',')

        # Indices for completed tasks per phase:
        # SPEC: 5, DEV: 6, TEST: 7, ROLLOUT: 8
        # Cumulated completed tasks: 11
        data['Day'].append(stat.day)
        data['SPEC'].append(int(completion_data[5]))
        data['DEV'].append(int(completion_data[6]))
        data['TEST'].append(int(completion_data[7]))
        data['ROLLOUT'].append(int(completion_data[8]))
        data['Cumulated'].append(int(completion_data[11]))

    df = pd.DataFrame(data)

    # Create bar chart
    fig, ax1 = plt.subplots(figsize=(15, 8))

    # Create stacked bars (left y-axis)
    ax1.bar(df['Day'], df['SPEC'], label='SPEC', color='lightblue',
            alpha=0.6)
    ax1.bar(df['Day'], df['DEV'], bottom=df['SPEC'],
            label='DEV', color='khaki', alpha=0.6)
    ax1.bar(df['Day'], df['TEST'],
            bottom=df['SPEC'] + df['DEV'],
            label='TEST', color='lightgreen', alpha=0.6)
    ax1.bar(df['Day'], df['ROLLOUT'],
            bottom=df['SPEC'] + df['DEV'] + df['TEST'],
            label='ROLLOUT', color='lightcoral', alpha=0.6)

    ax1.set_xlabel('Day')
    ax1.set_ylabel('Active Resources (Tasks Completed)')
    ax1.grid(True, axis='y')

    # Second y-axis for cumulated tasks
    ax2 = ax1.twinx()
    ax2.plot(df['Day'], df['Cumulated'], color='tab:blue', linewidth=2,
             label='Tasks completed (cumulative)')

    # Add burndown line
    remaining_tasks = [total_tasks - ft for ft in finished_tasks]
    ax2.plot(df['Day'], remaining_tasks, color='red', linewidth=2,
             label='Tasks remaining in backlog')

    ax2.set_ylabel('Number of Tasks')

    # Title and legend
    plt.title('Simulation Results')

    # 1) Hole Bar- und Line‑Handles nur einmal
    bar_handles, bar_labels = ax1.get_legend_handles_labels()
    line_handles, line_labels = ax2.get_legend_handles_labels()

    # 2) Baue pairs: je Bar + (entweder Line im ersten Paar oder leer)
    #    Wir nehmen an, es gibt genau 4 Bars und 2 Lines
    h_SPEC, h_DEV, h_TEST, h_ROLLOUT = bar_handles
    l_SPEC, l_DEV, l_TEST, l_ROLLOUT = bar_labels
    h_LINE1, h_LINE2 = line_handles
    l_LINE1, l_LINE2 = line_labels

    # 3) Interleaved handles/labels so dass die erste Zeile die LINEs enthält
    handles = [
        h_SPEC, None, h_DEV, None, h_TEST, None, h_ROLLOUT, None,
        h_LINE1, h_LINE2]
    labels = [
        l_SPEC, "", l_DEV, "", l_TEST, "", l_ROLLOUT, "",
        l_LINE1, l_LINE2]

    # 4) Zeichne Legende in 2 Spalten unter dem Plot
    ax1.legend(
        handles,
        labels,
        ncol=2,
        loc="lower center",
        bbox_to_anchor=(0.80, -0.20),
        frameon=True,
        facecolor="white",
        framealpha=0.9,
        columnspacing=2.0,
        handletextpad=0.5,
    )

    # 5) Unten Platz schaffen
    plt.subplots_adjust(bottom=0.25)
    plt.show()
