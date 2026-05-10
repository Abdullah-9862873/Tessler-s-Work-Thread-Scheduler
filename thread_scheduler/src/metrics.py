"""
Metrics — Equations 16-19.
ΔC, ΔL, Δm calculations for evaluating the collapse algorithm.
"""

from typing import Dict, List, Any, Optional


def calculate_core_savings(original_cores: int, collapsed_cores: int) -> float:
    """Δm = m_original - m_collapsed (Eq. 16)."""
    return original_cores - collapsed_cores


def calculate_workload_reduction(original_workload: float, collapsed_workload: float) -> float:
    """ΔC = C_i - C_hat_i (Eq. 18)."""
    return original_workload - collapsed_workload


def calculate_path_extension(original_critical_path: float, collapsed_critical_path: float) -> float:
    """ΔL = L_hat_i - L_i (Eq. 19)."""
    return collapsed_critical_path - original_critical_path


def calculate_schedulability_ratio(num_schedulable: int, total_tasks: int) -> float:
    if total_tasks == 0:
        return 0.0
    return num_schedulable / total_tasks


def calculate_utilization_change(original_utilization: float, collapsed_utilization: float) -> float:
    return collapsed_utilization - original_utilization


def evaluate_task_before_after(task_before: Any, task_after: Any) -> Dict[str, Any]:
    """Compare a single task's metrics before and after collapse."""
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
                getattr(task_before, 'core_requirement', 1),
                getattr(task_after, 'core_requirement', 1)
            ),
            "workload_reduction": calculate_workload_reduction(
                task_before.workload(), task_after.workload()
            ),
            "path_extension": calculate_path_extension(
                task_before.critical_path(), task_after.critical_path()
            ),
            "utilization_change": calculate_utilization_change(
                task_before.utilization, task_after.utilization
            )
        }
    else:
        result["savings"] = {
            "core_savings": 0, "workload_reduction": 0,
            "path_extension": 0, "utilization_change": 0
        }

    return result


def evaluate_task_set(tasks_before: List[Any], tasks_after: List[Any],
                      heuristic: str = "unknown") -> Dict[str, Any]:
    """Aggregate metrics for an entire task set."""
    n = len(tasks_before)
    if n == 0:
        return {
            "heuristic": heuristic, "num_tasks": 0,
            "total_original_cores": 0, "total_collapsed_cores": 0,
            "total_core_savings": 0, "avg_core_savings": 0,
            "total_workload_reduction": 0, "avg_workload_reduction": 0,
            "total_path_extension": 0, "avg_path_extension": 0,
            "schedulability_ratio": 0
        }

    total_orig_wl = sum(t.workload() for t in tasks_before)
    total_coll_wl = sum(t.workload() for t in tasks_after) if all(t is not None for t in tasks_after) else total_orig_wl

    total_orig_cp = sum(t.critical_path() for t in tasks_before)
    total_coll_cp = sum(t.critical_path() for t in tasks_after) if all(t is not None for t in tasks_after) else total_orig_cp

    schedulable = sum(1 for t in tasks_after if t is not None)

    wl_reduction = calculate_workload_reduction(total_orig_wl, total_coll_wl)
    cp_extension = calculate_path_extension(total_orig_cp, total_coll_cp)

    return {
        "heuristic": heuristic,
        "num_tasks": n,
        "total_original_workload": total_orig_wl,
        "total_collapsed_workload": total_coll_wl,
        "total_workload_reduction": wl_reduction,
        "avg_workload_reduction": wl_reduction / n,
        "total_path_extension": cp_extension,
        "avg_path_extension": cp_extension / n,
        "schedulability_ratio": calculate_schedulability_ratio(schedulable, n)
    }


def compare_heuristics(task_sets_before: Dict[str, List[Any]],
                       task_sets_after: Dict[str, List[Any]]) -> Dict[str, Any]:
    """Compare results across OT-G, OT-L, OT-A heuristics."""
    results = {}
    for heuristic in task_sets_before:
        before = task_sets_before[heuristic]
        after = task_sets_after.get(heuristic, before)
        results[heuristic] = evaluate_task_set(before, after, heuristic)

    ranked = sorted(results.items(),
                    key=lambda x: x[1].get("total_workload_reduction", 0),
                    reverse=True)

    return {
        "results": results,
        "ranking": [h for h, _ in ranked],
        "best_heuristic": ranked[0][0] if ranked else None
    }


class MetricsCalculator:
    """Tracks evaluation results over multiple runs."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def add_result(self, task_id: str, result: Dict[str, Any]) -> None:
        self.history.append({"task_id": task_id, "result": result})

    def compute_summary(self) -> Dict[str, Any]:
        if not self.history:
            return {
                "num_evaluations": 0,
                "total_core_savings": 0, "total_workload_reduction": 0,
                "avg_core_savings": 0, "avg_workload_reduction": 0
            }

        core_sav = sum(h["result"].get("savings", {}).get("core_savings", 0) for h in self.history)
        wl_red = sum(h["result"].get("savings", {}).get("workload_reduction", 0) for h in self.history)
        n = len(self.history)

        return {
            "num_evaluations": n,
            "total_core_savings": core_sav,
            "total_workload_reduction": wl_red,
            "avg_core_savings": core_sav / n,
            "avg_workload_reduction": wl_red / n
        }

    def reset(self) -> None:
        self.history = []

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history