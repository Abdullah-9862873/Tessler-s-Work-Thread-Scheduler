"""
Core Allocation - Federated Scheduling
Based on Section III-C of the paper (Equation 5)

This module calculates how many processor cores are needed for tasks
under federated scheduling.
"""

import math
from typing import List, Tuple, Dict


def calculate_core_allocation(dag) -> int:
    """
    Calculate core allocation m_i for a DAG task (Equation 5).
    
    Formula: m_i = ⌈(C_i - L_i) / (D_i - L_i)⌉
    
    Where:
    - C_i = workload (sum of WCETs of all nodes)
    - L_i = critical path length (longest path through DAG)
    - D_i = deadline
    
    This is the KEY formula from the paper that we use to measure
    whether our collapse algorithm is working!
    
    Args:
        dag: DAG-OT task
    
    Returns:
        Number of cores required, or -1 if infeasible
    """
    workload = dag.workload()
    critical_path = dag.critical_path_length()
    deadline = dag.deadline
    
    # Check if task is infeasible (critical path exceeds deadline)
    if critical_path > deadline:
        return -1  # Infeasible - can't meet deadline
    
    # Calculate numerator and denominator
    numerator = workload - critical_path
    denominator = deadline - critical_path
    
    # Handle edge cases
    if denominator <= 0:
        # If denominator <= 0, either:
        # - L == D: single core needed (or zero)
        # - L > D: already caught above as infeasible
        if numerator <= 0:
            return 1  # Can execute on single core
        else:
            return 1  # Still needs 1 core, even if tight
    
    # Calculate core allocation
    cores = math.ceil(numerator / denominator)
    
    # Always return at least 1 core if feasible
    return max(1, cores)


def is_high_utilization(dag) -> bool:
    """
    Determine if task is high utilization (u_i > 1).
    
    From the paper:
    - High utilization tasks (u_i > 1): assigned dedicated cores
    - Low utilization tasks (u_i ≤ 1): scheduled on remaining cores
    
    This helps us decide how to schedule the task in a multi-core system.
    
    Args:
        dag: DAG-OT task
    
    Returns:
        True if high utilization (u_i > 1)
    """
    return dag.utilization() > 1.0


def separate_high_low_utilization(tasks: List) -> Tuple[List, List]:
    """
    Separate tasks into high and low utilization sets.
    
    This is part of federated scheduling - we handle high and low
    utilization tasks differently.
    
    Args:
        tasks: List of DAG-OT tasks
    
    Returns:
        Tuple of (high_utilization_tasks, low_utilization_tasks)
    """
    high_util = []
    low_util = []
    
    for task in tasks:
        if is_high_utilization(task):
            high_util.append(task)
        else:
            low_util.append(task)
    
    return high_util, low_util


def calculate_total_core_requirements(tasks: List) -> Dict:
    """
    Calculate total core requirements for a task set under federated scheduling.
    
    This tells us how many cores we need in total for a set of tasks,
    assuming federated scheduling.
    
    Args:
        tasks: List of DAG-OT tasks
    
    Returns:
        Dictionary with:
        - total_high_cores: Cores needed for high utilization tasks
        - high_tasks: List of high utilization tasks with their core allocations
        - low_tasks: List of low utilization tasks
        - infeasible: List of infeasible tasks
        - num_high, num_low, num_infeasible: Counts
    """
    high_util, low_util = separate_high_low_utilization(tasks)
    
    # Calculate cores for high utilization tasks
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
    
    # Low utilization tasks - just track them
    low_task_info = [{
        'task': task,
        'utilization': task.utilization()
    } for task in low_util]
    
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
    Check if core allocation improved (Definition 6).
    
    Definition 6 (Improved Core Allocation):
        m̂_i ≺ m_i if and only if:
        1. m_i > 0 ⇒ 0 < m̂_i ≤ m_i  (reduction)
        2. m_i ≤ 0 ⇒ m̂_i ≥ m_i     (infeasible becomes feasible)
    
    Note: m̂_i must be > 0 (positive) to be valid. Going to 0 cores means
    the task still can't run, so it's not an improvement.
    
    This is used in the collapse algorithm to check if collapsing
    actually helped!
    
    Args:
        original_cores: Original core allocation m_i
        new_cores: New core allocation m̂_i
    
    Returns:
        True if improved
    """
    if original_cores > 0:
        # Must be positive and not exceed original
        return 0 < new_cores <= original_cores
    else:
        # Original infeasible (<= 0), new must be positive AND greater
        return new_cores > 0 and new_cores > original_cores


class CoreAllocator:
    """
    Core allocator for federated scheduling.
    
    This class helps allocate cores to tasks in a multi-core system.
    """
    
    def __init__(self, total_cores: int):
        """
        Initialize core allocator.
        
        Args:
            total_cores: Total number of cores in the system
        """
        self.total_cores = total_cores
    
    def allocate(self, tasks: List) -> Dict:
        """
        Allocate cores to tasks using federated scheduling.
        
        Args:
            tasks: List of DAG-OT tasks
        
        Returns:
            Allocation results with feasibility information
        """
        core_info = calculate_total_core_requirements(tasks)
        
        # Check if feasible
        high_cores_needed = core_info['total_high_cores']
        
        if high_cores_needed > self.total_cores:
            return {
                'feasible': False,
                'reason': 'insufficient_cores',
                'needed': high_cores_needed,
                'available': self.total_cores,
                **core_info
            }
        
        # Calculate remaining cores for low utilization tasks
        remaining_cores = self.total_cores - high_cores_needed
        
        return {
            'feasible': True,
            'total_cores': self.total_cores,
            'high_util_cores': high_cores_needed,
            'low_util_cores': remaining_cores,
            **core_info
        }
    
    def reset(self):
        """Reset allocator state (for future use)."""
        pass