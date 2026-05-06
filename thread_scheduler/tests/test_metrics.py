"""
Tests for Metrics Calculator
Based on Equations 16-19 of the paper
"""

import unittest
from src.metrics import (
    calculate_core_savings,
    calculate_workload_reduction,
    calculate_path_extension,
    calculate_schedulability_ratio,
    calculate_utilization_change,
    evaluate_task_before_after,
    evaluate_task_set,
    compare_heuristics,
    MetricsCalculator
)


class MockTask:
    """Mock task for testing."""
    
    def __init__(self, workload_val, critical_path_val, util_val, core_req_val=1):
        self._workload = workload_val
        self._critical_path = critical_path_val
        self._utilization = util_val
        self._core_requirement = core_req_val
    
    def workload(self):
        return self._workload
    
    def critical_path(self):
        return self._critical_path
    
    @property
    def utilization(self):
        return self._utilization
    
    @property
    def core_requirement(self):
        return self._core_requirement


class TestCoreSavings(unittest.TestCase):
    """Test core savings calculation (Equation 16)."""
    
    def test_positive_savings(self):
        """Test positive savings when cores reduced."""
        result = calculate_core_savings(5, 3)
        self.assertEqual(result, 2)
    
    def test_no_savings(self):
        """Test zero savings when cores unchanged."""
        result = calculate_core_savings(3, 3)
        self.assertEqual(result, 0)
    
    def test_negative_savings(self):
        """Test negative savings when cores increased."""
        result = calculate_core_savings(2, 4)
        self.assertEqual(result, -2)
    
    def test_infeasible_to_feasible(self):
        """Test saving when going from infeasible to feasible."""
        result = calculate_core_savings(-1, 2)
        self.assertEqual(result, -3)


class TestWorkloadReduction(unittest.TestCase):
    """Test workload reduction calculation (Equation 18)."""
    
    def test_positive_reduction(self):
        """Test positive reduction when workload decreased."""
        result = calculate_workload_reduction(100, 80)
        self.assertEqual(result, 20)
    
    def test_no_reduction(self):
        """Test zero reduction when workload unchanged."""
        result = calculate_workload_reduction(100, 100)
        self.assertEqual(result, 0)
    
    def test_negative_reduction(self):
        """Test negative reduction when workload increased."""
        result = calculate_workload_reduction(80, 100)
        self.assertEqual(result, -20)


class TestPathExtension(unittest.TestCase):
    """Test critical path extension calculation (Equation 19)."""
    
    def test_positive_extension(self):
        """Test positive extension when path increased."""
        result = calculate_path_extension(10, 15)
        self.assertEqual(result, 5)
    
    def test_no_extension(self):
        """Test zero extension when path unchanged."""
        result = calculate_path_extension(10, 10)
        self.assertEqual(result, 0)
    
    def test_negative_extension(self):
        """Test negative extension when path decreased."""
        result = calculate_path_extension(15, 10)
        self.assertEqual(result, -5)


class TestSchedulabilityRatio(unittest.TestCase):
    """Test schedulability ratio calculation."""
    
    def test_full_schedulability(self):
        """Test ratio of 1 when all tasks schedulable."""
        result = calculate_schedulability_ratio(10, 10)
        self.assertEqual(result, 1.0)
    
    def test_partial_schedulability(self):
        """Test ratio between 0 and 1."""
        result = calculate_schedulability_ratio(7, 10)
        self.assertEqual(result, 0.7)
    
    def test_no_schedulability(self):
        """Test ratio of 0 when no tasks schedulable."""
        result = calculate_schedulability_ratio(0, 10)
        self.assertEqual(result, 0.0)
    
    def test_zero_total_tasks(self):
        """Test zero when no tasks."""
        result = calculate_schedulability_ratio(0, 0)
        self.assertEqual(result, 0.0)


class TestUtilizationChange(unittest.TestCase):
    """Test utilization change calculation."""
    
    def test_positive_change(self):
        """Test positive change (worse)."""
        result = calculate_utilization_change(0.5, 0.7)
        self.assertAlmostEqual(result, 0.2)
    
    def test_negative_change(self):
        """Test negative change (improvement)."""
        result = calculate_utilization_change(0.7, 0.5)
        self.assertAlmostEqual(result, -0.2)
    
    def test_no_change(self):
        """Test zero change."""
        result = calculate_utilization_change(0.5, 0.5)
        self.assertEqual(result, 0)


class TestEvaluateTaskBeforeAfter(unittest.TestCase):
    """Test single task evaluation."""
    
    def test_with_after_task(self):
        """Test evaluation with valid after task."""
        before = MockTask(100, 20, 0.5, 3)
        after = MockTask(80, 25, 0.4, 2)
        
        result = evaluate_task_before_after(before, after)
        
        self.assertEqual(result["before"]["workload"], 100)
        self.assertEqual(result["after"]["workload"], 80)
        self.assertEqual(result["savings"]["core_savings"], 1)
        self.assertEqual(result["savings"]["workload_reduction"], 20)
        self.assertEqual(result["savings"]["path_extension"], 5)
    
    def test_with_null_after(self):
        """Test evaluation when collapse failed (after is None)."""
        before = MockTask(100, 20, 0.5, 3)
        
        result = evaluate_task_before_after(before, None)
        
        self.assertIsNone(result["after"])
        self.assertEqual(result["savings"]["core_savings"], 0)


class TestEvaluateTaskSet(unittest.TestCase):
    """Test task set evaluation."""
    
    def test_single_task_set(self):
        """Test evaluation with single task."""
        before = [MockTask(100, 20, 0.5, 3)]
        after = [MockTask(80, 25, 0.4, 2)]
        
        result = evaluate_task_set(before, after, "OT-G")
        
        self.assertEqual(result["num_tasks"], 1)
        self.assertEqual(result["total_workload_reduction"], 20)
        self.assertEqual(result["avg_workload_reduction"], 20)
        self.assertEqual(result["schedulability_ratio"], 1.0)
    
    def test_multiple_tasks(self):
        """Test evaluation with multiple tasks."""
        before = [
            MockTask(100, 20, 0.5, 3),
            MockTask(50, 10, 0.25, 1)
        ]
        after = [
            MockTask(80, 25, 0.4, 2),
            MockTask(40, 12, 0.2, 1)
        ]
        
        result = evaluate_task_set(before, after, "OT-L")
        
        self.assertEqual(result["num_tasks"], 2)
        self.assertEqual(result["total_workload_reduction"], 30)
        self.assertEqual(result["avg_workload_reduction"], 15)
    
    def test_empty_task_set(self):
        """Test evaluation with empty task set."""
        result = evaluate_task_set([], [], "OT-A")
        
        self.assertEqual(result["num_tasks"], 0)
    
    def test_heuristic_name_stored(self):
        """Test heuristic name is stored in result."""
        before = [MockTask(100, 20, 0.5, 3)]
        after = [MockTask(80, 25, 0.4, 2)]
        
        result = evaluate_task_set(before, after, "OT-G")
        
        self.assertEqual(result["heuristic"], "OT-G")


class TestCompareHeuristics(unittest.TestCase):
    """Test heuristic comparison."""
    
    def test_single_heuristic(self):
        """Test comparison with single heuristic."""
        before = {"OT-G": [MockTask(100, 20, 0.5, 3)]}
        after = {"OT-G": [MockTask(80, 25, 0.4, 2)]}
        
        result = compare_heuristics(before, after)
        
        self.assertIn("OT-G", result["results"])
        self.assertIn("ranking", result)
    
    def test_multiple_heuristics(self):
        """Test comparison with multiple heuristics."""
        before = {
            "OT-G": [MockTask(100, 20, 0.5, 3)],
            "OT-L": [MockTask(100, 20, 0.5, 3)]
        }
        after = {
            "OT-G": [MockTask(80, 25, 0.4, 2)],
            "OT-L": [MockTask(60, 30, 0.3, 1)]
        }
        
        result = compare_heuristics(before, after)
        
        self.assertEqual(len(result["results"]), 2)
        self.assertIn("OT-G", result["results"])
        self.assertIn("OT-L", result["results"])
        self.assertEqual(len(result["ranking"]), 2)
    
    def test_best_heuristic_identified(self):
        """Test best heuristic is correctly identified."""
        before = {
            "OT-G": [MockTask(100, 20, 0.5, 3)],
            "OT-L": [MockTask(100, 20, 0.5, 3)]
        }
        after = {
            "OT-G": [MockTask(80, 25, 0.4, 2)],
            "OT-L": [MockTask(50, 30, 0.25, 1)]
        }
        
        result = compare_heuristics(before, after)
        
        self.assertEqual(result["best_heuristic"], "OT-L")


class TestMetricsCalculatorClass(unittest.TestCase):
    """Test MetricsCalculator class."""
    
    def test_creation(self):
        """Test calculator creation."""
        calc = MetricsCalculator()
        self.assertEqual(len(calc.history), 0)
    
    def test_add_result(self):
        """Test adding result to history."""
        calc = MetricsCalculator()
        calc.add_result("task1", {"savings": {"core_savings": 2}})
        
        self.assertEqual(len(calc.history), 1)
        self.assertEqual(calc.history[0]["task_id"], "task1")
    
    def test_compute_summary_empty(self):
        """Test summary with no history."""
        calc = MetricsCalculator()
        summary = calc.compute_summary()
        
        self.assertEqual(summary["num_evaluations"], 0)
    
    def test_compute_summary_with_data(self):
        """Test summary with data."""
        calc = MetricsCalculator()
        calc.add_result("task1", {"savings": {"core_savings": 2, "workload_reduction": 10}})
        calc.add_result("task2", {"savings": {"core_savings": 1, "workload_reduction": 5}})
        
        summary = calc.compute_summary()
        
        self.assertEqual(summary["num_evaluations"], 2)
        self.assertEqual(summary["total_core_savings"], 3)
        self.assertEqual(summary["total_workload_reduction"], 15)
        self.assertEqual(summary["avg_core_savings"], 1.5)
    
    def test_reset(self):
        """Test resetting history."""
        calc = MetricsCalculator()
        calc.add_result("task1", {"savings": {"core_savings": 2}})
        calc.reset()
        
        self.assertEqual(len(calc.history), 0)
    
    def test_get_history(self):
        """Test getting full history."""
        calc = MetricsCalculator()
        calc.add_result("task1", {"savings": {"core_savings": 2}})
        calc.add_result("task2", {"savings": {"core_savings": 1}})
        
        history = calc.get_history()
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["task_id"], "task1")
        self.assertEqual(history[1]["task_id"], "task2")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases."""
    
    def test_zero_cores_original(self):
        """Test with zero original cores."""
        result = calculate_core_savings(0, 0)
        self.assertEqual(result, 0)
    
    def test_zero_workload(self):
        """Test with zero workload."""
        result = calculate_workload_reduction(0, 0)
        self.assertEqual(result, 0)
    
    def test_zero_critical_path(self):
        """Test with zero critical path."""
        result = calculate_path_extension(0, 0)
        self.assertEqual(result, 0)
    
    def test_large_values(self):
        """Test with large values."""
        result = calculate_core_savings(10000, 5000)
        self.assertEqual(result, 5000)


if __name__ == '__main__':
    unittest.main()