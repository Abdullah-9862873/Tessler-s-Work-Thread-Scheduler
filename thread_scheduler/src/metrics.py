"""
Metrics Calculator
Based on Equations 16-19 of the paper

This module calculates metrics to measure the effectiveness of the collapse algorithm.
"""

from typing import Dict, List, Any, Optional


def calculate_core_savings(original_cores: int, collapsed_cores: int) -> float:
    """
    Calculate core savings from collapse.
    
    Δm = m_saved = m_i,high - m̂_i,high (Equation 16)
    
    Args:
        original_cores: Cores needed before collapse
        collapsed_cores: Cores needed after collapse
        
    Returns:
        Positive if cores saved, negative if more cores needed
    """
    return original_cores - collapsed_cores


def calculate_workload_reduction(original_workload: float, collapsed_workload: float) -> float:
    """
    Calculate workload reduction from collapse.
    
    ΔC = C_i - Ĉ_i (Equation 18)
    
    Args:
        original_workload: Workload before collapse
        collapsed_workload: Workload after collapse
        
    Returns:
        Positive if workload reduced, negative if increased
    """
    return original_workload - collapsed_workload


def calculate_path_extension(original_critical_path: float, collapsed_critical_path: float) -> float:
    """
    Calculate critical path extension from collapse.
    
    ΔL = L̂_i - L_i (Equation 19)
    
    Args:
        original_critical_path: Critical path before collapse
        collapsed_critical_path: Critical path after collapse
        
    Returns:
        Positive if path extended, negative if reduced
    """
    return collapsed_critical_path - original_critical_path


def calculate_schedulability_ratio(num_schedulable: int, total_tasks: int) -> float:
    """
    Calculate fraction of tasks that are schedulable.
    
    Args:
        num_schedulable: Number of tasks that can be scheduled
        total_tasks: Total number of tasks
        
    Returns:
        Fraction between 0 and 1
    """
    if total_tasks == 0:
        return 0.0
    return num_schedulable / total_tasks


def calculate_utilization_change(original_utilization: float, collapsed_utilization: float) -> float:
    """
    Calculate change in utilization.
    
    Args:
        original_utilization: Utilization before collapse
        collapsed_utilization: Utilization after collapse
        
    Returns:
        Change in utilization (negative = improvement)
    """
    return collapsed_utilization - original_utilization


def evaluate_task_before_after(task_before: Any, task_after: Any) -> Dict[str, Any]:
    """
    Evaluate single task metrics before/after collapse.
    
    Args:
        task_before: Task object before collapse
        task_after: Task object after collapse (or None if collapse failed)
        
    Returns:
        Dict with before, after, and savings metrics
    """
    result = {
        "before": {
            "workload": task_before.workload(),
            "critical_path": task_before.critical_path(),
            "utilization": task_before.utilization
        },
        "after": None,
        "savings": {}
    }
    
    if task_after is not None:
        result["after"] = {
            "workload": task_after.workload(),
            "critical_path": task_after.critical_path(),
            "utilization": task_after.utilization
        }
        
        result["savings"] = {
            "core_savings": calculate_core_savings(
                task_before.core_requirement if hasattr(task_before, 'core_requirement') else 1,
                task_after.core_requirement if hasattr(task_after, 'core_requirement') else 1
            ),
            "workload_reduction": calculate_workload_reduction(
                task_before.workload(),
                task_after.workload()
            ),
            "path_extension": calculate_path_extension(
                task_before.critical_path(),
                task_after.critical_path()
            ),
            "utilization_change": calculate_utilization_change(
                task_before.utilization,
                task_after.utilization
            )
        }
    else:
        result["savings"] = {
            "core_savings": 0,
            "workload_reduction": 0,
            "path_extension": 0,
            "utilization_change": 0
        }
    
    return result


def evaluate_task_set(tasks_before: List[Any], tasks_after: List[Any], 
                      heuristic: str = "unknown") -> Dict[str, Any]:
    """
    Aggregate metrics for entire task set.
    
    Args:
        tasks_before: List of tasks before collapse
        tasks_after: List of tasks after collapse
        heuristic: Name of heuristic used (OT-G, OT-L, OT-A)
        
    Returns:
        Aggregated results dictionary
    """
    num_tasks = len(tasks_before)
    if num_tasks == 0:
        return {
            "heuristic": heuristic,
            "num_tasks": 0,
            "total_original_cores": 0,
            "total_collapsed_cores": 0,
            "total_core_savings": 0,
            "avg_core_savings": 0,
            "total_workload_reduction": 0,
            "avg_workload_reduction": 0,
            "total_path_extension": 0,
            "avg_path_extension": 0,
            "schedulability_ratio": 0
        }
    
    total_original_workload = sum(t.workload() for t in tasks_before)
    total_collapsed_workload = sum(t.workload() for t in tasks_after) if all(t is not None for t in tasks_after) else total_original_workload
    
    total_original_critical_path = sum(t.critical_path() for t in tasks_before)
    total_collapsed_critical_path = sum(t.critical_path() for t in tasks_after) if all(t is not None for t in tasks_after) else total_original_critical_path
    
    schedulable_count = sum(1 for t in tasks_after if t is not None)
    
    result = {
        "heuristic": heuristic,
        "num_tasks": num_tasks,
        "total_original_workload": total_original_workload,
        "total_collapsed_workload": total_collapsed_workload,
        "total_workload_reduction": calculate_workload_reduction(
            total_original_workload, total_collapsed_workload
        ),
        "avg_workload_reduction": calculate_workload_reduction(
            total_original_workload, total_collapsed_workload
        ) / num_tasks,
        "total_path_extension": calculate_path_extension(
            total_original_critical_path, total_collapsed_critical_path
        ),
        "avg_path_extension": calculate_path_extension(
            total_original_critical_path, total_collapsed_critical_path
        ) / num_tasks,
        "schedulability_ratio": calculate_schedulability_ratio(
            schedulable_count, num_tasks
        )
    }
    
    return result


def compare_heuristics(task_sets_before: Dict[str, List[Any]], 
                       task_sets_after: Dict[str, List[Any]]) -> Dict[str, Any]:
    """
    Compare results across different heuristics (OT-G, OT-L, OT-A).
    
    Args:
        task_sets_before: Dict mapping heuristic name to list of tasks before
        task_sets_after: Dict mapping heuristic name to list of tasks after
        
    Returns:
        Comparison results with rankings
    """
    results = {}
    
    for heuristic in task_sets_before.keys():
        tasks_before = task_sets_before[heuristic]
        tasks_after = task_sets_after.get(heuristic, tasks_before)
        
        eval_result = evaluate_task_set(tasks_before, tasks_after, heuristic)
        results[heuristic] = eval_result
    
    sorted_by_savings = sorted(
        results.items(), 
        key=lambda x: x[1].get("total_workload_reduction", 0), 
        reverse=True
    )
    
    return {
        "results": results,
        "ranking": [h for h, _ in sorted_by_savings],
        "best_heuristic": sorted_by_savings[0][0] if sorted_by_savings else None
    }


class MetricsCalculator:
    """
    Class to track and compute metrics over multiple evaluations.
    
    Attributes:
        history: List to store evaluation results
    """
    
    def __init__(self):
        """Initialize the metrics calculator."""
        self.history: List[Dict[str, Any]] = []
    
    def add_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """
        Add a result to the history.
        
        Args:
            task_id: Identifier for the task
            result: Evaluation result dictionary
        """
        self.history.append({
            "task_id": task_id,
            "result": result
        })
    
    def compute_summary(self) -> Dict[str, Any]:
        """
        Compute summary statistics across all stored results.
        
        Returns:
            Summary dictionary with aggregate metrics
        """
        if not self.history:
            return {
                "num_evaluations": 0,
                "total_core_savings": 0,
                "total_workload_reduction": 0,
                "avg_core_savings": 0,
                "avg_workload_reduction": 0
            }
        
        total_core_savings = sum(
            h["result"].get("savings", {}).get("core_savings", 0) 
            for h in self.history
        )
        total_workload_reduction = sum(
            h["result"].get("savings", {}).get("workload_reduction", 0)
            for h in self.history
        )
        
        return {
            "num_evaluations": len(self.history),
            "total_core_savings": total_core_savings,
            "total_workload_reduction": total_workload_reduction,
            "avg_core_savings": total_core_savings / len(self.history),
            "avg_workload_reduction": total_workload_reduction / len(self.history)
        }
    
    def reset(self) -> None:
        """Clear all stored history."""
        self.history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the full evaluation history.
        
        Returns:
            List of stored evaluations
        """
        return self.history