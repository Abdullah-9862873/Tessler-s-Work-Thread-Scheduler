"""
Tests for Task Generator
Based on Section IX (synthetic evaluation pipeline)
"""

import unittest
import networkx as nx
from src.task_generator import (
    generate_dag_structure,
    ensure_single_source_sink,
    generate_dag_ot_task,
    generate_task_set,
    TaskSetGenerator
)
from src.dag_model import DAGTask, DAGNode


class TestDAGStructure(unittest.TestCase):
    """Test DAG structure generation."""
    
    def test_basic_dag_generation(self):
        """Test basic DAG generation with default parameters."""
        G = generate_dag_structure(10, 0.1)
        self.assertEqual(len(G.nodes()), 10)
        self.assertTrue(nx.is_directed_acyclic_graph(G))
    
    def test_different_node_counts(self):
        """Test different node counts create appropriate graphs."""
        for num_nodes in [10, 20, 50]:
            G = generate_dag_structure(num_nodes, 0.1)
            self.assertEqual(len(G.nodes()), num_nodes)
            self.assertTrue(nx.is_directed_acyclic_graph(G))
    
    def test_edge_probability_affects_density(self):
        """Test higher edge probability creates denser graphs."""
        G_sparse = generate_dag_structure(20, 0.02)
        G_dense = generate_dag_structure(20, 0.2)
        
        self.assertLess(G_sparse.number_of_edges(), G_dense.number_of_edges())
    
    def test_seed_reproducibility(self):
        """Test same seed produces same graph."""
        G1 = generate_dag_structure(20, 0.1, seed=42)
        G2 = generate_dag_structure(20, 0.1, seed=42)
        
        self.assertEqual(set(G1.edges()), set(G2.edges()))
    
    def test_edges_only_forward(self):
        """Test edges only go from lower to higher node indices."""
        G = generate_dag_structure(50, 0.2)
        for u, v in G.edges():
            self.assertLess(u, v)


class TestSourceSinkEnforcement(unittest.TestCase):
    """Test single source/sink enforcement."""
    
    def test_multiple_sources_collapsed(self):
        """Test multiple sources are collapsed to single source."""
        G = generate_dag_structure(10, 0.3)
        G, added_source, added_sink = ensure_single_source_sink(G)
        
        sources = [n for n in G.nodes() if G.in_degree(n) == 0]
        self.assertEqual(len(sources), 1)
        self.assertTrue(added_source)
    
    def test_multiple_sinks_collapsed(self):
        """Test multiple sinks are collapsed to single sink."""
        G = generate_dag_structure(10, 0.3)
        G, added_source, added_sink = ensure_single_source_sink(G)
        
        sinks = [n for n in G.nodes() if G.out_degree(n) == 0]
        self.assertEqual(len(sinks), 1)
        self.assertTrue(added_sink)
    
    def test_single_source_sink_unchanged(self):
        """Test single source/sink remains unchanged."""
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])
        
        G_copy, added_source, added_sink = ensure_single_source_sink(G)
        
        self.assertFalse(added_source)
        self.assertFalse(added_sink)


class TestDAGOTTaskGeneration(unittest.TestCase):
    """Test complete DAG-OT task generation."""
    
    def test_basic_task_generation(self):
        """Test basic task generation creates valid DAGTask."""
        task = generate_dag_ot_task(
            task_id="test_task",
            num_nodes=10,
            edge_probability=0.1,
            num_objects=4,
            growth_factor=0.5,
            target_utilization=0.5,
            base_wcet=100
        )
        
        self.assertIsInstance(task, DAGTask)
        self.assertEqual(task.task_id, "test_task")
        self.assertGreater(task.period, 0)
    
    def test_different_node_counts(self):
        """Test different node counts create appropriate number of nodes."""
        for num_nodes in [5, 15, 30]:
            task = generate_dag_ot_task(
                task_id=f"task_{num_nodes}",
                num_nodes=num_nodes,
                edge_probability=0.1,
                num_objects=4,
                growth_factor=0.5,
                target_utilization=0.5
            )
            
            workload = task.workload()
            self.assertGreater(workload, 0)
    
    def test_different_growth_factors(self):
        """Test different growth factors work."""
        for gf in [0.2, 0.6, 1.0]:
            task = generate_dag_ot_task(
                task_id=f"task_gf{gf}",
                num_nodes=10,
                edge_probability=0.1,
                num_objects=4,
                growth_factor=gf,
                target_utilization=0.5
            )
            
            self.assertIsNotNone(task)
            self.assertGreater(task.workload(), 0)
    
    def test_utilization_approximately_achieved(self):
        """Test generated task achieves approximately target utilization."""
        target_u = 0.5
        task = generate_dag_ot_task(
            task_id="test_u",
            num_nodes=10,
            edge_probability=0.1,
            num_objects=4,
            growth_factor=0.5,
            target_utilization=target_u,
            base_wcet=100
        )
        
        workload = task.workload()
        achieved_u = workload / task.period
        
        self.assertAlmostEqual(achieved_u, target_u, places=1)
    
    def test_different_num_objects(self):
        """Test different number of objects parameter."""
        for num_objs in [2, 8, 16]:
            task = generate_dag_ot_task(
                task_id=f"task_obj{num_objs}",
                num_nodes=10,
                edge_probability=0.1,
                num_objects=num_objs,
                growth_factor=0.5,
                target_utilization=0.5
            )
            
            self.assertIsNotNone(task)
    
    def test_task_has_valid_dag(self):
        """Test generated task has valid DAG structure."""
        task = generate_dag_ot_task(
            task_id="test_dag",
            num_nodes=15,
            edge_probability=0.15,
            num_objects=4,
            growth_factor=0.5,
            target_utilization=0.5
        )
        
        self.assertTrue(nx.is_directed_acyclic_graph(task.graph))


class TestTaskSetGeneration(unittest.TestCase):
    """Test task set generation."""
    
    def test_generate_multiple_tasks(self):
        """Test generating multiple tasks."""
        tasks = generate_task_set(
            num_tasks=5,
            num_nodes=10,
            edge_probability=0.1,
            num_objects=4,
            growth_factor=0.5,
            target_utilization=1.0
        )
        
        self.assertEqual(len(tasks), 5)
    
    def test_task_ids_unique(self):
        """Test task IDs are unique."""
        tasks = generate_task_set(
            num_tasks=10,
            num_nodes=10,
            edge_probability=0.1,
            num_objects=4,
            growth_factor=0.5,
            target_utilization=1.0
        )
        
        task_ids = [t.task_id for t in tasks]
        self.assertEqual(len(task_ids), len(set(task_ids)))
    
    def test_utilization_split_evenly(self):
        """Test total utilization is distributed across tasks."""
        total_u = 2.0
        num_tasks = 4
        u_per_task = total_u / num_tasks
        
        tasks = generate_task_set(
            num_tasks=num_tasks,
            num_nodes=10,
            edge_probability=0.1,
            num_objects=4,
            growth_factor=0.5,
            target_utilization=total_u
        )
        
        for task in tasks:
            achieved_u = task.workload() / task.period
            self.assertAlmostEqual(achieved_u, u_per_task, places=1)


class TestTaskSetGeneratorClass(unittest.TestCase):
    """Test TaskSetGenerator class."""
    
    def test_generator_creation(self):
        """Test generator creation."""
        gen = TaskSetGenerator(seed=42)
        self.assertEqual(gen.seed, 42)
    
    def test_generator_defaults_to_none_seed(self):
        """Test generator works without seed."""
        gen = TaskSetGenerator()
        self.assertIsNone(gen.seed)
    
    def test_random_task_generation(self):
        """Test random task generation."""
        gen = TaskSetGenerator(seed=42)
        task = gen.generate_random_task()
        
        self.assertIsInstance(task, DAGTask)
        self.assertGreater(task.workload(), 0)
    
    def test_reproducibility_with_same_seed(self):
        """Test same seed produces same tasks."""
        gen1 = TaskSetGenerator(seed=100)
        gen2 = TaskSetGenerator(seed=100)
        
        task1 = gen1.generate_random_task(num_nodes=10, edge_probability=0.1,
                                         num_objects=4, growth_factor=0.5,
                                         target_utilization=0.5)
        task2 = gen2.generate_random_task(num_nodes=10, edge_probability=0.1,
                                         num_objects=4, growth_factor=0.5,
                                         target_utilization=0.5)
        
        self.assertAlmostEqual(task1.workload(), task2.workload(), places=5)
        self.assertAlmostEqual(task1.period, task2.period, places=5)
    
    def test_task_set_generation(self):
        """Test task set generation from class."""
        gen = TaskSetGenerator(seed=42)
        tasks = gen.generate_task_set(num_tasks=5)
        
        self.assertEqual(len(tasks), 5)
    
    def test_grid_generation_creates_correct_count(self):
        """Test grid generation creates all parameter combinations."""
        gen = TaskSetGenerator(seed=42)
        tasks = gen.generate_grid_tasks(num_tasks_per_combination=1)
        
        expected_count = (len(TaskSetGenerator.NODE_COUNTS) *
                         len(TaskSetGenerator.EDGE_PROBABILITIES) *
                         len(TaskSetGenerator.NUM_OBJECTS) *
                         len(TaskSetGenerator.GROWTH_FACTORS) *
                         len(TaskSetGenerator.TARGET_UTILIZATIONS))
        
        self.assertEqual(len(tasks), expected_count)
    
    def test_constants_match_paper(self):
        """Test constants match paper Table IX."""
        self.assertEqual(TaskSetGenerator.NODE_COUNTS, [16, 32, 64])
        self.assertEqual(TaskSetGenerator.EDGE_PROBABILITIES, [0.02, 0.06, 0.12])
        self.assertEqual(TaskSetGenerator.NUM_OBJECTS, [4, 8, 16])
        self.assertEqual(TaskSetGenerator.GROWTH_FACTORS, [0.2, 0.6, 1.0])
        self.assertEqual(TaskSetGenerator.TARGET_UTILIZATIONS, [0.25, 0.50, 2.0, 4.0, 8.0, 16.0])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_single_node_task(self):
        """Test task with single node."""
        task = generate_dag_ot_task(
            task_id="single_node",
            num_nodes=1,
            edge_probability=0.0,
            num_objects=2,
            growth_factor=0.5,
            target_utilization=0.5
        )
        
        self.assertEqual(len(task.graph.nodes()), 1)
    
    def test_zero_edge_probability(self):
        """Test graph with no edges between original nodes."""
        task = generate_dag_ot_task(
            task_id="chain",
            num_nodes=5,
            edge_probability=0.0,
            num_objects=2,
            growth_factor=0.5,
            target_utilization=0.5
        )
        
        self.assertGreater(task.graph.number_of_edges(), 0)
    
    def test_high_edge_probability(self):
        """Test graph with high edge density."""
        task = generate_dag_ot_task(
            task_id="dense",
            num_nodes=5,
            edge_probability=1.0,
            num_objects=2,
            growth_factor=0.5,
            target_utilization=0.5
        )
        
        self.assertTrue(nx.is_directed_acyclic_graph(task.graph))
    
    def test_small_base_wcet(self):
        """Test with small base WCET."""
        task = generate_dag_ot_task(
            task_id="small_wcet",
            num_nodes=5,
            edge_probability=0.1,
            num_objects=2,
            growth_factor=0.5,
            target_utilization=0.5,
            base_wcet=10
        )
        
        self.assertGreater(task.workload(), 0)
    
    def test_high_target_utilization(self):
        """Test with high target utilization."""
        task = generate_dag_ot_task(
            task_id="high_u",
            num_nodes=10,
            edge_probability=0.1,
            num_objects=4,
            growth_factor=0.5,
            target_utilization=10.0
        )
        
        self.assertGreater(task.period, 0)


if __name__ == '__main__':
    unittest.main()