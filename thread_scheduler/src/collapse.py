"""
DAGOT-REDUCE — Algorithm 1 from Section V.
"""

import random
import networkx as nx
import math
from typing import List, Tuple, Dict


def candidate_identification(dag) -> List[Tuple[str, str]]:
    """All (u, v) pairs where α_u = α_v (Definition 4)."""
    return dag.get_candidates()


def calculate_delta_workload(dag, node_u: str, node_v: str) -> float:
    """
    Workload savings from collapsing u and v (Eq. 14).
    Δ = c_u(η_u) + c_v(η_v) - c_u(η_u + η_v)
    """
    u_data = dag.graph.nodes[node_u]
    v_data = dag.graph.nodes[node_v]
    eta_u, eta_v = u_data['num_threads'], v_data['num_threads']
    wceto_func = u_data['wceto_func']
    return wceto_func(eta_u) + wceto_func(eta_v) - wceto_func(eta_u + eta_v)


def calculate_penalty(dag, node_u: str, node_v: str) -> float:
    """
    Critical path extension from collapsing u and v (Eq. 15).
    γ = L_hat - L. Returns inf if collapse creates a cycle.
    """
    try:
        original_cp = dag.critical_path_length()
    except ValueError:
        return float('inf')

    saved_graph = dag.graph.copy()
    try:
        collapse_nodes(dag, node_u, node_v)
        try:
            new_cp = dag.critical_path_length()
        except ValueError:
            new_cp = float('inf')
    except Exception:
        new_cp = float('inf')
    finally:
        dag.graph = saved_graph

    return new_cp - original_cp


def check_cycles_after_collapse(dag, node_u: str, node_v: str) -> bool:
    """True if collapsing u, v would introduce a cycle."""
    temp = dag.graph.copy()

    u_data = dag.graph.nodes[node_u]
    v_data = dag.graph.nodes[node_v]
    new_eta = u_data['num_threads'] + v_data['num_threads']

    temp.remove_node(node_u)
    temp.remove_node(node_v)

    collapsed_name = f"{node_u}_collapsed"
    temp.add_node(collapsed_name,
                  object_id=u_data['object_id'],
                  num_threads=new_eta,
                  wceto_func=u_data['wceto_func'])

    preds = (set(dag.graph.predecessors(node_u)) | set(dag.graph.predecessors(node_v))) - {node_u, node_v}
    succs = (set(dag.graph.successors(node_u)) | set(dag.graph.successors(node_v))) - {node_u, node_v}

    for p in preds:
        temp.add_edge(p, collapsed_name)
    for s in succs:
        temp.add_edge(collapsed_name, s)

    try:
        list(nx.find_cycle(temp))
        return True
    except nx.NetworkXNoCycle:
        return False


def collapse_nodes(dag, node_u: str, node_v: str) -> None:
    """
    Collapse u and v into a single node (Definition 5).
    η_new = η_u + η_v, edges are redirected accordingly.
    """
    u_data = dag.graph.nodes[node_u]
    v_data = dag.graph.nodes[node_v]
    new_eta = u_data['num_threads'] + v_data['num_threads']
    wceto_func = u_data['wceto_func']
    object_id = u_data['object_id']
    collapsed_name = f"{node_u}_collapsed"

    preds = (set(dag.graph.predecessors(node_u)) | set(dag.graph.predecessors(node_v))) - {node_u, node_v}
    succs = (set(dag.graph.successors(node_u)) | set(dag.graph.successors(node_v))) - {node_u, node_v}

    dag.graph.remove_node(node_u)
    dag.graph.remove_node(node_v)

    dag.graph.add_node(collapsed_name,
                       object_id=object_id,
                       num_threads=new_eta,
                       wceto_func=wceto_func)

    for p in preds:
        dag.graph.add_edge(p, collapsed_name)
    for s in succs:
        dag.graph.add_edge(collapsed_name, s)

    if object_id in dag._nodes_by_object:
        dag._nodes_by_object[object_id] = [
            n for n in dag._nodes_by_object[object_id]
            if n != node_u and n != node_v
        ]
        dag._nodes_by_object[object_id].append(collapsed_name)


def check_beneficial_collapse(dag, node_u: str, node_v: str, original_cores: int) -> bool:
    """
    Definition 7 — collapse is beneficial iff:
      1) no cycles introduced
      2) deadline still met (if it was met before)
      3) core allocation improved (or maintained)
    """
    if check_cycles_after_collapse(dag, node_u, node_v):
        return False

    original_cp = dag.critical_path_length()

    saved_graph = dag.graph.copy()
    collapse_nodes(dag, node_u, node_v)
    new_cp = dag.critical_path_length()
    dag.graph = saved_graph

    if original_cp <= dag.deadline and new_cp > dag.deadline:
        return False

    saved_graph = dag.graph.copy()
    collapse_nodes(dag, node_u, node_v)
    new_workload = dag.workload()
    new_cp = dag.critical_path_length()
    dag.graph = saved_graph

    if new_cp >= dag.deadline:
        new_cores = float('inf')
    else:
        denom = dag.deadline - new_cp
        new_cores = math.ceil((new_workload - new_cp) / denom) if denom > 0 else float('inf')

    if original_cores > 0:
        return 0 < new_cores <= original_cores
    else:
        return new_cores > original_cores


def order_by_greatest_benefit(candidates: List[Tuple[str, str]], dag) -> List[Tuple[str, str]]:
    """Sort candidates by descending Δ (Eq. 14)."""
    return sorted(candidates, key=lambda p: calculate_delta_workload(dag, p[0], p[1]), reverse=True)


def order_by_least_penalty(candidates: List[Tuple[str, str]], dag) -> List[Tuple[str, str]]:
    """Sort candidates by ascending γ (Eq. 15)."""
    return sorted(candidates, key=lambda p: calculate_penalty(dag, p[0], p[1]))


def order_arbitrary(candidates: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Shuffle candidates randomly (baseline)."""
    result = list(candidates)
    random.shuffle(result)
    return result


def dagot_reduce(dag, heuristic: str = "greatest_benefit") -> Dict:
    """
    Algorithm 1 — DAGOT-REDUCE.

    Finds candidate pairs, orders them by the chosen heuristic,
    and collapses each pair that passes the benefit check.

    Returns a dict with before/after metrics and the list of collapsed pairs.
    """
    original_workload = dag.workload()
    original_cp = dag.critical_path_length()

    if original_cp >= dag.deadline:
        original_cores = -1
    else:
        denom = dag.deadline - original_cp
        original_cores = math.ceil((original_workload - original_cp) / denom) if denom > 0 else float('inf')

    candidates = candidate_identification(dag)

    if heuristic == "greatest_benefit":
        ordered = order_by_greatest_benefit(candidates, dag)
    elif heuristic == "least_penalty":
        ordered = order_by_least_penalty(candidates, dag)
    else:
        ordered = order_arbitrary(candidates)

    collapsed_pairs = []
    for u, v in ordered:
        if u not in dag.graph.nodes or v not in dag.graph.nodes:
            continue
        if check_beneficial_collapse(dag, u, v, original_cores):
            collapse_nodes(dag, u, v)
            collapsed_pairs.append((u, v))

    final_workload = dag.workload()
    final_cp = dag.critical_path_length()

    if final_cp >= dag.deadline:
        final_cores = -1
    else:
        denom = dag.deadline - final_cp
        final_cores = math.ceil((final_workload - final_cp) / denom) if denom > 0 else float('inf')

    return {
        'collapsed_pairs': collapsed_pairs,
        'original_cores': original_cores,
        'final_cores': final_cores,
        'core_saved': max(0, original_cores - final_cores) if original_cores > 0 else 0,
        'original_workload': original_workload,
        'final_workload': final_workload,
        'workload_saved': original_workload - final_workload,
        'original_critical_path': original_cp,
        'final_critical_path': final_cp
    }