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
    
    # Combined legend for both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, 
               loc='upper right', 
               facecolor='white', 
               framealpha=0.9)
    
    # Show diagram
    plt.show()
