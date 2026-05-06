"""
Tests for DAG Model
Based on paper's Figure 1 example
"""

import unittest
import math
from src.dag_model import DAGTask, DAGNode


def create_simple_wceto(c1):
    """Create a simple linear WCETO function for testing."""
    def wceto_func(eta):
        return c1 * eta
    return wceto_func


class TestDAGNode(unittest.TestCase):
    """Test DAGNode class."""
    
    def test_node_creation(self):
        """Test creating a basic node."""
        wceto_func = create_simple_wceto(10)
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        
        self.assertEqual(node.object_id, "obj1")
        self.assertEqual(node.num_threads, 1)
        self.assertAlmostEqual(node.wceto(), 10.0)
    
    def test_node_wceto_with_threads(self):
        """Test WCETO calculation with multiple threads."""
        wceto_func = create_simple_wceto(10)
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=3)
        
        self.assertAlmostEqual(node.wceto(), 30.0)
    
    def test_node_wceto_with_eta_param(self):
        """Test WCETO calculation with eta parameter."""
        wceto_func = create_simple_wceto(10)
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        
        self.assertAlmostEqual(node.wceto(5), 50.0)
    
    def test_node_repr(self):
        """Test node string representation."""
        wceto_func = create_simple_wceto(10)
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        
        self.assertIn("obj1", repr(node))
        self.assertIn("η=1", repr(node))


class TestDAGTask(unittest.TestCase):
    """Test DAGTask class."""
    
    def test_task_creation(self):
        """Test creating a basic task."""
        task = DAGTask(task_id="task1", period=100.0, deadline=100.0)
        
        self.assertEqual(task.task_id, "task1")
        self.assertEqual(task.period, 100.0)
        self.assertEqual(task.deadline, 100.0)
        self.assertEqual(task.num_nodes(), 0)
    
    def test_add_node(self):
        """Test adding nodes to task."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        node1 = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        node2 = DAGNode(object_id="obj2", wceto_func=wceto_func, num_threads=1)
        
        task.add_node(node1, "node1")
        task.add_node(node2, "node2")
        
        self.assertEqual(task.num_nodes(), 2)
    
    def test_add_edge(self):
        """Test adding edges between nodes."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        node1 = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        node2 = DAGNode(object_id="obj2", wceto_func=wceto_func, num_threads=1)
        
        task.add_node(node1, "node1")
        task.add_node(node2, "node2")
        task.add_edge("node1", "node2")
        
        self.assertTrue(task.graph.has_edge("node1", "node2"))
    
    def test_workload_calculation(self):
        """Test workload calculation (Equation 7)."""
        task = DAGTask(task_id="task1", period=100.0)
        
        # Add 4 nodes with specific WCETs (like paper's Figure 1 simplified)
        for obj_id, wcet, name in [("s", 20, "s"), ("u", 10, "u"), 
                                    ("v", 10, "v"), ("t", 20, "t")]:
            wceto_func = create_simple_wceto(wcet)
            node = DAGNode(object_id=obj_id, wceto_func=wceto_func, num_threads=1)
            task.add_node(node, name)
        
        # Add edges: s -> u -> t and s -> v -> t
        task.add_edge("s", "u")
        task.add_edge("u", "t")
        task.add_edge("s", "v")
        task.add_edge("v", "t")
        
        # Expected workload: 20 + 10 + 10 + 20 = 60
        expected_workload = 60.0
        self.assertAlmostEqual(task.workload(), expected_workload, places=1)
    
    def test_critical_path_calculation(self):
        """Test critical path calculation (Equation 6)."""
        task = DAGTask(task_id="task1", period=100.0)
        
        # Add nodes with known WCETs
        for obj_id, wcet, name in [("s", 20, "s"), ("u", 10, "u"), 
                                    ("v", 10, "v"), ("t", 20, "t")]:
            wceto_func = create_simple_wceto(wcet)
            node = DAGNode(object_id=obj_id, wceto_func=wceto_func, num_threads=1)
            task.add_node(node, name)
        
        # Add edges: s -> u -> t and s -> v -> t
        task.add_edge("s", "u")
        task.add_edge("u", "t")
        task.add_edge("s", "v")
        task.add_edge("v", "t")
        
        # Critical path should be s -> u -> t = 20 + 10 + 20 = 50
        expected_critical_path = 50.0
        self.assertAlmostEqual(task.critical_path_length(), expected_critical_path, places=1)
    
    def test_utilization_calculation(self):
        """Test utilization calculation (Equation 3)."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        task.add_node(node, "node1")
        
        # Utilization = C / T = 10 / 100 = 0.1
        self.assertAlmostEqual(task.utilization(), 0.1)
    
    def test_candidate_identification(self):
        """Test candidate identification (Definition 4)."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        # Add two nodes with same object (candidates)
        node1 = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        node2 = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        
        task.add_node(node1, "node1")
        task.add_node(node2, "node2")
        
        candidates = task.get_candidates()
        
        # Should have one candidate pair
        self.assertEqual(len(candidates), 1)
        # Order might be (node1, node2) or (node2, node1)
        self.assertTrue(("node1", "node2") in candidates or ("node2", "node1") in candidates)
    
    def test_no_candidates_different_objects(self):
        """Test no candidates when objects differ."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        node1 = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        node2 = DAGNode(object_id="obj2", wceto_func=wceto_func, num_threads=1)
        
        task.add_node(node1, "node1")
        task.add_node(node2, "node2")
        
        candidates = task.get_candidates()
        
        self.assertEqual(len(candidates), 0)
    
    def test_multiple_candidates(self):
        """Test multiple candidates with same object."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        # Add 3 nodes with same object
        for i in range(3):
            node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
            task.add_node(node, f"node{i}")
        
        candidates = task.get_candidates()
        
        # 3 nodes = 3 pairs (C(3,2) = 3)
        self.assertEqual(len(candidates), 3)
    
    def test_get_nodes_by_object(self):
        """Test get_nodes_by_object method."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        # Add nodes with different objects
        for obj, name in [("obj1", "n1"), ("obj1", "n2"), ("obj2", "n3")]:
            node = DAGNode(object_id=obj, wceto_func=wceto_func, num_threads=1)
            task.add_node(node, name)
        
        # Get nodes for obj1
        obj1_nodes = task.get_nodes_by_object("obj1")
        self.assertEqual(len(obj1_nodes), 2)
        self.assertIn("n1", obj1_nodes)
        self.assertIn("n2", obj1_nodes)
        
        # Get nodes for obj2
        obj2_nodes = task.get_nodes_by_object("obj2")
        self.assertEqual(len(obj2_nodes), 1)
        self.assertIn("n3", obj2_nodes)
        
        # Get nodes for non-existent object
        empty = task.get_nodes_by_object("nonexistent")
        self.assertEqual(len(empty), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_single_node_dag(self):
        """Test DAG with only one node."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
        task.add_node(node, "node1")
        
        self.assertEqual(task.num_nodes(), 1)
        self.assertEqual(task.workload(), 10.0)
        self.assertEqual(task.critical_path_length(), 10.0)
        self.assertEqual(task.utilization(), 0.1)
    
    def test_empty_task(self):
        """Test empty DAG task."""
        task = DAGTask(task_id="task1", period=100.0)
        
        self.assertEqual(task.num_nodes(), 0)
        self.assertEqual(task.workload(), 0.0)
        self.assertEqual(task.critical_path_length(), 0.0)
        self.assertEqual(task.utilization(), 0.0)
        self.assertEqual(len(task.get_candidates()), 0)
    
    def test_all_same_object(self):
        """Test when all nodes have same object (maximum candidates)."""
        task = DAGTask(task_id="task1", period=100.0)
        wceto_func = create_simple_wceto(10)
        
        # Add 4 nodes all with same object
        for i in range(4):
            node = DAGNode(object_id="obj1", wceto_func=wceto_func, num_threads=1)
            task.add_node(node, f"node{i}")
        
        # 4 nodes = C(4,2) = 6 pairs
        candidates = task.get_candidates()
        self.assertEqual(len(candidates), 6)


if __name__ == '__main__':
    unittest.main()