# Thread Scheduler Simulator

This project implements a Python simulator based on Prof. Tessler's research paper "Bringing Inter-Thread Cache Benefits to Federated Scheduling".

## What I've Done

### So Far (DAG-OT Model)
I built the core data structures for representing tasks in the simulator:

1. **DAGNode class** - Represents a single node in a task graph. Each node has:
   - An object ID (which executable it runs)
   - A WCETO function (worst-case execution time)
   - A thread count

2. **DAGTask class** - Represents a complete task with:
   - A period and deadline
   - A directed acyclic graph (DAG) structure
   - Methods to calculate workload, critical path, and utilization

3. **Candidate identification** - Found a way to identify which nodes can be merged together (nodes that run the same object)

### Testing
I wrote and ran 13 tests that verify:
- Creating nodes and tasks works correctly
- Workload calculation is accurate
- Critical path calculation is accurate
- Utilization calculation is accurate  
- Candidate identification finds the right pairs

All 13 tests passed.

## What the Project Can Do Now
The project can now:
- Create DAG tasks with nodes and edges
- Calculate workload (total execution time)
- Calculate critical path (longest path through the task)
- Calculate utilization (how much of the period is used)
- Identify which nodes are candidates for merging

## What's Next
I still need to implement:
- Growth factor WCETO (how cache affects execution time)
- Collapse algorithm (the main algorithm that merges nodes)
- Core allocation (how many processor cores are needed)
- Task generator (create test tasks)
- Metrics (measure improvements)

## How to Run Tests
```bash
cd Project/thread_scheduler
python -m pytest tests/test_dag_model.py -v
```

## References
- Tessler, C., Modekurthy, V. P., Fisher, N., & Saifullah, A. (2020). "Bringing Inter-Thread Cache Benefits to Federated Scheduling" - arXiv:2002.12516