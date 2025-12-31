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
    # Create split view with enough height
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True, 
                                  gridspec_kw={'height_ratios': [1, 1]})

    # --- TOP CHART: GANTT VIEW ---
    
    # Get all stories and their completion data from the last snapshot
    final_stats = statistics[-1]
    all_story_ids = sorted(list(final_stats.task_completion_dates.keys()))
    
    # Define colors for phases
    phase_colors = {
        Phase.SPEC: 'lightblue',
        Phase.DEV: 'khaki',
        Phase.TEST: 'lightgreen',
        Phase.ROLLOUT: 'lightcoral'
    }
    
    # Track y-position for each story
    y_pos = 0
    y_ticks = []
    y_labels = []

    for story_id in all_story_ids:
        feature_id = final_stats.story_feature_map.get(story_id)
        is_target = (highlight_feature_id is None or 
                    feature_id == highlight_feature_id)
        
        # Add label for this story
        y_ticks.append(y_pos)
        y_labels.append(story_id)
        
        # Get completion events
        dates = final_stats.task_completion_dates[story_id]
        
        # Plot each finished task block
        for phase, day in dates["completed"]:
            color = phase_colors.get(phase, 'gray')
            alpha = 1.0 if is_target else 0.1
            
            # Plot a rectangle for the day
            # (day-1 to day, height 0.8 centered at y_pos)
            ax1.barh(y_pos, 1, left=day-1, height=0.8, 
                    color=color, alpha=alpha, edgecolor='none')
            
        y_pos += 1

    # Compact mode: Hide Y-ticks to save space
    ax1.set_yticks([]) 
    # ax1.set_yticklabels(y_labels, fontsize=8) # Disabled for compact view
    ax1.set_ylabel('User Stories (Compact)')
    ax1.set_title(f'User Story Progress (Highlighting: {highlight_feature_id if highlight_feature_id else "All"})')
    ax1.grid(True, axis='x', alpha=0.3)
    
    # Add simple legend for phases in Gantt
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=phase_colors[Phase.SPEC], label='SPEC'),
        Patch(facecolor=phase_colors[Phase.DEV], label='DEV'),
        Patch(facecolor=phase_colors[Phase.TEST], label='TEST'),
        Patch(facecolor=phase_colors[Phase.ROLLOUT], label='ROLLOUT'),
    ]
    ax1.legend(handles=legend_elements, loc='upper right', ncol=4, fontsize='small')


    # --- BOTTOM CHART: RESOURCE UTILIZATION ---
        
    # Initialize DataFrame data
    data = {
        'Day': [],
        'SPEC': [], 'SPEC_Other': [],
        'DEV': [], 'DEV_Other': [],
        'TEST': [], 'TEST_Other': [],
        'ROLLOUT': [], 'ROLLOUT_Other': [],
        'Cumulated': []
    }

    finished_tasks = get_finished_tasks_per_day(statistics)

    for stat in statistics:
        counts = {
            'SPEC': 0, 'SPEC_Other': 0,
            'DEV': 0, 'DEV_Other': 0,
            'TEST': 0, 'TEST_Other': 0,
            'ROLLOUT': 0, 'ROLLOUT_Other': 0
        }
        
        story_ids = stat.task_completion_dates.keys()
        for story_id in story_ids:
            feature_id = stat.story_feature_map.get(story_id)
            is_target = (highlight_feature_id is None or 
                        feature_id == highlight_feature_id)
            suffix = "" if is_target else "_Other"

            dates = stat.task_completion_dates[story_id]
            for phase, day in dates["completed"]:
                if day == stat.day:
                    key = f"{phase.name}{suffix}"
                    if key in counts:
                        counts[key] += 1
        
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

    # Convert counts to stacked bars
    stack_order = [
        ('SPEC_Other', 'SPEC (Other)'), ('SPEC', 'SPEC'),
        ('DEV_Other', 'DEV (Other)'), ('DEV', 'DEV'),
        ('TEST_Other', 'TEST (Other)'), ('TEST', 'TEST'),
        ('ROLLOUT_Other', 'ROLLOUT (Other)'), ('ROLLOUT', 'ROLLOUT')
    ]
    
    colors = {
        'SPEC': 'lightblue', 'SPEC_Other': 'lightblue',
        'DEV': 'khaki', 'DEV_Other': 'khaki',
        'TEST': 'lightgreen', 'TEST_Other': 'lightgreen',
        'ROLLOUT': 'lightcoral', 'ROLLOUT_Other': 'lightcoral'
    }

    bottom = pd.Series([0] * len(df))
    
    # Store handles for legend
    legend_handles = {}

    for col, label in stack_order:
        if highlight_feature_id is None and 'Other' in col:
            continue

        bars = ax2.bar(
            df['Day'], df[col],
            bottom=bottom,
            label=label if 'Other' not in col else None,
            color=colors[col],
            alpha=1.0 if 'Other' not in col else 0.2, # Stronger contrast: 1.0 vs 0.2
            width=1.0
        )
        bottom += df[col]
        
        if 'Other' not in col:
            legend_handles[col] = bars

    ax2.set_xlabel('Simulation Day')
    ax2.set_ylabel('Active Tasks (WIP)')
    ax2.grid(True, axis='y', alpha=0.3)
    ax2.set_title('Work In Progress (WIP)')
    
    # --- RESTORE CUMULATIVE LINES ---
    
    ax3 = ax2.twinx()
    
    # 1. Tasks Completed
    line1, = ax3.plot(df['Day'], df['Cumulated'], color='tab:blue', linewidth=2,
             label='Tasks completed')
             
    # 2. Remaining Tasks (Burndown)
    remaining_tasks = [total_tasks - ft for ft in finished_tasks]
    line2, = ax3.plot(
        df['Day'], remaining_tasks,
        color='red', linewidth=2,
        label='Burndown (Stories finished)'
    )
    
    # 3. Work in Progress
    work_in_progress = []
    for stat in statistics:
        completion_data = stat.get_daily_completion_stats()
        tasks_completed = completion_data['tasks_completed_cumulated']
        tasks_in_finished = sum(
            story.get_total_tasks()
            for story in stat.finished_work
        )
        work_in_progress.append(tasks_completed - tasks_in_finished)

    line3, = ax3.plot(df['Day'], work_in_progress, color='orange', linewidth=2,
             label='WIP (Tasks)')
             
    ax3.set_ylabel('Cumulative Tasks / WIP')
    
    # Combined Legend for Ax2/Ax3
    handles = [
        legend_elements[0], legend_elements[1], # SPEC, DEV
        legend_elements[2], legend_elements[3], # TEST, ROLLOUT
        line1, line2, line3
    ]
    labels = [
        'SPEC', 'DEV',
        'TEST', 'ROLLOUT',
        'Completed', 'Burndown', 'WIP'
    ]
    
    ax2.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.2),
              ncol=4)
    
    
    # --- SCROLLABLE WINDOW ---
    
    try:
        import tkinter as tk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

        root = tk.Tk()
        root.title("DevCycleSim Dashboard")
        root.geometry("1400x900") # Start with a reasonable window size

        # Create a canvas with scrollbars
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=1)

        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack gui elements
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Embed matplotlib figure
        canvas_agg = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas_agg.draw()
        canvas_agg.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas_agg, root)
        toolbar.update()
        # canvas_agg.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        root.mainloop()

    except ImportError:
        print("Warning: Tkinter/TkAgg not available. Falling back to standard plt.show() (non-scrollable).")
        plt.tight_layout()
        plt.show()
