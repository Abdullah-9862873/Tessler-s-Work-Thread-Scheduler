# Thread Scheduler Simulator

This project implements a Python simulator based on Prof. Tessler's research paper "Bringing Inter-Thread Cache Benefits to Federated Scheduling".

---

## What I've Done So Far

### Module 1: DAG-OT Model (Complete ✅)

**Objective:** Build the core data structures to represent tasks in the simulator.

**What I Built:**
1. **DAGNode class** - Represents a single node in a task graph. Each node has:
   - An object ID (which executable it runs)
   - A WCETO function (worst-case execution time)
   - A thread count

2. **DAGTask class** - Represents a complete task with:
   - A period and deadline
   - A directed acyclic graph (DAG) structure using NetworkX
   - Methods to calculate workload, critical path, and utilization

3. **Candidate identification** - Identifies which nodes can be merged together (nodes that run the same executable object)

**Testing:** 13 tests written and passed.
- Verified node and task creation
- Verified workload calculation (C = sum of all WCETs)
- Verified critical path calculation (L = longest path through DAG)
- Verified utilization calculation (u = C / T)
- Verified candidate identification

---

### Module 2: Growth Factor WCETO (Complete ✅)

**Objective:** Implement a way to model how execution time changes when multiple threads run together, and how they share cached data.

**The Problem:**
When multiple threads run the same code, they can share cached instructions. This means running 2 threads together might take less than 2x the time of running 1 thread. We need a mathematical formula to capture this "cache benefit."

**What I Built:**
1. **create_growth_factor_wceto(c1, F) function** - Creates a WCETO function using this formula:

   ```
   c(η) = c(1) + F × (η - 1) × c(1)
   ```

   Where:
   - c(1) = execution time for 1 thread
   - η = number of threads
   - F = growth factor (between 0 and 1)

   **Simple explanation:**
   - If F = 1 (worst case): Running 2 threads takes 2× the time, 3 threads takes 3× the time. No cache benefit at all.
   - If F = 0.5 (half benefit): Running 2 threads takes 1.5× the time (instead of 2×), because threads share half the cached data.
   - If F = 0.2 (best case): Running 2 threads takes only 1.2× the time. Much better!

2. **verify_concavity() function** - Checks that the function is "concave" - meaning each additional thread gives less benefit than the previous one. This is crucial because concavity is what makes the collapse algorithm work! If the function wasn't concave, merging nodes might actually make things worse.

3. **GrowthFactorWCETO class** - A convenient wrapper class that:
   - Stores c1 and F values
   - Can be called like a function
   - Has helpful properties like `is_concave` and `satisfies_definition`
   - Can calculate marginal gain (benefit from one more thread)
   - Can calculate total benefit (how much faster bundled is vs separate)

**The Math Made Simple:**
Think of it like this:
- You have 1 thread that takes 10ms to run (c1 = 10)
- If F = 0.5, then:
  - 1 thread = 10ms
  - 2 threads = 10 + 0.5×(2-1)×10 = 15ms (instead of 20ms if run separately!)
  - 3 threads = 10 + 0.5×(3-1)×10 = 20ms (instead of 30ms!)
  - 5 threads = 10 + 0.5×(5-1)×10 = 30ms (instead of 50ms!)

The benefit grows as we bundle more threads together!

**Testing:** 18 tests written and passed.
- Verified basic WCETO calculation for different F values
- Verified F=1 gives linear (no benefit)
- Verified F<1 gives sub-linear (cache benefit)
- Verified concavity property
- Verified Definition 3 property from the paper
- Tested the GrowthFactorWCETO class
- Tested marginal gain and total benefit calculations

---

## What the Project Can Do Now

The project can now:
- **Create DAG tasks** with nodes and edges representing parallel work
- **Calculate workload** (total execution time of all nodes)
- **Calculate critical path** (longest path through the task graph)
- **Calculate utilization** (how much of the period is used)
- **Identify candidate nodes** that can be merged
- **Model cache benefits** with growth factor WCETO
- **Verify concavity** ensuring the collapse algorithm will work

---

## What's Next

I still need to implement:
- **Collapse algorithm** - The main algorithm that merges nodes to reduce core allocation
- **Core allocation** - Calculate how many processor cores are needed
- **Task generator** - Create test tasks with various parameters
- **Metrics** - Measure improvements from collapse
- **Experiments** - Run evaluations and compare results
- **Demo** - Build an interactive visualization

---

## How to Run Tests

```bash
cd Project/thread_scheduler

# Run DAG model tests
python -m pytest tests/test_dag_model.py -v

# Run growth factor tests
python -m pytest tests/test_growth_factor.py -v

# Run all tests
python -m pytest tests/ -v
```

---

## References

- Tessler, C., Modekurthy, V. P., Fisher, N., & Saifullah, A. (2020). "Bringing Inter-Thread Cache Benefits to Federated Scheduling" - arXiv:2002.12516