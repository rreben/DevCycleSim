import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Optional
from .process_statistic import ProcessStatistic
from .user_story import Phase


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


def plot_simulation_results(
    statistics: List[ProcessStatistic],
    highlight_feature_id: Optional[str] = None
) -> None:
    """Creates a stacked bar chart of daily tasks.

    Tasks are stacked per day, starting with SPEC (bottom),
    followed by DEV, TEST, and ROLLOUT (top). Additionally shows the
    cumulative number of completed tasks as a line.

    If highlight_feature_id is provided, stories belonging to this feature
    are shown in color, while others are shown in gray.

    Args:
        statistics: List of ProcessStatistic objects containing the
                  simulation results
        highlight_feature_id: Optional ID of a feature to highlight
    """
    # Prepare data for DataFrame
    data = {
        'Day': [],
        'SPEC': [], 'SPEC_Other': [],
        'DEV': [], 'DEV_Other': [],
        'TEST': [], 'TEST_Other': [],
        'ROLLOUT': [], 'ROLLOUT_Other': [],
        'Cumulated': []
    }

    # Get total number of tasks from last day's data
    last_day_stats = statistics[-1].get_daily_completion_stats()
    total_tasks = last_day_stats['tasks_finished_cumulated']

    # Calculate finished tasks per day
    finished_tasks = get_finished_tasks_per_day(statistics)

    for stat in statistics:
        # Initialize counts
        counts = {
            'SPEC': 0, 'SPEC_Other': 0,
            'DEV': 0, 'DEV_Other': 0,
            'TEST': 0, 'TEST_Other': 0,
            'ROLLOUT': 0, 'ROLLOUT_Other': 0
        }
        
        # Calculate daily completions split by feature
        story_ids = stat.task_completion_dates.keys()
        for story_id in story_ids:
            # Determine if this story belongs to the highlighted feature
            # If no highlight_feature_id is set, everything counts as "Focus"
            feature_id = stat.story_feature_map.get(story_id)
            is_target = (highlight_feature_id is None or 
                        feature_id == highlight_feature_id)
            suffix = "" if is_target else "_Other"

            # Check completions for this story on this day
            dates = stat.task_completion_dates[story_id]
            for phase, day in dates["completed"]:
                if day == stat.day:
                    if phase == Phase.SPEC:
                        counts[f'SPEC{suffix}'] += 1
                    elif phase == Phase.DEV:
                        counts[f'DEV{suffix}'] += 1
                    elif phase == Phase.TEST:
                        counts[f'TEST{suffix}'] += 1
                    elif phase == Phase.ROLLOUT:
                        counts[f'ROLLOUT{suffix}'] += 1

        # Get cumulative total (same as before)
        completion_data = stat.get_daily_completion_stats()
        
        data['Day'].append(stat.day)
        data['SPEC'].append(counts['SPEC'])
        data['SPEC_Other'].append(counts['SPEC_Other'])
        data['DEV'].append(counts['DEV'])
        data['DEV_Other'].append(counts['DEV_Other'])
        data['TEST'].append(counts['TEST'])
        data['TEST_Other'].append(counts['TEST_Other'])
        data['ROLLOUT'].append(counts['ROLLOUT'])
        data['ROLLOUT_Other'].append(counts['ROLLOUT_Other'])
        data['Cumulated'].append(completion_data['tasks_completed_cumulated'])

    df = pd.DataFrame(data)

    # Create bar chart
    fig, ax1 = plt.subplots(figsize=(15, 8))

    # Define colors
    colors = {
        'SPEC': 'lightblue', 'SPEC_Other': '#E0E0E0',
        'DEV': 'khaki', 'DEV_Other': '#D3D3D3',
        'TEST': 'lightgreen', 'TEST_Other': '#C0C0C0',
        'ROLLOUT': 'lightcoral', 'ROLLOUT_Other': '#A9A9A9'
    }

    # Stack order: SPEC_Other, SPEC, DEV_Other, DEV, etc.
    stack_order = [
        ('SPEC_Other', 'SPEC (Other)'),
        ('SPEC', 'SPEC'),
        ('DEV_Other', 'DEV (Other)'),
        ('DEV', 'DEV'),
        ('TEST_Other', 'TEST (Other)'),
        ('TEST', 'TEST'),
        ('ROLLOUT_Other', 'ROLLOUT (Other)'),
        ('ROLLOUT', 'ROLLOUT')
    ]

    bottom = pd.Series([0] * len(df))
    
    # Store handles for legend
    legend_handles = {}

    for col, label in stack_order:
        # Only plot if there is data (optimization) or if it's a primary column
        # Ideally we plot everything to keep the stack consistent
        
        # If not highlighting, skip "Other" columns to avoid clutter/confusing legend
        # (Though values should be 0 anyway)
        if highlight_feature_id is None and 'Other' in col:
            continue

        color = colors[col]
        
        # Plot bar
        bars = ax1.bar(
            df['Day'], df[col],
            bottom=bottom,
            label=label if 'Other' not in col else None, # Only label main phases
            color=color,
            alpha=0.6 if 'Other' not in col else 0.4
        )
        
        # Update bottom
        bottom += df[col]
        
        # Store handle if it's a main phase
        if 'Other' not in col:
            legend_handles[col] = bars

    ax1.set_xlabel('Day')
    ax1.set_ylabel('Active Resources (Tasks Completed)')
    ax1.grid(True, axis='y')

    # Second y-axis for cumulated tasks
    ax2 = ax1.twinx()
    start_label = 'Tasks completed (cumulative)'
    line1, = ax2.plot(df['Day'], df['Cumulated'], color='tab:blue', linewidth=2,
             label=start_label)

    # Add burndown line
    remaining_tasks = [total_tasks - ft for ft in finished_tasks]
    line2, = ax2.plot(
        df['Day'],
        remaining_tasks,
        color='red',
        linewidth=2,
        label='Tasks in unfinished user stories (run-down)'
    )

    # Add work in progress line
    work_in_progress = []
    for stat in statistics:
        completion_data = stat.get_daily_completion_stats()
        tasks_completed = completion_data['tasks_completed_cumulated']
        tasks_in_finished = sum(
            story.get_total_tasks()
            for story in stat.finished_work
        )
        work_in_progress.append(tasks_completed - tasks_in_finished)

    line3, = ax2.plot(df['Day'], work_in_progress, color='orange', linewidth=2,
             label='Tasks in progress (completed)')

    ax2.set_ylabel('Number of Tasks')

    # Title
    title = 'Simulation Results'
    if highlight_feature_id:
        title += f' (Highlighting {highlight_feature_id})'
    plt.title(title)

    # Custom Legend
    # We want:
    # Row 1: Lines (Cumulative, Rundown, WIP)
    # Row 2: Bars (SPEC, DEV, TEST, ROLLOUT) - Colors only / Primary
    
    # If highlighted, we could add a note about gray bars, but simplicity is better.
    
    handles = [
        legend_handles['SPEC'], legend_handles['DEV'], 
        legend_handles['TEST'], legend_handles['ROLLOUT'],
        line1, line2, line3
    ]
    labels = [
        'SPEC', 'DEV', 'TEST', 'ROLLOUT',
        'Tasks completed', 'Unfinished tasks', 'Tasks in progress'
    ]

    # Organize in columns
    # Reusing the previous nice layout 4 bars interleaved with spacers?
    # Previous layout was complex. Let's simplify.
    
    ax1.legend(
        handles,
        labels,
        ncol=4, # 4 columns
        loc="lower center",
        bbox_to_anchor=(0.5, -0.25), # Center below
        frameon=True,
        facecolor="white"
    )

    plt.subplots_adjust(bottom=0.20)
    plt.show()
