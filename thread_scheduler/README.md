# Thread Scheduler Simulator - DAG-OT Implementation

A Python implementation of the DAG-OT (DAG with Objects and Threads) model and the DAGOT-REDUCE collapse algorithm from Prof. Corey Tessler's paper: **"Bringing Inter-Thread Cache Benefits to Federated Scheduling"**

## Project Structure

```
thread_scheduler/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── dag_model.py             # DAG-OT node/graph data structures
│   ├── collapse.py              # DAGOT-REDUCE + heuristics
│   ├── growth_factor.py         # Growth factor WCETO
│   ├── core_allocation.py       # Federated scheduling
│   ├── task_generator.py        # Synthetic task generation
│   └── metrics.py               # ΔC, ΔL, Δm calculations
├── tests/
│   ├── test_dag_model.py
│   ├── test_growth_factor.py
│   ├── test_collapse.py
│   ├── test_core_allocation.py
│   └── test_task_generator.py
├── requirements.txt
└── README.md
```

## TODO

- [ ] Implement src/dag_model.py - DAG-OT Model
- [ ] Implement src/growth_factor.py - Growth Factor WCETO
- [ ] Implement src/collapse.py - Collapse Algorithm
- [ ] Implement src/core_allocation.py - Core Allocation
- [ ] Implement src/task_generator.py - Task Generator
- [ ] Implement src/metrics.py - Metrics Calculator
- [ ] Implement tests for all modules
- [ ] Run tests against paper examples (Figure 1, 5, Tables II, III)

## References

- Tessler, C., Modekurthy, V. P., Fisher, N., & Saifullah, A. (2020). "Bringing Inter-Thread Cache Benefits to Federated Scheduling" - arXiv:2002.12516