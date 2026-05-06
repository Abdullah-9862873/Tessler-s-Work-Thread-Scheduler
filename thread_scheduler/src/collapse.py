"""
Collapse Algorithm - DAGOT-REDUCE
Based on Section V of the paper (Algorithm 1)
"""

import random
import networkx as nx
import math
from typing import List, Tuple, Dict


def candidate_identification(dag) -> List[Tuple[str, str]]:
    """
    Find all candidate pairs for collapse (Definition 4).
    
    Candidates are pairs of nodes (u, v) where α_u = α_v (same object).
    
    Args:
        dag: DAG-OT task
    
    Returns:
        List of (node1, node2) tuples that are candidates for collapse
    """
    return dag.get_candidates()


def calculate_delta_workload(dag, node_u: str, node_v: str) -> float:
    """
    Calculate workload savings Δ from collapsing nodes (Equation 14).
    
    Formula: Δ = c_u(η_u) + c_v(η_v) - c_u(η_u + η_v)
    
    This represents how much total execution time we save by merging
    two nodes that run the same code (object).
    
    Args:
        dag: DAG-OT task
        node_u: First node name
        node_v: Second node name
    
    Returns:
        Workload savings (positive means reduction)
    """
    node_u_data = dag.graph.nodes[node_u]
    node_v_data = dag.graph.nodes[node_v]
    
    eta_u = node_u_data['num_threads']
    eta_v = node_v_data['num_threads']
    wceto_func = node_u_data['wceto_func']  # Same for both nodes (same object)
    
    c_u = wceto_func(eta_u)
    c_v = wceto_func(eta_v)
    c_collapsed = wceto_func(eta_u + eta_v)
    
    return (c_u + c_v) - c_collapsed


def calculate_penalty(dag, node_u: str, node_v: str) -> float:
    """
    Calculate critical path extension γ from collapsing nodes (Equation 15).
    
    Formula: γ = L̂_i - L_i
    
    This measures how much the longest path through the DAG changes
    after collapsing two nodes. We want this to be small or negative!
    
    Args:
        dag: DAG-OT task
        node_u: First node name
        node_v: Second node name
    
    Returns:
        Change in critical path (positive = extension, negative = reduction)
        Returns infinity if collapse creates a cycle
    """
    try:
        original_critical_path = dag.critical_path_length()
    except ValueError:
        return float('inf')  # Original graph has cycle
    
    original_graph = dag.graph.copy()
    
    # Perform temporary collapse to see new critical path
    try:
        collapse_nodes(dag, node_u, node_v)
        try:
            new_critical_path = dag.critical_path_length()
        except ValueError:
            new_critical_path = float('inf')  # Collapse creates cycle
    except Exception:
        new_critical_path = float('inf')
    finally:
        # Restore original graph
        dag.graph = original_graph
    
    return new_critical_path - original_critical_path


def check_cycles_after_collapse(dag, node_u: str, node_v: str) -> bool:
    """
    Check if collapsing nodes u and v would introduce a cycle.
    
    We need to ensure the DAG stays acyclic after collapse.
    This is one of the conditions for a "beneficial" collapse.
    
    Args:
        dag: DAG-OT task
        node_u: First node name
        node_v: Second node name
    
    Returns:
        True if collapse would introduce a cycle (bad!)
    """
    # Create temporary collapsed version to check for cycles
    temp_graph = dag.graph.copy()
    
    node_u_data = dag.graph.nodes[node_u]
    node_v_data = dag.graph.nodes[node_v]
    
    eta_u = node_u_data['num_threads']
    eta_v = node_v_data['num_threads']
    new_eta = eta_u + eta_v
    wceto_func = node_u_data['wceto_func']
    object_id = node_u_data['object_id']
    
    # Remove original nodes
    temp_graph.remove_node(node_u)
    temp_graph.remove_node(node_v)
    
    # Add collapsed node
    collapsed_name = f"{node_u}_collapsed"
    temp_graph.add_node(collapsed_name,
                      object_id=object_id,
                      num_threads=new_eta,
                      wceto_func=wceto_func)
    
    # Get all predecessors and successors
    predecessors_u = set(dag.graph.predecessors(node_u))
    predecessors_v = set(dag.graph.predecessors(node_v))
    successors_u = set(dag.graph.successors(node_u))
    successors_v = set(dag.graph.successors(node_v))
    
    # Union of predecessors and successors (excluding each other)
    all_predecessors = (predecessors_u | predecessors_v) - {node_u, node_v}
    all_successors = (successors_u | successors_v) - {node_u, node_v}
    
    # Add edges from predecessors to collapsed node
    for pred in all_predecessors:
        temp_graph.add_edge(pred, collapsed_name)
    
    # Add edges from collapsed node to successors
    for succ in all_successors:
        temp_graph.add_edge(collapsed_name, succ)
    
    # Check for cycles
    try:
        list(nx.find_cycle(temp_graph))
        return True  # Cycle found - bad!
    except nx.NetworkXNoCycle:
        return False  # No cycle - good!


def collapse_nodes(dag, node_u: str, node_v: str) -> None:
    """
    Collapse nodes u and v into a single node (Definition 5).
    
    When we collapse:
    - η_û ← η_u + η_v (join threads together)
    - α_û ← α_u (same object)
    - c_û ← c_u (same WCETO function)
    - Update edges: redirect all incoming/outgoing edges
    
    This is the key operation that reduces workload!
    
    Args:
        dag: DAG-OT task
        node_u: First node to collapse (will be removed)
        node_v: Second node to collapse (will be removed)
    """
    node_u_data = dag.graph.nodes[node_u]
    node_v_data = dag.graph.nodes[node_v]
    
    eta_u = node_u_data['num_threads']
    eta_v = node_v_data['num_threads']
    new_eta = eta_u + eta_v
    
    wceto_func = node_u_data['wceto_func']
    object_id = node_u_data['object_id']
    
    # Create new collapsed node name
    collapsed_name = f"{node_u}_collapsed"
    
    # Get all predecessors and successors
    predecessors_u = set(dag.graph.predecessors(node_u))
    predecessors_v = set(dag.graph.predecessors(node_v))
    successors_u = set(dag.graph.successors(node_u))
    successors_v = set(dag.graph.successors(node_v))
    
    # Union of predecessors and successors (excluding each other)
    all_predecessors = (predecessors_u | predecessors_v) - {node_u, node_v}
    all_successors = (successors_u | successors_v) - {node_u, node_v}
    
    # Remove old nodes
    dag.graph.remove_node(node_u)
    dag.graph.remove_node(node_v)
    
    # Add collapsed node
    dag.graph.add_node(collapsed_name,
                      object_id=object_id,
                      num_threads=new_eta,
                      wceto_func=wceto_func)
    
    # Add edges from predecessors to collapsed node
    for pred in all_predecessors:
        dag.graph.add_edge(pred, collapsed_name)
    
    # Add edges from collapsed node to successors
    for succ in all_successors:
        dag.graph.add_edge(collapsed_name, succ)
    
    # Update nodes_by_object tracking
    if object_id in dag._nodes_by_object:
        dag._nodes_by_object[object_id] = [
            n for n in dag._nodes_by_object[object_id] 
            if n != node_u and n != node_v
        ]
        dag._nodes_by_object[object_id].append(collapsed_name)


def check_beneficial_collapse(dag, node_u: str, node_v: str, original_cores: int) -> bool:
    """
    Check if collapse is beneficial (Definition 7).
    
    A collapse is "beneficial" if ALL three conditions are met:
    1. Post-collapse DAG contains no cycles
    2. If L_i ≤ D_i pre-collapse, then L̂_i ≤ D_i post-collapse (deadline still met)
    3. m̂_i ≺ m_i (improved core allocation)
    
    This ensures we don't make things worse!
    
    Args:
        dag: DAG-OT task
        node_u: First node
        node_v: Second node
        original_cores: Original core allocation m_i
    
    Returns:
        True if collapse is beneficial
    """
    # Check 1: No cycles
    if check_cycles_after_collapse(dag, node_u, node_v):
        return False
    
    # Check 2: Deadline still met (if originally met)
    original_critical_path = dag.critical_path_length()
    
    # Temporarily collapse to check new critical path
    temp_graph = dag.graph.copy()
    collapse_nodes(dag, node_u, node_v)
    new_critical_path = dag.critical_path_length()
    dag.graph = temp_graph
    
    # If originally feasible, must stay feasible
    if original_critical_path <= dag.deadline:
        if new_critical_path > dag.deadline:
            return False
    
    # Check 3: Improved core allocation
    temp_graph = dag.graph.copy()
    collapse_nodes(dag, node_u, node_v)
    new_workload = dag.workload()
    new_critical_path = dag.critical_path_length()
    dag.graph = temp_graph
    
    # Calculate new core allocation: m̂_i = ceil((Ĉ_i - L̂_i) / (D_i - L̂_i))
    if new_critical_path >= dag.deadline:
        new_cores = float('inf')  # Infeasible
    else:
        numerator = new_workload - new_critical_path
        denominator = dag.deadline - new_critical_path
        new_cores = math.ceil(numerator / denominator) if denominator > 0 else float('inf')
    
    # Improved means: if original > 0, new is between 0 and original
    if original_cores > 0:
        return 0 < new_cores <= original_cores
    else:
        return new_cores > original_cores


def order_by_greatest_benefit(candidates: List[Tuple[str, str]], dag) -> List[Tuple[str, str]]:
    """
    Order candidates by descending workload savings (Equation 14).
    
    Δ = c_u(η_u) + c_v(η_v) - c_u(η_u + η_v)
    
    This heuristic picks the pairs that give the most workload reduction first.
    Simple and effective!
    
    Args:
        candidates: List of candidate pairs
        dag: DAG-OT task
    
    Returns:
        Sorted list of candidate pairs (highest Δ first)
    """
    def get_delta(pair):
        return calculate_delta_workload(dag, pair[0], pair[1])
    
    return sorted(candidates, key=get_delta, reverse=True)


def order_by_least_penalty(candidates: List[Tuple[str, str]], dag) -> List[Tuple[str, str]]:
    """
    Order candidates by increasing critical path extension (Equation 15).
    
    γ = L̂_i - L_i
    
    This heuristic picks pairs that change the critical path the least.
    May allow more collapses overall!
    
    Args:
        candidates: List of candidate pairs
        dag: DAG-OT task
    
    Returns:
        Sorted list of candidate pairs (lowest γ first)
    """
    def get_penalty(pair):
        return calculate_penalty(dag, pair[0], pair[1])
    
    return sorted(candidates, key=get_penalty)


def order_arbitrary(candidates: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """
    Random ordering (arbitrary baseline).
    
    Used as a baseline to compare against the smart heuristics.
    
    Args:
        candidates: List of candidate pairs
    
    Returns:
        Shuffled list of candidate pairs
    """
    result = list(candidates)
    random.shuffle(result)
    return result


def dagot_reduce(dag, heuristic: str = "greatest_benefit") -> Dict:
    """
    Main DAGOT-REDUCE algorithm (Algorithm 1 from the paper).
    
    This is the core algorithm that makes everything work!
    
    procedure DAGOT-REDUCE(G_i):
        A ← CANDIDATES(G_i)       # Find all (u,v) pairs where α_u = α_v
        A ← ORDER(A)               # Apply heuristic ordering
        while |A| ≠ 0:
            (u, v) ← FIRST(A)
            A ← A \ (u, v)
            if BENEFIT(G_i, u, v):  # Definition 7
                COLLAPSE(G_i, u, v) # Definition 5
    
    Args:
        dag: DAG-OT task to reduce
        heuristic: Ordering heuristic ("greatest_benefit", "least_penalty", "arbitrary")
    
    Returns:
        Dictionary with metrics:
            - 'collapsed_pairs': List of collapsed node pairs
            - 'original_cores': Core allocation before collapse
            - 'final_cores': Core allocation after collapse
            - 'core_saved': Number of cores saved
            - 'original_workload': Workload before
            - 'final_workload': Workload after
            - 'workload_saved': Workload reduction
            - 'original_critical_path': Critical path before
            - 'final_critical_path': Critical path after
    """
    # Calculate original metrics
    original_workload = dag.workload()
    original_critical_path = dag.critical_path_length()
    
    if original_critical_path >= dag.deadline:
        original_cores = -1  # Infeasible
    else:
        numerator = original_workload - original_critical_path
        denominator = dag.deadline - original_critical_path
        original_cores = math.ceil(numerator / denominator) if denominator > 0 else float('inf')
    
    # Find candidates
    candidates = candidate_identification(dag)
    
    # Order candidates based on heuristic
    if heuristic == "greatest_benefit":
        ordered_candidates = order_by_greatest_benefit(candidates, dag)
    elif heuristic == "least_penalty":
        ordered_candidates = order_by_least_penalty(candidates, dag)
    else:  # arbitrary
        ordered_candidates = order_arbitrary(candidates)
    
    # Track collapsed pairs
    collapsed_pairs = []
    
    # Process each candidate
    for node_u, node_v in ordered_candidates:
        # Skip if nodes were already collapsed
        if node_u not in dag.graph.nodes or node_v not in dag.graph.nodes:
            continue
        
        # Check if beneficial
        if check_beneficial_collapse(dag, node_u, node_v, original_cores):
            collapse_nodes(dag, node_u, node_v)
            collapsed_pairs.append((node_u, node_v))
    
    # Calculate final metrics
    final_workload = dag.workload()
    final_critical_path = dag.critical_path_length()
    
    if final_critical_path >= dag.deadline:
        final_cores = -1  # Infeasible
    else:
        numerator = final_workload - final_critical_path
        denominator = dag.deadline - final_critical_path
        final_cores = math.ceil(numerator / denominator) if denominator > 0 else float('inf')
    
    return {
        'collapsed_pairs': collapsed_pairs,
        'original_cores': original_cores,
        'final_cores': final_cores,
        'core_saved': max(0, original_cores - final_cores) if original_cores > 0 else 0,
        'original_workload': original_workload,
        'final_workload': final_workload,
        'workload_saved': original_workload - final_workload,
        'original_critical_path': original_critical_path,
        'final_critical_path': final_critical_path
    }