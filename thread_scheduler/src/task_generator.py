"""
Synthetic Task Generator
Based on Section IX of the paper (pipeline)

This module generates synthetic DAG-OT tasks for evaluation.
"""

import random
import networkx as nx
from .dag_model import DAGNode, DAGTask
from .growth_factor import create_growth_factor_wceto


def generate_dag_structure(num_nodes, edge_probability, seed=None):
    """
    Create random DAG with specified number of nodes.
    
    Args:
        num_nodes: Number of nodes to create
        edge_probability: Probability of adding each possible edge
        seed: Optional random seed for reproducibility
        
    Returns:
        networkx DiGraph representing the DAG
    """
    if seed is not None:
        random.seed(seed)
    
    G = nx.DiGraph()
    G.add_nodes_from(range(num_nodes))
    
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if random.random() < edge_probability:
                G.add_edge(i, j)
    
    if not nx.is_directed_acyclic_graph(G):
        G = nx.transitive_reduction(G)
    
    return G


def ensure_single_source_sink(G):
    """
    Ensure the DAG has exactly one source (entry) and one sink (exit).
    
    Args:
        G: networkx DiGraph
        
    Returns:
        tuple: (modified_graph, added_source_node, added_sink_node)
    """
    G = G.copy()
    added_source = False
    added_sink = False
    
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]
    sinks = [n for n in G.nodes() if G.out_degree(n) == 0]
    
    if len(sources) > 1:
        new_source = "source"
        while new_source in G.nodes():
            new_source = f"source_{random.randint(0, 10000)}"
        G.add_node(new_source)
        for s in sources:
            G.add_edge(new_source, s)
        added_source = True
    
    if len(sinks) > 1:
        new_sink = "sink"
        while new_sink in G.nodes():
            new_sink = f"sink_{random.randint(0, 10000)}"
        G.add_node(new_sink)
        for s in sinks:
            G.add_edge(s, new_sink)
        added_sink = True
    
    return G, added_source, added_sink


def generate_dag_ot_task(task_id, num_nodes, edge_probability, num_objects,
                         growth_factor, target_utilization, base_wcet=100, seed=None):
    """
    Complete pipeline to generate a DAG-OT task.
    
    Args:
        task_id: Unique identifier for the task
        num_nodes: Number of nodes in the DAG
        edge_probability: Probability of adding each edge
        num_objects: Number of unique objects (executables)
        growth_factor: Cache benefit parameter F (0-1)
        target_utilization: Target utilization to achieve (U)
        base_wcet: Base WCET for single thread execution
        seed: Optional random seed for reproducibility
        
    Returns:
        DAGTask object with all properties set
    """
    if seed is not None:
        random.seed(seed)
    
    G = generate_dag_structure(num_nodes, edge_probability)
    G, added_source, added_sink = ensure_single_source_sink(G)
    
    task = DAGTask(task_id=task_id, period=1.0, deadline=1.0)
    
    node_object_map = {}
    for node_id in G.nodes():
        obj_id = random.randint(0, num_objects - 1)
        node_object_map[node_id] = obj_id
    
    if added_source:
        source_nodes = [n for n in G.nodes() if G.in_degree(n) == 0 and n != "source"]
        if source_nodes:
            obj_id = random.randint(0, num_objects - 1)
            node_object_map["source"] = obj_id
    
    if added_sink:
        sink_nodes = [n for n in G.nodes() if G.out_degree(n) == 0 and n != "sink"]
        if sink_nodes:
            obj_id = random.randint(0, num_objects - 1)
            node_object_map["sink"] = obj_id
    
    for node_id in G.nodes():
        obj_id = node_object_map[node_id]
        wceto_func = create_growth_factor_wceto(base_wcet, growth_factor)
        node = DAGNode(object_id=obj_id, wceto_func=wceto_func, num_threads=1)
        task.add_node(node, str(node_id))
    
    for u, v in G.edges():
        task.add_edge(str(u), str(v))
    
    workload = task.workload()
    if workload > 0:
        period = workload / target_utilization
        task.period = period
        task.deadline = period
    
    return task


def generate_task_set(num_tasks, num_nodes, edge_probability, num_objects,
                      growth_factor, target_utilization, base_wcet=100, seed=None):
    """
    Generate multiple tasks with similar parameters.
    
    Args:
        num_tasks: Number of tasks to generate
        num_nodes: Nodes per task
        edge_probability: Edge probability per task
        num_objects: Number of unique objects
        growth_factor: Cache benefit parameter
        target_utilization: Total target utilization (split across tasks)
        base_wcet: Base WCET
        seed: Optional random seed
        
    Returns:
        list of DAGTask objects
    """
    if seed is not None:
        random.seed(seed)
    
    utilization_per_task = target_utilization / num_tasks
    tasks = []
    
    for i in range(num_tasks):
        task_seed = None if seed is None else seed + i
        task = generate_dag_ot_task(
            task_id=f"task{i}",
            num_nodes=num_nodes,
            edge_probability=edge_probability,
            num_objects=num_objects,
            growth_factor=growth_factor,
            target_utilization=utilization_per_task,
            base_wcet=base_wcet,
            seed=task_seed
        )
        tasks.append(task)
    
    return tasks


class TaskSetGenerator:
    """
    Class for generating task sets based on paper parameters.
    
    Constants from Table IX in the paper:
    - NODE_COUNTS: [16, 32, 64]
    - EDGE_PROBABILITIES: [0.02, 0.06, 0.12]
    - NUM_OBJECTS: [4, 8, 16]
    - GROWTH_FACTORS: [0.2, 0.6, 1.0]
    - TARGET_UTILIZATIONS: [0.25, 0.50, 2.0, 4.0, 8.0, 16.0]
    """
    
    NODE_COUNTS = [16, 32, 64]
    EDGE_PROBABILITIES = [0.02, 0.06, 0.12]
    NUM_OBJECTS = [4, 8, 16]
    GROWTH_FACTORS = [0.2, 0.6, 1.0]
    TARGET_UTILIZATIONS = [0.25, 0.50, 2.0, 4.0, 8.0, 16.0]
    
    def __init__(self, seed=None):
        """
        Initialize generator with random seed.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate_random_task(self, num_nodes=None, edge_probability=None,
                            num_objects=None, growth_factor=None,
                            target_utilization=None, base_wcet=100):
        """
        Generate a single random task.
        
        Args:
            num_nodes: Override default random selection
            edge_probability: Override default random selection
            num_objects: Override default random selection
            growth_factor: Override default random selection
            target_utilization: Override default random selection
            base_wcet: Base WCET value
            
        Returns:
            DAGTask object
        """
        if num_nodes is None:
            num_nodes = random.choice(self.NODE_COUNTS)
        if edge_probability is None:
            edge_probability = random.choice(self.EDGE_PROBABILITIES)
        if num_objects is None:
            num_objects = random.choice(self.NUM_OBJECTS)
        if growth_factor is None:
            growth_factor = random.choice(self.GROWTH_FACTORS)
        if target_utilization is None:
            target_utilization = random.choice(self.TARGET_UTILIZATIONS)
        
        task_seed = None if self.seed is None else random.randint(0, 100000)
        
        return generate_dag_ot_task(
            task_id=f"task_{random.randint(0, 100000)}",
            num_nodes=num_nodes,
            edge_probability=edge_probability,
            num_objects=num_objects,
            growth_factor=growth_factor,
            target_utilization=target_utilization,
            base_wcet=base_wcet,
            seed=task_seed
        )
    
    def generate_task_set(self, num_tasks, num_nodes=None, edge_probability=None,
                         num_objects=None, growth_factor=None,
                         target_utilization=None, base_wcet=100):
        """
        Generate multiple random tasks.
        
        Args:
            num_tasks: Number of tasks to generate
            Other args: Same as generate_random_task
            
        Returns:
            list of DAGTask objects
        """
        if num_nodes is None:
            num_nodes = random.choice(self.NODE_COUNTS)
        if edge_probability is None:
            edge_probability = random.choice(self.EDGE_PROBABILITIES)
        if num_objects is None:
            num_objects = random.choice(self.NUM_OBJECTS)
        if growth_factor is None:
            growth_factor = random.choice(self.GROWTH_FACTORS)
        if target_utilization is None:
            target_utilization = random.choice(self.TARGET_UTILIZATIONS)
        
        return generate_task_set(
            num_tasks=num_tasks,
            num_nodes=num_nodes,
            edge_probability=edge_probability,
            num_objects=num_objects,
            growth_factor=growth_factor,
            target_utilization=target_utilization,
            base_wcet=base_wcet,
            seed=self.seed
        )
    
    def generate_grid_tasks(self, num_tasks_per_combination=1):
        """
        Generate all parameter combinations (grid search).
        
        Args:
            num_tasks_per_combination: Tasks per parameter combination
            
        Returns:
            list of all DAGTask objects
        """
        tasks = []
        
        for num_nodes in self.NODE_COUNTS:
            for edge_prob in self.EDGE_PROBABILITIES:
                for num_objs in self.NUM_OBJECTS:
                    for growth_f in self.GROWTH_FACTORS:
                        for target_u in self.TARGET_UTILIZATIONS:
                            for i in range(num_tasks_per_combination):
                                task_seed = None if self.seed is None else self.seed + i
                                task = generate_dag_ot_task(
                                    task_id=f"task_{len(tasks)}",
                                    num_nodes=num_nodes,
                                    edge_probability=edge_prob,
                                    num_objects=num_objs,
                                    growth_factor=growth_f,
                                    target_utilization=target_u,
                                    base_wcet=100,
                                    seed=task_seed
                                )
                                tasks.append(task)
        
        return tasks