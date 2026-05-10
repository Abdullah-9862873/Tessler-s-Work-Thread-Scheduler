"""
DAG-OT Model
Definitions from Section III-D of the paper.
"""

import networkx as nx
from typing import Optional, Callable, List


class DAGNode:
    """
    Node in a DAG-OT task.
    v = <alpha, c(eta), eta> where alpha is the executable object,
    c(eta) is the WCETO function, and eta is the thread count.
    """

    def __init__(self, object_id: str, wceto_func: Callable, num_threads: int = 1):
        self.object_id = object_id
        self.wceto_func = wceto_func
        self.num_threads = num_threads

    def wceto(self, eta: Optional[int] = None) -> float:
        if eta is None:
            eta = self.num_threads
        return self.wceto_func(eta)

    def __repr__(self):
        return f"DAGNode(α={self.object_id}, η={self.num_threads}, c(η)={self.wceto():.2f})"


class DAGTask:
    """
    Full DAG-OT task: τ_i = (T_i, D_i, G_i) where G_i = (V_i, E_i).
    """

    def __init__(self, task_id: str, period: float, deadline: float = None):
        self.task_id = task_id
        self.period = period
        self.deadline = deadline if deadline is not None else period
        self.graph = nx.DiGraph()
        self._nodes_by_object = {}

    def add_node(self, node: DAGNode, node_name: str) -> None:
        self.graph.add_node(node_name,
                           object_id=node.object_id,
                           num_threads=node.num_threads,
                           wceto_func=node.wceto_func)

        if node.object_id not in self._nodes_by_object:
            self._nodes_by_object[node.object_id] = []
        self._nodes_by_object[node.object_id].append(node_name)

    def add_edge(self, from_node: str, to_node: str) -> None:
        self.graph.add_edge(from_node, to_node)

    def critical_path_length(self) -> float:
        """L_i = max path sum of c_v(η_v) through the DAG (Eq. 6)."""
        try:
            topo_order = list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            raise ValueError("Graph contains a cycle - not a valid DAG")

        longest_path = {}
        for node in topo_order:
            nd = self.graph.nodes[node]
            wceto = nd['wceto_func'](nd['num_threads'])
            preds = list(self.graph.predecessors(node))
            if not preds:
                longest_path[node] = wceto
            else:
                longest_path[node] = wceto + max(longest_path[p] for p in preds)

        return max(longest_path.values()) if longest_path else 0.0

    def workload(self) -> float:
        """C_i = sum of c_v(η_v) over all nodes (Eq. 7)."""
        total = 0.0
        for node in self.graph.nodes():
            nd = self.graph.nodes[node]
            total += nd['wceto_func'](nd['num_threads'])
        return total

    def utilization(self) -> float:
        """u_i = C_i / T_i (Eq. 3)."""
        return self.workload() / self.period

    def get_candidates(self) -> List[tuple]:
        """All (u, v) pairs where α_u = α_v (Definition 4)."""
        candidates = []
        for object_id, nodes in self._nodes_by_object.items():
            if len(nodes) >= 2:
                for i in range(len(nodes)):
                    for j in range(i + 1, len(nodes)):
                        candidates.append((nodes[i], nodes[j]))
        return candidates

    def get_nodes_by_object(self, object_id: str) -> List[str]:
        return self._nodes_by_object.get(object_id, [])

    def num_nodes(self) -> int:
        return self.graph.number_of_nodes()

    def __repr__(self):
        return f"DAGTask({self.task_id}, nodes={self.num_nodes()}, C={self.workload():.2f}, L={self.critical_path_length():.2f})"