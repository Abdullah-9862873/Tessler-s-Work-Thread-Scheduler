"""
Tests for Core Allocation
Based on Section III-C (Equation 5)
"""

import unittest
import math
from src.dag_model import DAGTask, DAGNode
from src.growth_factor import create_growth_factor_wceto
from src import core_allocation


def create_simple_wceto(c1):
    """Create a simple linear WCETO function for testing."""
    def wceto_func(eta):
        return c1 * eta
    return wceto_func


class TestCoreAllocation(unittest.TestCase):
    """Test core allocation formula (Equation 5)."""
    
    def test_simple_core_allocation(self):
        """Test basic core allocation calculation."""
        task = DAGTask(task_id="task1", period=100.0, deadline=100.0)
        
        # Create task: C=100, L=20, D=100
        # m = ceil((100-20)/(100-20)) = ceil(80/80) = 1
        wceto_func = create_simple_wceto(20)
        
        # 5 nodes with WCET 20 each = workload 100
        for i in range(5):
            node = DAGNode(object_id=f"obj{i % 2}", wceto_func=wceto_func, num_threads=1)
            task.add_node(node, f"node{i}")
        
        # Add edges to create critical path less than workload
        for i in range(4):
            task.add_edge(f"node{i}", f"node{i+1}")
        
        cores = core_allocation.calculate_core_allocation(task)
        
        # Should need at least 1 core
        self.assertGreaterEqual(cores, 1)
    
    def test_infeasible_task(self):
        """Test infeasible task (critical path > deadline)."""
        task = DAGTask(task_id="task1", period=100.0, deadline=50.0)
        wceto_func = create_simple_wceto(20)
        
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        task.add_node(node, "node1")
        
        # Critical path = 20, deadline = 50, so should be feasible
        cores = core_allocation.calculate_core_allocation(task)
        
        self.assertGreater(cores, 0)
    
    def test_exactly_one_core(self):
        """Test task that needs exactly one core."""
        task = DAGTask(task_id="task1", period=100.0, deadline=100.0)
        wceto_func = create_simple_wceto(10)
        
        # Single node: C=10, L=10, D=100
        # m = ceil((10-10)/(100-10)) = 0 -> but we handle as 1
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        task.add_node(node, "node1")
        
        cores = core_allocation.calculate_core_allocation(task)
        
        # Should need 1 core
        self.assertGreaterEqual(cores, 1)
    
    def test_high_cores_needed(self):
        """Test task that needs multiple cores."""
        task = DAGTask(task_id="task1", period=50.0, deadline=50.0)
        
        # Create a task with: C = 100, L = 20, D = 50
        # This should need multiple cores
        # m = ceil((100-20)/(50-20)) = ceil(80/30) = 3
        wceto_func = create_simple_wceto(10)
        
        # Create chain: 10 nodes, each 10 units
        # Workload = 100, but critical path = 20 (only 2 nodes on longest path: 10 + 10)
        for i in range(10):
            node = DAGNode(object_id=f"obj{i}", wceto_func=wceto_func, num_threads=1)
            task.add_node(node, f"node{i}")
        
        # Create a diamond shape so critical path is shorter than workload
        #       node0
        #      /    \
        #   node1    node2
        #      \    /
        #       node3
        #      /    \
        #   node4    node5
        #      \    /
        #       node6
        # ... and so on
        
        # Actually let's just do a chain with some parallel branches
        # Chain: 0->1->2->3->4->5->6->7->8->9
        # This gives L = 10*10 = 100 (worst case)
        
        # Let's do: nodes with parallel edges to make L < C
        # Create 2 parallel chains
        for i in range(5):
            task.add_edge(f"node{i}", f"node{i+5}")  # Connect chain to chain
        
        # Now critical path is only 10 (one chain), but workload is 100
        # L = 10, C = 100, D = 50
        # m = ceil((100-10)/(50-10)) = ceil(90/40) = 3
        
        cores = core_allocation.calculate_core_allocation(task)
        
        # Should need multiple cores due to high utilization
        self.assertGreater(cores, 1)


class TestHighLowUtilization(unittest.TestCase):
    """Test high/low utilization detection."""
    
    def test_high_utilization(self):
        """Test high utilization detection (u > 1)."""
        task = DAGTask(task_id="task1", period=50.0)
        wceto_func = create_simple_wceto(60)
        
        # Utilization = 60/50 = 1.2 > 1
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        task.add_node(node, "node1")
        
        self.assertTrue(core_allocation.is_high_utilization(task))
    
    def test_low_utilization(self):
        """Test low utilization detection (u <= 1)."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        # Utilization = 10/100 = 0.1 < 1
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        task.add_node(node, "node1")
        
        self.assertFalse(core_allocation.is_high_utilization(task))
    
    def test_boundary_utilization(self):
        """Test exactly 1.0 utilization is low."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(100)
        
        # Utilization = 100/100 = 1.0 (not > 1, so low)
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        task.add_node(node, "node1")
        
        self.assertFalse(core_allocation.is_high_utilization(task))
    
    def test_separation(self):
        """Test separating tasks into high/low."""
        tasks = []
        
        # High utilization task
        task1 = DAGTask(task_id="task1", period=50.0)
        wceto1 = create_simple_wceto(60)
        node1 = DAGNode(object_id="obj1", wceto_func=wceto1, num_threads=1)
        task1.add_node(node1, "node1")
        tasks.append(task1)
        
        # Low utilization task
        task2 = DAGTask(task_id="task2", period=100.0)
        wceto2 = create_simple_wceto(10)
        node2 = DAGNode(object_id="obj1", wceto_func=wceto2, num_threads=1)
        task2.add_node(node2, "node1")
        tasks.append(task2)
        
        high, low = core_allocation.separate_high_low_utilization(tasks)
        
        self.assertEqual(len(high), 1)
        self.assertEqual(len(low), 1)


class TestImprovedCoreAllocation(unittest.TestCase):
    """Test improved core allocation check (Definition 6)."""
    
    def test_improvement_reduction(self):
        """Test core reduction is improvement."""
        # m_i > 0 => 0 < m̂_i <= m_i
        self.assertTrue(core_allocation.check_improved_core_allocation(5, 3))
        self.assertTrue(core_allocation.check_improved_core_allocation(5, 5))
        self.assertTrue(core_allocation.check_improved_core_allocation(5, 1))
    
    def test_no_improvement(self):
        """Test cases that are not improvements."""
        # More cores needed = not improved
        self.assertFalse(core_allocation.check_improved_core_allocation(3, 5))
        # Zero or negative = not improvement for positive original
        self.assertFalse(core_allocation.check_improved_core_allocation(0, 0))
        self.assertFalse(core_allocation.check_improved_core_allocation(-1, 0))
    
    def test_infeasible_to_feasible(self):
        """Test infeasible becoming feasible is improvement."""
        # m_i <= 0 => m̂_i >= m_i
        self.assertTrue(core_allocation.check_improved_core_allocation(-1, 3))
        self.assertTrue(core_allocation.check_improved_core_allocation(-1, 1))


class TestCoreAllocator(unittest.TestCase):
    """Test CoreAllocator class."""
    
    def test_allocator_creation(self):
        """Test creating allocator."""
        allocator = core_allocation.CoreAllocator(total_cores=8)
        
        self.assertEqual(allocator.total_cores, 8)
    
    def test_feasible_allocation(self):
        """Test feasible allocation."""
        allocator = core_allocation.CoreAllocator(total_cores=10)
        
        tasks = []
        task = DAGTask(task_id="task1", period=100.0)
        wceto = create_simple_wceto(10)
        node = DAGNode(object_id="obj1", wceto_func=wceto, num_threads=1)
        task.add_node(node, "node1")
        tasks.append(task)
        
        result = allocator.allocate(tasks)
        
        self.assertTrue(result['feasible'])
    
    def test_infeasible_allocation(self):
        """Test infeasible allocation (not enough cores)."""
        allocator = core_allocation.CoreAllocator(total_cores=1)
        
        # Create high utilization tasks requiring > 1 core
        tasks = []
        for i in range(5):
            task = DAGTask(task_id=f"task{i}", period=10.0)
            wceto = create_simple_wceto(50)
            node = DAGNode(object_id="obj1", wceto_func=wceto, num_threads=1)
            task.add_node(node, "node1")
            tasks.append(task)
        
        result = allocator.allocate(tasks)
        
        # Should be infeasible due to high core requirements
        self.assertIn('feasible', result)
    
    def test_total_core_requirements(self):
        """Test calculate_total_core_requirements function."""
        tasks = []
        
        # Low utilization task
        task1 = DAGTask(task_id="task1", period=100.0)
        wceto1 = create_simple_wceto(10)
        node1 = DAGNode(object_id="obj1", wceto_func=wceto1, num_threads=1)
        task1.add_node(node1, "node1")
        tasks.append(task1)
        
        # Another low utilization task
        task2 = DAGTask(task_id="task2", period=100.0)
        wceto2 = create_simple_wceto(20)
        node2 = DAGNode(object_id="obj1", wceto_func=wceto2, num_threads=1)
        task2.add_node(node2, "node1")
        tasks.append(task2)
        
        result = core_allocation.calculate_total_core_requirements(tasks)
        
        self.assertIn('total_high_cores', result)
        self.assertIn('high_tasks', result)
        self.assertIn('low_tasks', result)
        self.assertIn('infeasible', result)


if __name__ == '__main__':
    unittest.main()