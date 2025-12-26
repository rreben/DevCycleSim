import pytest
from unittest.mock import MagicMock, patch
from devcyclesim.src.process_statistic import ProcessStatistic
from devcyclesim.src.user_story import UserStory, Phase
from devcyclesim.src.visualization import plot_simulation_results
import numpy as np

def test_process_statistic_story_feature_map():
    """
    Test that ProcessStatistic correctly builds the story_feature_map.
    """
    # Create mock process
    process = MagicMock()
    
    # Story 1: Feature A
    s1 = MagicMock(spec=UserStory)
    s1.story_id = "S1"
    s1.feature_id = "FeatureA"
    s1.get_task_completion_dates.return_value = {"completed": [], "pending": []}
    
    # Story 2: Feature B
    s2 = MagicMock(spec=UserStory)
    s2.story_id = "S2"
    s2.feature_id = "FeatureB"
    s2.get_task_completion_dates.return_value = {"completed": [], "pending": []}
    
    process.backlog = [s1]
    process.spec_step.input_queue = [s2]
    process.spec_step.work_in_progress = []
    process.spec_step.done = []
    # Simplified other steps
    for step in [process.dev_step, process.test_step, process.rollout_step]:
        step.input_queue = []
        step.work_in_progress = []
        step.done = []
        # Mock capacity for StepStatistic
        step.capacity = 1
        step.count_input_queue.return_value = 0
        step.count_work_in_progress.return_value = 0
        step.count_done.return_value = 0
    process.spec_step.capacity = 1
    process.spec_step.count_input_queue.return_value = 1  # s2
    
    process.finished_work = []
    
    # Create statistics
    stat = ProcessStatistic.from_process(process, day=1)
    
    # Verify map
    assert "S1" in stat.story_feature_map
    assert stat.story_feature_map["S1"] == "FeatureA"
    assert "S2" in stat.story_feature_map
    assert stat.story_feature_map["S2"] == "FeatureB"

def test_plot_simulation_results_splits_data():
    """
    Test that plot_simulation_results logic splits data into proper buckets.
    Since we cannot easily check the internal variables of the function,
    we will rely on mocking ax.bar and checking the data passed to it.
    """
    # Mock Statistic
    stat = MagicMock(spec=ProcessStatistic)
    stat.day = 1
    stat.story_feature_map = {
        "S1": "FeatureA",
        "S2": "FeatureB"
    }
    # S1 (FeatureA) completed SPEC on day 1
    # S2 (FeatureB) completed SPEC on day 1
    stat.task_completion_dates = {
        "S1": {"completed": [(Phase.SPEC, 1)], "pending": []},
        "S2": {"completed": [(Phase.SPEC, 1)], "pending": []}
    }
    # Mock cumulative stats
    stat.get_daily_completion_stats.return_value = {
        "tasks_completed_cumulated": 2,
        "tasks_finished_cumulated": 0
    }
    stat.finished_work = []
    
    statistics = [stat]
    
    # Patch plt
    with patch('matplotlib.pyplot.show'), \
         patch('matplotlib.pyplot.subplots') as mock_subplots:
         
        mock_fig = MagicMock()
        mock_ax1 = MagicMock()
        mock_ax2 = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax1)
        mock_ax1.twinx.return_value = mock_ax2
        
        # Configure plot returns to support unpacking "line, = ax.plot()"
        mock_ax2.plot.return_value = [MagicMock()]

        # We need to ensure get_legend_handles_labels returns enough dummy items
        # The code expects 4 bars handles? No, now it iterates stack_order
        # and collects handles.
        # But at the end it calls get_legend_handles_labels() on ax1 and ax2
        mock_ax1.get_legend_handles_labels.return_value = ([], []) 
        mock_ax2.get_legend_handles_labels.return_value = ([], [])

        # Call with highlighting FeatureA
        # S1 is FeatureA -> SPEC (Focus)
        # S2 is FeatureB -> SPEC_Other
        plot_simulation_results(statistics, highlight_feature_id="FeatureA")
        
        # Check ax1.bar calls
        # We expect separate calls for 'SPEC' and 'SPEC_Other'
        # Data passed to bar is the sequence of values.
        # We need to capture the calls and inspect the data.
        
        # Collect all calls to bar
        bar_calls = mock_ax1.bar.call_args_list
        
        # We expect calls for:
        # SPEC_Other (count=1 for day 1)
        # SPEC (count=1 for day 1)
        # Other phases 0
        
        found_spec_focus = False
        found_spec_other = False
        
        for call in bar_calls:
            args, kwargs = call
            # args[0] is x (day), args[1] is heights
            heights = args[1]
            label = kwargs.get('label')
            
            # Note: The function labels 'SPEC' but passes None for 'SPEC_Other'
            # We can check the data
            if label == 'SPEC': 
                # This should be the Focus bar
                if heights[0] == 1:
                    found_spec_focus = True
            elif label is None and kwargs.get('color') == '#E0E0E0':
                # This is likely SPEC_Other
                 if heights[0] == 1:
                    found_spec_other = True

        assert found_spec_focus, "Did not find SPEC focus bar with height 1"
        assert found_spec_other, "Did not find SPEC_Other bar with height 1"
