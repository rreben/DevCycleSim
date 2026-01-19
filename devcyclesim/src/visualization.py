import matplotlib
try:
    matplotlib.use('TkAgg')
except ImportError:
    pass

import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Optional
from .process_statistic import ProcessStatistic
from .user_story import Phase


def get_finished_tasks_per_day(
        statistics: List[ProcessStatistic]) -> List[int]:
    """Calculates the cumulative number of tasks in finished stories per day.
    
    For Burndown, we track VALUE (original tasks), not Effort (correction tasks).
    So we use get_value_tasks_count().

    Args:
        statistics: List of ProcessStatistic objects

    Returns:
        List of integers with number of tasks in finished stories per day
    """
    finished_tasks = []

    for stat in statistics:
        # Sum up tasks in all finished stories for this day
        # Only count VALUE tasks for Burndown
        tasks_in_finished_stories = sum(
            story.get_value_tasks_count()
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
    
    # Calculate Effort Spent vs Value
    # Last day stats has 'tasks_finished_cumulated' which is essentially the Value sum of all finished stories
    last_day_stats = statistics[-1].get_daily_completion_stats()
    total_value_tasks = last_day_stats['tasks_finished_cumulated']

    # Calculate finished tasks per day (Value-based)
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
            for phase, day, is_corr in dates["completed"]:
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
        # Cumulated tracks Effort (Total Tasks Done)
        data['Cumulated'].append(completion_data['tasks_completed_cumulated'])

    df = pd.DataFrame(data)

    import numpy as np
    from matplotlib.colors import ListedColormap, BoundaryNorm

    # Create split view with enough height
    # 3 Subplots: Gantt (Top), Heatmap (Middle), WIP (Bottom)
    # Reduced middle ratio from 0.8 to 0.4 for a slimmer look
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True, 
                                  gridspec_kw={'height_ratios': [2, 0.4, 2]})

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
    
    # Rework Colors (Pink/Red shades)
    rework_colors = {
        Phase.SPEC: '#E6E6FA',    # Lavender (Pale Pinkish)
        Phase.DEV: '#FFB6C1',     # LightPink
        Phase.TEST: '#FF69B4',    # HotPink
        Phase.ROLLOUT: '#DC143C'  # Crimson
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
        for phase, day, is_corr in dates["completed"]:
            base_color = rework_colors.get(phase, 'red') if is_corr else phase_colors.get(phase, 'gray')
            color = base_color
            alpha = 1.0 if is_target else 0.1
            
            # Plot a rectangle for the day
            # (day-0.5 to day+0.5, height 0.8 centered at y_pos)
            ax1.barh(y_pos, 1, left=day-0.5, height=0.8, 
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
    legend_elements = []
    
    # 1. Row: Normal Phases
    for p in [Phase.SPEC, Phase.DEV, Phase.TEST, Phase.ROLLOUT]:
        legend_elements.append(Patch(facecolor=phase_colors[p], label=p.name))

    # 2. Row: Correction Phases
    for p in [Phase.SPEC, Phase.DEV, Phase.TEST, Phase.ROLLOUT]:
        legend_elements.append(Patch(facecolor=rework_colors[p], label=f"{p.name} (Corr)"))

    ax1.legend(handles=legend_elements, loc='upper right', ncol=4, fontsize='small')


    # --- DATA COLLECTION FOR HEATMAP AND BOTTOM CHART ---
    
    # We'll collect all data in one pass to ensure consistency between Heatmap and WIP chart
    
    num_days = len(statistics)
    heatmap_data = np.zeros((5, num_days))
    
    # Prepare keys for daily_counts and wip_data
    # We need: PHASE, PHASE_Corr, PHASE_Other, PHASE_Corr_Other
    phases = [Phase.SPEC, Phase.DEV, Phase.TEST, Phase.ROLLOUT]
    keys = []
    for p in phases:
        keys.append(p.name)
        keys.append(f"{p.name}_Corr")
        keys.append(f"{p.name}_Other")
        keys.append(f"{p.name}_Corr_Other")

    # Initialize DataFrame data dict for Bottom Chart
    wip_data = {'Day': [], 'Cumulated': []}
    for k in keys:
        wip_data[k] = []

    finished_tasks = get_finished_tasks_per_day(statistics)

    for i, stat in enumerate(statistics):
        # 1. Calculate Daily Phase Counts (Work Done)
        daily_counts = {k: 0 for k in keys}
        
        # Aggregated counts for Heatmap (ignoring Feature split)
        heatmap_counts = {p: 0 for p in phases}
        
        story_ids = stat.task_completion_dates.keys()
        for story_id in story_ids:
            feature_id = stat.story_feature_map.get(story_id)
            is_target = (highlight_feature_id is None or 
                        feature_id == highlight_feature_id)
            suffix = "" if is_target else "_Other"

            dates = stat.task_completion_dates[story_id]
            for phase, day, is_corr in dates["completed"]:
                if day == stat.day:
                    # Update Bottom Chart Counts
                    # Construct key: PHASE[_Corr][_Other]
                    corr_part = "_Corr" if is_corr else ""
                    key = f"{phase.name}{corr_part}{suffix}"
                    
                    if key in daily_counts:
                        daily_counts[key] += 1
                    
                    # Update Heatmap Counts
                    heatmap_counts[phase] += 1
        
        # 2. Fill Heatmap Data (Utilization)
        def calc_util(processed_count, cap):
            return (processed_count / cap) if cap > 0 else 0.0

        u_spec = calc_util(heatmap_counts[Phase.SPEC], stat.spec_stats.capacity)
        u_dev = calc_util(heatmap_counts[Phase.DEV], stat.dev_stats.capacity)
        u_test = calc_util(heatmap_counts[Phase.TEST], stat.test_stats.capacity)
        u_roll = calc_util(heatmap_counts[Phase.ROLLOUT], stat.rollout_stats.capacity)
        
        # Total Util
        total_processed = sum(heatmap_counts.values())
        total_cap = (stat.spec_stats.capacity + stat.dev_stats.capacity +
                    stat.test_stats.capacity + stat.rollout_stats.capacity)
        u_total = calc_util(total_processed, total_cap)
        
        # Row 0 is Top
        heatmap_data[0, i] = u_total
        heatmap_data[1, i] = u_spec
        heatmap_data[2, i] = u_dev
        heatmap_data[3, i] = u_test
        heatmap_data[4, i] = u_roll

        # 3. Fill WIP DataFrame Data
        completion_data = stat.get_daily_completion_stats()
        wip_data['Day'].append(stat.day)
        wip_data['Cumulated'].append(completion_data['tasks_completed_cumulated'])
        for k in keys:
            wip_data[k].append(daily_counts[k])

    # --- PLOTTING HEATMAP (Ax2) ---
    
    # Define Colors
    cmap = ListedColormap(['#ffcccc', '#ffeb99', '#99ff99', '#33cc33'])
    bounds = [0.0, 0.6, 0.8, 1.0, 10.0] 
    norm = BoundaryNorm(bounds, cmap.N)
    
    im = ax2.imshow(heatmap_data, cmap=cmap, norm=norm, aspect='auto', interpolation='nearest',
                   extent=[statistics[0].day - 0.5, statistics[-1].day + 0.5, 4.5, -0.5])
    
    for y in [0.5, 1.5, 2.5, 3.5]:
        ax2.axhline(y=y, color='white', linewidth=3, zorder=10)
    
    ax2.set_yticks(np.arange(5))
    ax2.set_yticklabels(["Total", "SPEC", "DEV", "TEST", "ROLLOUT"])
    ax2.set_title("Resource Efficiency (Utilization)")
    ax2.grid(False)

    # --- PLOTTING WIP CHART (Ax3) ---
    df = pd.DataFrame(wip_data)

    # Stack Order: Other (Bottom) -> Normal -> Correction (Top)
    # Order: 
    # SPEC_Other, SPEC, SPEC_Corr_Other, SPEC_Corr
    # ...
    stack_order = []
    for p in phases:
        name = p.name
        stack_order.append( (f"{name}_Other", f"{name} (Other)") )
        stack_order.append( (f"{name}", f"{name}") )
        stack_order.append( (f"{name}_Corr_Other", f"{name} (Corr Other)") )
        stack_order.append( (f"{name}_Corr", f"{name} (Corr)") )
    
    # Define colors for all keys
    colors = {}
    for p in phases:
        name = p.name
        base_col = phase_colors[p]
        corr_col = rework_colors[p]
        
        colors[name] = base_col
        colors[f"{name}_Other"] = base_col
        colors[f"{name}_Corr"] = corr_col
        colors[f"{name}_Corr_Other"] = corr_col

    bottom = pd.Series([0] * len(df))
    
    legend_handles = {}

    for col, label in stack_order:
        if highlight_feature_id is None and 'Other' in col:
            continue

        # Logic to skip legend entries for 'Other' or duplicate Correction entries?
        # We want explicit legend for main phases and maybe ONE generic "Correction" 
        # or specific correction phases if we want full consistency.
        # User asked for "consistent colors".
        # Let's label them.
        
        # Determine alpha
        alpha = 1.0
        if 'Other' in col:
            alpha = 0.2
            
        # Determine label for Legend
        # We only want basic labels in legend to avoid clutter?
        # "SPEC", "DEV" ... and "Correction" (generic) or "SPEC (Corr)"?
        # User: "Farben für das Rework ... nicht auch konsistent verwendet"
        # Let's allow specific coloring.
        
        draw_label = None
        if 'Other' not in col:
            draw_label = label

        bars = ax3.bar(
            df['Day'], df[col],
            bottom=bottom,
            label=draw_label,
            color=colors[col],
            alpha=alpha,
            width=1.0
        )
        bottom += df[col]
        
        # Collect handles for cleaner custom legend
        # We only care about main phases + corrections
        if 'Other' not in col:
            legend_handles[col] = bars

    ax3.set_xlabel('Simulation Day')
    ax3.set_ylabel('Resources at work')
    ax3.grid(True, axis='y', alpha=0.3)
    ax3.set_title('Work In Progress (WIP)')
    
    # --- RESTORE CUMULATIVE LINES ---
    
    ax4 = ax3.twinx()
    
    # 1. Tasks Completed (EFFORT SPENT)
    line1, = ax4.plot(df['Day'], df['Cumulated'], color='tab:blue', linewidth=2,
             label='Effort Spent')
             
    # 2. Remaining Tasks (Burndown of VALUE)
    remaining_tasks = [total_value_tasks - ft for ft in finished_tasks]
    line2, = ax4.plot(
        df['Day'], remaining_tasks,
        color='red', linewidth=2,
        label='Burndown (Value)'
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

    line3, = ax4.plot(df['Day'], work_in_progress, color='orange', linewidth=2,
             label='WIP (Tasks)')
             
    ax4.set_ylabel('Cumulative Tasks / WIP')
    
    # Combined Legend
    # Top Row: Normal Phases
    # Bottom Row: Correction Phases?
    # Lines
    
    from matplotlib.lines import Line2D
    
    custom_handles = []
    custom_labels = []
    
    # row 1: Normal Phases
    for p in phases:
        custom_handles.append(Patch(facecolor=phase_colors[p], label=p.name))
        custom_labels.append(p.name)
        
    # row 2: Correction Phases
    for p in phases:
        custom_handles.append(Patch(facecolor=rework_colors[p], label=f"{p.name} (Corr)"))
        custom_labels.append(f"{p.name} (Corr)")
        
    # row 3: Lines
    custom_handles.extend([line1, line2, line3])
    custom_labels.extend(['Effort', 'Value', 'WIP'])
    
    # 4 columns? 4 phases...
    # Layout:
    # S, D, T, R
    # Sc, Dc, Tc, Rc
    # Eff, Val, WIP
    
    ax3.legend(custom_handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.25),
              ncol=4, fontsize='small')
    
    
    # --- SCROLLABLE WINDOW ---
    
    try:
        import tkinter as tk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        
        root = tk.Tk()
        # ... rest of the function remains same ...
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
        
        def on_closing():
            plt.close(fig) # Close matplotlib figure to free resources
            root.quit()    # Stop mainloop
            root.destroy() # Destroy window

        root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()

    except ImportError as e:
        print(f"Warning: Tkinter/TkAgg not available. Error: {e}")
        print("Falling back to standard plt.show() (non-scrollable).")
        plt.tight_layout()
        plt.show()
