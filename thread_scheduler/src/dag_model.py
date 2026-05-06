"""
DAG-OT Model - DAG with Objects and Threads
Based on Section III-D of the paper
"""

import networkx as nx
from typing import Optional, Callable, List


class DAGNode:
    """
    Node in a DAG-OT task.
    Node v = ⟨α, c(η), η⟩ where:
        α = executable object identifier
        c(η) = WCETO function (worst-case execution time + cache overhead)
        η = number of threads
    """
    
    def __init__(self, object_id: str, wceto_func: Callable, num_threads: int = 1):
        """
        Initialize a DAG-OT node.
        
        Args:
            object_id: Identifier for the executable object (α)
            wceto_func: Function c(η) that returns WCETO for η threads
            num_threads: Number of threads (η), defaults to 1
        """
        self.object_id = object_id
        self.wceto_func = wceto_func
        self.num_threads = num_threads
    
    def wceto(self, eta: Optional[int] = None) -> float:
        """
        Get WCETO for the node.
        
        Args:
            eta: Number of threads. If None, uses self.num_threads
        
        Returns:
            WCETO value
        """
        if eta is None:
            eta = self.num_threads
        return self.wceto_func(eta)
    
    def __repr__(self):
        return f"DAGNode(α={self.object_id}, η={self.num_threads}, c(η)={self.wceto():.2f})"


class DAGTask:
    """
    Full DAG-OT task with period and deadline.
    τ_i = (T_i, D_i, G_i) where G_i = (V_i, E_i)
    """
    
    def __init__(self, task_id: str, period: float, deadline: float = None):
        """
        Initialize a DAG-OT task.
        
        Args:
            task_id: Unique identifier for this task
            period: Minimum inter-arrival time (T_i)
            deadline: Relative deadline (D_i), defaults to period (implicit deadline)
        """
        self.task_id = task_id
        self.period = period
        self.deadline = deadline if deadline is not None else period
        
        self.graph = nx.DiGraph()
        self._nodes_by_object = {}
    
    def add_node(self, node: DAGNode, node_name: str) -> None:
        """
        Add a node to the DAG.
        
        Args:
            node: DAGNode to add
            node_name: Unique name for this node in the graph
        """
        self.graph.add_node(node_name, 
                           object_id=node.object_id,
                           num_threads=node.num_threads,
                           wceto_func=node.wceto_func)
        
        if node.object_id not in self._nodes_by_object:
            self._nodes_by_object[node.object_id] = []
        self._nodes_by_object[node.object_id].append(node_name)
    
    def add_edge(self, from_node: str, to_node: str) -> None:
        """
        Add a directed edge between nodes (precedence constraint).
        
        Args:
            from_node: Source node name
            to_node: Target node name
        """
        self.graph.add_edge(from_node, to_node)
    
    def critical_path_length(self) -> float:
        """
        Calculate critical path length L_i (Equation 6).
        L_i = Σ_{v∈λ_i} c_v(η_v) where λ_i is the critical path
        """
        try:
            topo_order = list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            raise ValueError("Graph contains a cycle - not a valid DAG")
        
        longest_path = {}
        for node in topo_order:
            node_data = self.graph.nodes[node]
            eta = node_data['num_threads']
            wceto = node_data['wceto_func'](eta)
            
            predecessors = list(self.graph.predecessors(node))
            if not predecessors:
                longest_path[node] = wceto
            else:
                longest_path[node] = wceto + max(longest_path[p] for p in predecessors)
        
        return max(longest_path.values()) if longest_path else 0.0
    
    def workload(self) -> float:
        """
        Calculate total workload C_i (Equation 7).
        C_i = Σ_{v∈V_i} c_v(η_v)
        """
        total = 0.0
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            eta = node_data['num_threads']
            wceto = node_data['wceto_func'](eta)
            total += wceto
        return total
    
    def utilization(self) -> float:
        """
        Calculate utilization u_i (Equation 3).
        u_i = C_i / T_i
        """
        return self.workload() / self.period
    
    def get_candidates(self) -> List[tuple]:
        """
        Find all candidate pairs for collapse (Definition 4).
        Candidates are nodes that share the same executable object α.
        
        Returns:
            List of (node1, node2) tuples that are candidates
        """
        candidates = []
        for object_id, nodes in self._nodes_by_object.items():
            if len(nodes) >= 2:
                for i in range(len(nodes)):
                    for j in range(i + 1, len(nodes)):
                        candidates.append((nodes[i], nodes[j]))
        return candidates
    
    def get_nodes_by_object(self, object_id: str) -> List[str]:
        """Get all nodes with a specific object ID."""
        return self._nodes_by_object.get(object_id, [])
    
    def num_nodes(self) -> int:
        """Return number of nodes in the DAG."""
        return self.graph.number_of_nodes()
    
    def __repr__(self):
        return f"DAGTask({self.task_id}, nodes={self.num_nodes()}, C={self.workload():.2f}, L={self.critical_path_length():.2f})"