from dataclasses import dataclass, field
from devcyclesim.src.process_step import ProcessStep
from devcyclesim.src.user_story import Phase
import numpy as np


@dataclass
class StepStatistic:
    """
    Statistics for a single process step.

    Args:
        input_queue_count: Number of stories in input queue
        work_in_progress_count: Number of stories in work in progress
        done_count: Number of stories in done queue
        capacity: Current capacity of the process step
    """
    input_queue_count: int
    work_in_progress_count: int
    done_count: int
    capacity: int

    @classmethod
    def from_process_step(cls, step: ProcessStep) -> 'StepStatistic':
        """
        Creates a StepStatistic from a ProcessStep.

        Args:
            step: The process step to create statistics from

        Returns:
            StepStatistic containing the current counts
        """
        return cls(
            input_queue_count=step.count_input_queue(),
            work_in_progress_count=step.count_work_in_progress(),
            done_count=step.count_done(),
            capacity=step.capacity
        )


@dataclass
class ProcessStatistic:
    """
    Statistics for the entire process at a specific point in time.

    Args:
        day: Current simulation day
        backlog_count: Number of stories in backlog
        finished_work_count: Number of completed stories
        finished_work: Array of completed stories
        spec_stats: Statistics for SPEC step
        dev_stats: Statistics for DEV step
        test_stats: Statistics for TEST step
        rollout_stats: Statistics for ROLLOUT step
        task_completion_dates: Dictionary mapping story
        IDs to their task completion dates
    """
    day: int
    backlog_count: int
    finished_work_count: int
    finished_work: np.ndarray
    spec_stats: StepStatistic
    dev_stats: StepStatistic
    test_stats: StepStatistic
    rollout_stats: StepStatistic
    task_completion_dates: (
        "dict[str, dict[str, list[tuple[Phase, int]]]]"
    ) = field(default_factory=dict)

    @classmethod
    def from_process(cls, process, day: int) -> 'ProcessStatistic':
        """
        Creates a ProcessStatistic from a Process instance.

        Args:
            process: The process to create statistics from
            day: Current simulation day

        Returns:
            ProcessStatistic containing the current state
        """
        # Collect task completion dates for all stories
        task_completion_dates = {}

        # Collect from backlog
        for story in process.backlog:
            task_completion_dates[story.story_id] = (
                story.get_task_completion_dates())

        # Collect from all process steps
        for step in [
            process.spec_step, process.dev_step,
                process.test_step, process.rollout_step]:
            # From input queue
            for story in step.input_queue:
                task_completion_dates[story.story_id] = (
                    story.get_task_completion_dates())
            # From work in progress
            for story in step.work_in_progress:
                task_completion_dates[story.story_id] = (
                    story.get_task_completion_dates())
            # From done queue
            for story in step.done:
                task_completion_dates[story.story_id] = (
                    story.get_task_completion_dates())

        # Collect from finished work
        for story in process.finished_work:
            task_completion_dates[story.story_id] = (
                story.get_task_completion_dates())

        return cls(
            day=day,
            backlog_count=len(process.backlog),
            finished_work_count=len(process.finished_work),
            finished_work=process.finished_work,
            spec_stats=StepStatistic.from_process_step(process.spec_step),
            dev_stats=StepStatistic.from_process_step(process.dev_step),
            test_stats=StepStatistic.from_process_step(process.test_step),
            rollout_stats=StepStatistic.from_process_step(
                process.rollout_step),
            task_completion_dates=task_completion_dates
        )

    def print_statistics(self) -> None:
        """
        Prints a formatted overview of the current process statistics.
        Shows the number of stories in each queue, the capacity for each step,
        and task completion dates.
        """
        print(f"\nProcess Statistics - Day {self.day}")
        print("-" * 50)
        print(f"Backlog: {self.backlog_count} stories")
        print(f"Finished Work: {self.finished_work_count} stories")
        print("\nProcess Steps:")
        print("-" * 50)

        steps = {
            "SPEC": self.spec_stats,
            "DEV": self.dev_stats,
            "TEST": self.test_stats,
            "ROLLOUT": self.rollout_stats
        }

        for step_name, stats in steps.items():
            print(f"\n{step_name}:")
            print(f"  Capacity: {stats.capacity}")
            print(f"  Input Queue: {stats.input_queue_count}")
            print(f"  In Progress: {stats.work_in_progress_count}")
            print(f"  Done: {stats.done_count}")

            # Calculate utilization as percentage
            if stats.capacity > 0:
                utilization = (
                    stats.work_in_progress_count
                    / stats.capacity
                    * 100
                )
                print(f"  Utilization: {utilization:.1f}%")

        if self.task_completion_dates:
            print("\nTask Completion Dates:")
            print("-" * 50)
            for story_id, completion_info in (
                self.task_completion_dates.items()
            ):
                print(f"\nStory {story_id}:")
                if completion_info["completed"]:
                    print("  Completed Tasks:")
                    for phase, day in completion_info["completed"]:
                        print(f"    {phase.name}: Day {day}")
                if completion_info["pending"]:
                    print("  Pending Tasks:")
                    for phase, _ in completion_info["pending"]:
                        print(f"    {phase.name}: Not completed")

    def get_csv_header(self) -> str:
        """
        Returns the CSV header for the statistics.

        Returns:
            str: CSV header line
        """
        return (
            "Day,Backlog,Finished,"
            "SPEC_Input,SPEC_InProgress,SPEC_Done,SPEC_Capacity,"
            "DEV_Input,DEV_InProgress,DEV_Done,DEV_Capacity,"
            "TEST_Input,TEST_InProgress,TEST_Done,TEST_Capacity,"
            "ROLLOUT_Input,ROLLOUT_InProgress,ROLLOUT_Done,ROLLOUT_Capacity"
        )

    def get_csv_line(self) -> str:
        """
        Returns the statistics as CSV line.

        Returns:
            str: CSV data line
        """
        return (
            f"{self.day:3},"
            f"{self.backlog_count:1},"
            f"{self.finished_work_count:1},"
            f"{self.spec_stats.input_queue_count:1},"
            f"{self.spec_stats.work_in_progress_count:1},"
            f"{self.spec_stats.done_count:1},"
            f"{self.spec_stats.capacity:1},"
            f"{self.dev_stats.input_queue_count:1},"
            f"{self.dev_stats.work_in_progress_count:1},"
            f"{self.dev_stats.done_count:1},"
            f"{self.dev_stats.capacity:1},"
            f"{self.test_stats.input_queue_count:1},"
            f"{self.test_stats.work_in_progress_count:1},"
            f"{self.test_stats.done_count:1},"
            f"{self.test_stats.capacity:1},"
            f"{self.rollout_stats.input_queue_count:1},"
            f"{self.rollout_stats.work_in_progress_count:1},"
            f"{self.rollout_stats.done_count:1},"
            f"{self.rollout_stats.capacity:1}"
        )

    def get_task_completion_csv_header(self) -> str:
        """
        Returns the CSV header for task completion summary.
        Contains story_ids of all stories that have been processed.

        Returns:
            str: CSV header line for task completion summary
        """
        # Get all story IDs from the process
        story_ids = []
        for story_id in self.task_completion_dates.keys():
            if story_id not in story_ids:
                story_ids.append(story_id)
        return "Day," + ",".join(sorted(story_ids))

    def get_task_completion_csv_line(self) -> str:
        """
        Returns a CSV line indicating which stories had task completions
        on the current day.

        Returns:
            str: CSV line with 1 for task completions, 0 otherwise
        """
        story_ids = sorted(self.task_completion_dates.keys())
        completions = []

        for story_id in story_ids:
            # Get completion dates for this story
            dates = self.task_completion_dates[story_id]
            # Check if any task was completed on this day
            completed_today = any(
                day == self.day
                for _, day in dates["completed"]
            )
            # Check if story has any completed tasks before or on this day
            has_started = any(
                day <= self.day
                for _, day in dates["completed"]
            )
            # Output:
            # - "1" if a task was completed today
            # - "0" if story has started but no task completed today
            # - "" (empty) if story hasn't started yet
            if completed_today:
                completions.append("1")
            elif has_started:
                completions.append("0")
            else:
                completions.append(" ")

        return f"{self.day:3}," + ",".join(completions)

    def get_task_completion_history_header(self) -> str:
        """
        Returns the CSV header for task completion history.
        Shows the type of completed tasks:
        S: Specification, D: Development, T: Testing, R: Rollout

        Returns:
            str: CSV header line for task completion history
        """
        story_ids = sorted(self.task_completion_dates.keys())
        capacity_headers = [
            "SPEC_Capacity",
            "DEV_Capacity",
            "TEST_Capacity",
            "ROLLOUT_Capacity"
        ]
        completed_headers = [
            "SPEC_completed",
            "DEV_completed",
            "TEST_completed",
            "ROLLOUT_completed"
        ]
        summary_headers = [
            "Stories_finished",
            "Tasks_completed_cumulated",
            "Tasks_finished_cumulated"
        ]
        all_headers = capacity_headers + completed_headers + summary_headers
        return f"Day,{','.join(all_headers)}," + ",".join(story_ids)

    def get_task_completion_history_line(self) -> str:
        """
        Returns a CSV line with task type indicators:
        S: Specification task completed
        D: Development task completed
        T: Testing task completed
        R: Rollout task completed
        ' ': No task completed today
        ' ': Story not started yet

        Returns:
            str: CSV line with task type indicators
        """
        story_ids = sorted(self.task_completion_dates.keys())
        completions = []

        # Add capacities with 2-digit width
        capacities = [
            f"{self.spec_stats.capacity:2}",
            f"{self.dev_stats.capacity:2}",
            f"{self.test_stats.capacity:2}",
            f"{self.rollout_stats.capacity:2}"
        ]

        # Process all stories first to collect completions
        for story_id in story_ids:
            # Get completion dates for this story
            dates = self.task_completion_dates[story_id]
            # Check which task was completed on this day
            task_completed_today = None
            for phase, day in dates["completed"]:
                if day == self.day:
                    task_completed_today = phase
                    break

            # Output the appropriate indicator
            if task_completed_today:
                if task_completed_today == Phase.SPEC:
                    completions.append("S")
                elif task_completed_today == Phase.DEV:
                    completions.append("D")
                elif task_completed_today == Phase.TEST:
                    completions.append("T")
                elif task_completed_today == Phase.ROLLOUT:
                    completions.append("R")
            else:
                completions.append(" ")

        # Count completions per phase
        spec_completed = str(completions.count("S")).rjust(2)
        dev_completed = str(completions.count("D")).rjust(2)
        test_completed = str(completions.count("T")).rjust(2)
        rollout_completed = str(completions.count("R")).rjust(2)

        completed_counts = [
            spec_completed,
            dev_completed,
            test_completed,
            rollout_completed
        ]

        # Count all completed tasks (including partially finished stories)
        tasks_completed = 0
        for dates in self.task_completion_dates.values():
            story_tasks = dates["completed"]
            if story_tasks:
                last_task_day = max(day for _, day in story_tasks)
                if last_task_day <= self.day:
                    tasks_completed += len(story_tasks)

        # Count tasks of finished stories by getting total tasks directly
        tasks_finished = sum(
            story.get_total_tasks()
            for story in self.finished_work
        )

        summary_counts = [
            str(self.finished_work_count).rjust(3),  # 3-stellig für Stories
            str(tasks_completed).rjust(4),  # 4-stellig für Tasks
            str(tasks_finished).rjust(4)  # 4-stellig für Tasks
        ]

        # Combine all parts
        parts = [f"{self.day:3}"]
        parts.extend(capacities)
        parts.extend(completed_counts)
        parts.extend(summary_counts)
        parts.extend(completions)
        return ",".join(parts)

    def get_daily_completion_stats(self) -> dict:
        """
        Returns structured statistics about task completion for this day.
        
        Returns:
            dict: Dictionary containing:
                - spec_completed: int
                - dev_completed: int
                - test_completed: int
                - rollout_completed: int
                - tasks_completed_cumulated: int
                - tasks_finished_cumulated: int
        """
        story_ids = sorted(self.task_completion_dates.keys())
        completions = []

        # Process all stories to collect completions for this day
        for story_id in story_ids:
            dates = self.task_completion_dates[story_id]
            task_completed_today = None
            for phase, day in dates["completed"]:
                if day == self.day:
                    task_completed_today = phase
                    break
            
            if task_completed_today:
                completions.append(task_completed_today)

        # Count completions per phase
        spec_completed = completions.count(Phase.SPEC)
        dev_completed = completions.count(Phase.DEV)
        test_completed = completions.count(Phase.TEST)
        rollout_completed = completions.count(Phase.ROLLOUT)

        # Count all completed tasks (including partially finished stories)
        tasks_completed = 0
        for dates in self.task_completion_dates.values():
            story_tasks = dates["completed"]
            if story_tasks:
                last_task_day = max(day for _, day in story_tasks)
                if last_task_day <= self.day:
                    tasks_completed += len(story_tasks)

        # Count tasks of finished stories
        tasks_finished = sum(
            story.get_total_tasks()
            for story in self.finished_work
        )

        return {
            "spec_completed": spec_completed,
            "dev_completed": dev_completed,
            "test_completed": test_completed,
            "rollout_completed": rollout_completed,
            "tasks_completed_cumulated": tasks_completed,
            "tasks_finished_cumulated": tasks_finished
        }
