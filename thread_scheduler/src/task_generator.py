"""
Synthetic Task Generator — based on Section IX pipeline.
"""

import random
import networkx as nx
from .dag_model import DAGNode, DAGTask
from .growth_factor import create_growth_factor_wceto


def generate_dag_structure(num_nodes, edge_probability, seed=None):
    """Create a random DAG with the given number of nodes and edge probability."""
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
    """Add virtual source/sink nodes if the DAG has multiple entries or exits."""
    G = G.copy()
    added_source = added_sink = False

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
    """Generate a complete DAG-OT task with the given parameters."""
    if seed is not None:
        random.seed(seed)

    G = generate_dag_structure(num_nodes, edge_probability)
    G, added_source, added_sink = ensure_single_source_sink(G)

    task = DAGTask(task_id=task_id, period=1.0, deadline=1.0)

    node_object_map = {}
    for node_id in G.nodes():
        node_object_map[node_id] = random.randint(0, num_objects - 1)

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
    """Generate multiple tasks with similar parameters."""
    if seed is not None:
        random.seed(seed)

    util_per_task = target_utilization / num_tasks
    tasks = []
    for i in range(num_tasks):
        task_seed = None if seed is None else seed + i
        tasks.append(generate_dag_ot_task(
            task_id=f"task{i}",
            num_nodes=num_nodes, edge_probability=edge_probability,
            num_objects=num_objects, growth_factor=growth_factor,
            target_utilization=util_per_task, base_wcet=base_wcet,
            seed=task_seed
        ))
    return tasks


class TaskSetGenerator:
    """
    Generates task sets using parameter ranges from Table IX:
    nodes in {16,32,64}, edges in {0.02,0.06,0.12}, objects in {4,8,16},
    growth factors in {0.2,0.6,1.0}, utilizations in {0.25,0.5,2,4,8,16}.
    """

    NODE_COUNTS = [16, 32, 64]
    EDGE_PROBABILITIES = [0.02, 0.06, 0.12]
    NUM_OBJECTS = [4, 8, 16]
    GROWTH_FACTORS = [0.2, 0.6, 1.0]
    TARGET_UTILIZATIONS = [0.25, 0.50, 2.0, 4.0, 8.0, 16.0]

    def __init__(self, seed=None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_random_task(self, num_nodes=None, edge_probability=None,
                            num_objects=None, growth_factor=None,
                            target_utilization=None, base_wcet=100):
        num_nodes = num_nodes or random.choice(self.NODE_COUNTS)
        edge_probability = edge_probability or random.choice(self.EDGE_PROBABILITIES)
        num_objects = num_objects or random.choice(self.NUM_OBJECTS)
        growth_factor = growth_factor or random.choice(self.GROWTH_FACTORS)
        target_utilization = target_utilization or random.choice(self.TARGET_UTILIZATIONS)

        task_seed = None if self.seed is None else random.randint(0, 100000)
        return generate_dag_ot_task(
            task_id=f"task_{random.randint(0, 100000)}",
            num_nodes=num_nodes, edge_probability=edge_probability,
            num_objects=num_objects, growth_factor=growth_factor,
            target_utilization=target_utilization, base_wcet=base_wcet,
            seed=task_seed
        )

    def generate_task_set(self, num_tasks, num_nodes=None, edge_probability=None,
                         num_objects=None, growth_factor=None,
                         target_utilization=None, base_wcet=100):
        num_nodes = num_nodes or random.choice(self.NODE_COUNTS)
        edge_probability = edge_probability or random.choice(self.EDGE_PROBABILITIES)
        num_objects = num_objects or random.choice(self.NUM_OBJECTS)
        growth_factor = growth_factor or random.choice(self.GROWTH_FACTORS)
        target_utilization = target_utilization or random.choice(self.TARGET_UTILIZATIONS)

        return generate_task_set(
            num_tasks=num_tasks, num_nodes=num_nodes,
            edge_probability=edge_probability, num_objects=num_objects,
            growth_factor=growth_factor, target_utilization=target_utilization,
            base_wcet=base_wcet, seed=self.seed
        )

    def generate_grid_tasks(self, num_tasks_per_combination=1):
        """Generate one task for every parameter combination (grid search)."""
        tasks = []
        for n in self.NODE_COUNTS:
            for ep in self.EDGE_PROBABILITIES:
                for no in self.NUM_OBJECTS:
                    for gf in self.GROWTH_FACTORS:
                        for tu in self.TARGET_UTILIZATIONS:
                            for i in range(num_tasks_per_combination):
                                s = None if self.seed is None else self.seed + i
                                tasks.append(generate_dag_ot_task(
                                    task_id=f"task_{len(tasks)}",
                                    num_nodes=n, edge_probability=ep,
                                    num_objects=no, growth_factor=gf,
                                    target_utilization=tu, base_wcet=100, seed=s
                                ))
        return tasks