import pytest
from unittest.mock import MagicMock, patch
from devcyclesim.src.process_statistic import ProcessStatistic
from devcyclesim.src.user_story import Phase
from devcyclesim.src.visualization import plot_simulation_results

def test_get_daily_completion_stats():
    """
    Test that get_daily_completion_stats returns the correct structure and values.
    """
    # Mock ProcessStatistic
    stat = MagicMock(spec=ProcessStatistic)
    stat.day = 5
    stat.finished_work = []
    
    # Mock task_completion_dates
    # Story 1: SPEC done on day 5
    # Story 2: DEV done on day 5
    # Story 3: TEST done on day 4 (not today)
    stat.task_completion_dates = {
        "STORY-1": {
            "completed": [(Phase.SPEC, 5)],
            "pending": []
        },
        "STORY-2": {
            "completed": [(Phase.SPEC, 3), (Phase.DEV, 5)],
            "pending": []
        },
        "STORY-3": {
            "completed": [(Phase.SPEC, 2), (Phase.DEV, 3), (Phase.TEST, 4)],
            "pending": []
        }
    }
    
    # Bind the real method to the mock object
    stat.get_daily_completion_stats = ProcessStatistic.get_daily_completion_stats.__get__(stat, ProcessStatistic)
    
    stats = stat.get_daily_completion_stats()
    
    assert stats["spec_completed"] == 1  # STORY-1
    assert stats["dev_completed"] == 1   # STORY-2
    assert stats["test_completed"] == 0  # STORY-3 finished TEST yesterday
    assert stats["rollout_completed"] == 0
    
    # Check cumulative tasks
    # STORY-1: 1 task
    # STORY-2: 2 tasks
    # STORY-3: 3 tasks
    # Total: 6
    assert stats["tasks_completed_cumulated"] == 6

def test_plot_simulation_results_calls_new_method():
    """
    Test that plot_simulation_results calls get_daily_completion_stats
    instead of parsing CSV strings.
    """
    # Create mock statistics
    stat1 = MagicMock(spec=ProcessStatistic)
    stat1.day = 1
    stat1.get_daily_completion_stats.return_value = {
        "spec_completed": 1,
        "dev_completed": 0,
        "test_completed": 0,
        "rollout_completed": 0,
        "tasks_completed_cumulated": 1,
        "tasks_finished_cumulated": 0
    }
    stat1.task_completion_dates = {}
    stat1.story_feature_map = {}
    # Mock finished_work for get_finished_tasks_per_day
    stat1.finished_work = []
    
    stat2 = MagicMock(spec=ProcessStatistic)
    stat2.day = 2
    stat2.get_daily_completion_stats.return_value = {
        "spec_completed": 0,
        "dev_completed": 1,
        "test_completed": 0,
        "rollout_completed": 0,
        "tasks_completed_cumulated": 2,
        "tasks_finished_cumulated": 0
    }
    stat2.task_completion_dates = {}
    stat2.story_feature_map = {}
    stat2.finished_work = []
    
    statistics = [stat1, stat2]
    
    # Patch matplotlib.pyplot to avoid showing the plot
    with patch('matplotlib.pyplot.show'), \
         patch('matplotlib.pyplot.subplots') as mock_subplots:
        
        # Configure mock figure and axes
        mock_fig = MagicMock()
        mock_ax1 = MagicMock()
        mock_ax2 = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax1)
        mock_ax1.twinx.return_value = mock_ax2
        
        # Configure plot return for unpacking
        mock_ax2.plot.return_value = [MagicMock()]

        # Configure legend handles to avoid unpacking errors
        mock_ax1.get_legend_handles_labels.return_value = (
            [MagicMock(), MagicMock(), MagicMock(), MagicMock()], 
            ["SPEC", "DEV", "TEST", "ROLLOUT"]
        )
        mock_ax2.get_legend_handles_labels.return_value = (
            [MagicMock(), MagicMock(), MagicMock()],
            ["Line1", "Line2", "Line3"]
        )
        
        plot_simulation_results(statistics)
        
        # Verify that the new method was called
        stat1.get_daily_completion_stats.assert_called()
        stat2.get_daily_completion_stats.assert_called()
        
        # Verify that the old method was NOT called
        stat1.get_task_completion_history_line.assert_not_called()
