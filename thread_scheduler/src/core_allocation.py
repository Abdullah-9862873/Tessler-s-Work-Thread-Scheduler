"""
Core Allocation — Federated Scheduling (Eq. 5)
m_i = ceil((C_i - L_i) / (D_i - L_i))
"""

import math
from typing import List, Tuple, Dict


def calculate_core_allocation(dag) -> int:
    """
    Core allocation for a DAG task under federated scheduling.
    Returns -1 if the task is infeasible (critical path > deadline).
    """
    workload = dag.workload()
    critical_path = dag.critical_path_length()
    deadline = dag.deadline

    if critical_path > deadline:
        return -1

    numerator = workload - critical_path
    denominator = deadline - critical_path

    if denominator <= 0:
        return 1

    return max(1, math.ceil(numerator / denominator))


def is_high_utilization(dag) -> bool:
    """True if u_i > 1 (task needs dedicated cores)."""
    return dag.utilization() > 1.0


def separate_high_low_utilization(tasks: List) -> Tuple[List, List]:
    """Split tasks into high-utilization (u > 1) and low-utilization sets."""
    high, low = [], []
    for task in tasks:
        (high if is_high_utilization(task) else low).append(task)
    return high, low


def calculate_total_core_requirements(tasks: List) -> Dict:
    """Aggregate core requirements across a task set."""
    high_util, low_util = separate_high_low_utilization(tasks)

    total_high_cores = 0
    high_task_info = []
    infeasible = []

    for task in high_util:
        cores = calculate_core_allocation(task)
        if cores == -1:
            infeasible.append((task.task_id, "critical_path_exceeds_deadline"))
        else:
            total_high_cores += cores
            high_task_info.append({
                'task': task,
                'cores': cores,
                'utilization': task.utilization()
            })

    low_task_info = [{'task': t, 'utilization': t.utilization()} for t in low_util]

    return {
        'total_high_cores': total_high_cores,
        'high_tasks': high_task_info,
        'low_tasks': low_task_info,
        'infeasible': infeasible,
        'num_high': len(high_task_info),
        'num_low': len(low_task_info),
        'num_infeasible': len(infeasible)
    }


def check_improved_core_allocation(original_cores: int, new_cores: int) -> bool:
    """
    Definition 6: m_hat precedes m iff the new allocation is
    no worse and still positive.
    """
    if original_cores > 0:
        return 0 < new_cores <= original_cores
    else:
        return new_cores > 0 and new_cores > original_cores


class CoreAllocator:
    """Allocates cores to tasks using federated scheduling."""

    def __init__(self, total_cores: int):
        self.total_cores = total_cores

    def allocate(self, tasks: List) -> Dict:
        core_info = calculate_total_core_requirements(tasks)
        high_cores_needed = core_info['total_high_cores']

        if high_cores_needed > self.total_cores:
            return {
                'feasible': False,
                'reason': 'insufficient_cores',
                'needed': high_cores_needed,
                'available': self.total_cores,
                **core_info
            }

        remaining = self.total_cores - high_cores_needed
        return {
            'feasible': True,
            'total_cores': self.total_cores,
            'high_util_cores': high_cores_needed,
            'low_util_cores': remaining,
            **core_info
        }

    def reset(self):
        pass