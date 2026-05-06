"""
Thread Scheduler Simulator - DAG-OT Model Implementation
Based on Prof. Tessler's paper: "Bringing Inter-Thread Cache Benefits to Federated Scheduling"

Modules:
    - dag_model: DAG-OT node/graph data structures
    - collapse: DAGOT-REDUCE algorithm and heuristics
    - growth_factor: Growth factor WCETO calculation
    - core_allocation: Federated scheduling core allocation
    - task_generator: Synthetic DAG task generation
    - metrics: ΔC, ΔL, Δm calculations
"""

__version__ = "1.0.0"