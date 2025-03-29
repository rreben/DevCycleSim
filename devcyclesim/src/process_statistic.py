from dataclasses import dataclass
from devcyclesim.src.process_step import ProcessStep


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
        spec_stats: Statistics for SPEC step
        dev_stats: Statistics for DEV step
        test_stats: Statistics for TEST step
        rollout_stats: Statistics for ROLLOUT step
    """
    day: int
    backlog_count: int
    finished_work_count: int
    spec_stats: StepStatistic
    dev_stats: StepStatistic
    test_stats: StepStatistic
    rollout_stats: StepStatistic

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
        return cls(
            day=day,
            backlog_count=len(process.backlog),
            finished_work_count=len(process.finished_work),
            spec_stats=StepStatistic.from_process_step(process.spec_step),
            dev_stats=StepStatistic.from_process_step(process.dev_step),
            test_stats=StepStatistic.from_process_step(process.test_step),
            rollout_stats=StepStatistic.from_process_step(process.rollout_step)
        )

    def print_statistics(self) -> None:
        """
        Prints a formatted overview of the current process statistics.
        Shows the number of stories in each queue
        and the capacity for each step.
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
