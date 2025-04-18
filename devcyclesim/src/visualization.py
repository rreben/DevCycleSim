import matplotlib.pyplot as plt
import pandas as pd
from typing import List
from .process_statistic import ProcessStatistic


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
    ax2.set_ylabel('Number of Tasks')

    # Title and legend
    plt.title('Simulation Results')

    # 1) Hole Bar- und Line‑Handles nur einmal
    bar_handles, bar_labels = ax1.get_legend_handles_labels()
    line_handles, line_labels = ax2.get_legend_handles_labels()

    # 2) Baue pairs: je Bar + (entweder Line im ersten Paar oder leer)
    #    Wir nehmen an, es gibt genau 4 Bars und 1 Line
    h_SPEC, h_DEV, h_TEST, h_ROLLOUT = bar_handles
    l_SPEC, l_DEV, l_TEST, l_ROLLOUT = bar_labels
    h_LINE = line_handles[0]
    l_LINE = line_labels[0]

    # 3) Interleaved handles/labels so dass die erste Zeile die LINE enthält
    handles = [
        h_SPEC, None, h_DEV, None, h_TEST, None, h_ROLLOUT, None, None,
        h_LINE]
    labels = [l_SPEC, "", l_DEV, "", l_TEST, "", l_ROLLOUT, "", "", l_LINE]

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
