# Thread Scheduler Project

This project implements the DAGOT-REDUCE algorithm based on Prof. Corey Tessler's research on "Bringing Inter-Thread Cache Benefits to Federated Scheduling". The algorithm optimizes thread scheduling by intelligently collapsing nodes in a Directed Acyclic Graph (DAG) that share the same executable code.

---

## Project Overview

The main goal is to reduce computational resource usage by merging nodes that run identical code. When multiple threads execute the same application (e.g., multiple browser tabs running Chrome), they can be combined into a single thread, reducing overall CPU usage while preserving task dependencies.

### Key Components

1. **DAG Model** - Represents tasks as directed acyclic graphs where nodes are applications and edges are dependencies
2. **WCETO Functions** - Worst-Case Execution Time functions that model how execution time changes with thread count
3. **Collapse Algorithm** - The DAGOT-REDUCE algorithm that identifies and merges collapsible nodes
4. **Core Allocation** - Calculates how many processor cores are needed for tasks
5. **Task Generator** - Creates synthetic DAG-OT tasks for evaluation
6. **Metrics Calculator** - Measures the effectiveness of the optimization

---

## Project Structure

```
Project/
├── thread_scheduler/          # Core algorithm implementation
│   ├── src/
│   │   ├── dag_model.py       # DAG and node data structures
│   │   ├── growth_factor.py  # WCETO functions
│   │   ├── collapse.py        # DAGOT-REDUCE algorithm
│   │   ├── core_allocation.py # Core calculation
│   │   ├── task_generator.py # Synthetic task generation
│   │   └── metrics.py        # Evaluation metrics
│   ├── tests/                 # Test suite (133 tests)
│   ├── requirements.txt       # Dependencies
│   └── README.md             # Detailed documentation
├── Notebook/                  # Demonstration notebook
│   └── thread_scheduler.ipynb # Real CPU workload demo
└── README.md                 # This file
```

---

## Running the Tests

The test suite contains 133 tests covering all components of the thread scheduler.

### Command to Run All Tests

```bash
cd D:\Professors Reached\10- Corey Tessler\Project\thread_scheduler
python -m pytest tests/ -v
```

### Run Individual Test Files

```bash
# DAG model tests (14 tests)
python -m pytest tests/test_dag_model.py -v

# Growth factor tests (17 tests)
python -m pytest tests/test_growth_factor.py -v

# Collapse algorithm tests (18 tests)
python -m pytest tests/test_collapse.py -v

# Core allocation tests (13 tests)
python -m pytest tests/test_core_allocation.py -v

# Task generator tests (31 tests)
python -m pytest tests/test_task_generator.py -v

# Metrics tests (23 tests)
python -m pytest tests/test_metrics.py -v
```

---

## What the 133 Tests Cover

### 1. DAG Model Tests (14 tests)
These tests verify the fundamental data structures:
- DAGNode creation and properties
- DAGTask creation with period and deadline
- Adding nodes and edges to the DAG
- Workload calculation (sum of all WCETOs)
- Critical path calculation (longest path through DAG)
- Utilization calculation
- Candidate identification (nodes with same object ID)

### 2. Growth Factor Tests (17 tests)
These tests verify the WCETO functions that model execution time:
- Basic WCETO calculation with different growth factors
- Growth factor F=1 gives linear time (no cache benefit)
- Growth factor F<1 gives sub-linear time (cache benefit)
- Concavity verification (ensures algorithm works correctly)
- GrowthFactorWCETO class functionality
- Marginal gain and total benefit calculations

### 3. Collapse Algorithm Tests (18 tests)
These tests verify the core DAGOT-REDUCE algorithm:
- Candidate identification (finding nodes with same object)
- Workload savings calculation (Equation 14 from paper)
- Critical path penalty calculation (Equation 15 from paper)
- Cycle detection after collapse
- Node collapse operation (merging two nodes)
- Beneficial collapse verification (3 conditions)
- Three ordering heuristics:
  - Greatest Benefit (OT-G)
  - Least Penalty (OT-L)
  - Arbitrary (OT-A)
- Main DAGOT-REDUCE algorithm execution

### 4. Core Allocation Tests (13 tests)
These tests verify core calculation for multi-core scheduling:
- Core allocation formula from the paper
- High vs low utilization detection
- Federated scheduling separation
- Total core requirements for task sets
- Improved core allocation verification
- CoreAllocator class functionality
- Edge cases and boundary conditions

### 5. Task Generator Tests (31 tests)
These tests verify synthetic task generation:
- DAG structure generation with specified node count
- Edge probability effects on graph density
- Forward-only edge direction (ensures acyclic)
- Source/sink enforcement (single entry and exit)
- Complete task generation pipeline
- Task set generation with utilization splitting
- TaskSetGenerator class with paper parameters
- Reproducibility with random seeds

### 6. Metrics Tests (23 tests)
These tests verify the evaluation metrics:
- Core savings calculation (Equation 16)
- Workload reduction calculation (Equation 18)
- Critical path extension calculation (Equation 19)
- Schedulability ratio calculation
- Utilization change calculation
- Task before/after evaluation
- Task set evaluation
- Heuristic comparison
- MetricsCalculator class functionality

---

## Dependencies

The project requires:
- Python 3.10+
- NetworkX (for DAG representation)
- NumPy (for numerical calculations)
- Matplotlib (for visualization)
- psutil (for CPU measurements in demo)

Install dependencies:
```bash
pip install networkx numpy matplotlib psutil pytest
```

---

## Demonstration

The Notebook folder contains a demonstration that shows the algorithm working with real CPU load:

1. Creates a 5-node DAG representing different applications
2. Three nodes run "chrome" (same object - candidates for collapse)
3. Two nodes run different applications (vscode, slack)
4. Runs the DAGOT-REDUCE algorithm to find optimal collapses
5. Measures actual CPU time before and after optimization

To run the demonstration:
1. Open `Notebook/thread_scheduler.ipynb` in Jupyter
2. Execute all cells in order
3. The notebook uses Python multiprocessing to create real CPU load

---

## The Research Paper

This implementation is based on the paper:

**Tessler, C., Modekurthy, V. P., Fisher, N., & Saifullah, A. (2020). "Bringing Inter-Thread Cache Benefits to Federated Scheduling" - arXiv:2002.12516**

The paper addresses how to optimize thread scheduling in multi-core systems when multiple threads run the same code. The key insight is that when threads share cached instructions, running them together takes less time than running them separately. The DAGOT-REDUCE algorithm finds opportunities to merge such threads while respecting task dependencies.

---

## For New Contributors

If you're joining this project:

1. **Start with the tests** - Run `python -m pytest tests/ -v` to understand what each component does
2. **Read the module documentation** - The README.md in thread_scheduler/ has detailed explanations
3. **Understand the DAG** - The core data structure is in dag_model.py
4. **Understand the algorithm** - The collapse.py contains the main optimization logic
5. **Run the demo** - The notebook shows a working example with real CPU measurements

The 133 tests serve as both verification and documentation. Each test has a descriptive name that explains what it's checking.

---