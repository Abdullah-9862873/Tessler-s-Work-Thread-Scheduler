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

### Module 3: Collapse Algorithm (Complete ✅)

**Objective:** Implement the core algorithm from Prof. Tessler's paper - the one that actually reduces core allocation by merging nodes!

**The Problem:**
The whole point of the paper is to show that we can save processor cores by merging nodes that run the same code. But we need to be careful - we can't just merge randomly. We need an algorithm that:
1. Finds candidate nodes (that run the same object)
2. Decides which pairs to merge first
3. Checks that merging won't break things (no cycles, deadlines still met)
4. Does this repeatedly until no more beneficial merges

**What I Built:**
1. **candidate_identification(dag)** - Finds all pairs of nodes that run the same executable. These are "candidates" for merging.

2. **calculate_delta_workload(dag, u, v)** - Calculates how much workload we save by merging two nodes. Formula: Δ = c_u(η_u) + c_v(η_v) - c_u(η_u + η_v)

3. **calculate_penalty(dag, u, v)** - Calculates how much the critical path changes. We want this to be small!

4. **check_cycles_after_collapse(dag, u, v)** - Makes sure merging won't create a cycle in the DAG.

5. **collapse_nodes(dag, u, v)** - Actually performs the merge:
   - Combines threads: η_new = η_u + η_v
   - Keeps same object ID
   - Redirects edges to new node

6. **check_beneficial_collapse(dag, u, v, cores)** - Checks THREE conditions:
   - No cycles introduced
   - Deadline still met
   - Core allocation improves

7. **dagot_reduce(dag, heuristic)** - The MAIN ALGORITHM (Algorithm 1 from paper):
   ```
   1. Find all candidates (pairs with same object)
   2. Order them by heuristic
   3. Try each one - if beneficial, collapse it
   4. Repeat until no more beneficial collapses
   ```

8. **Three Heuristics:**
   - **Greatest Benefit (OT-G):** Pick pairs that save most workload first
   - **Least Penalty (OT-G):** Pick pairs that change critical path least
   - **Arbitrary (OT-A):** Random - used as baseline for comparison

**Why This Matters:**
This is the KEY algorithm that demonstrates the paper's contribution. Without this, we can't show the 20% core reduction that the paper talks about!

**Testing:** 18 tests written and passed.
- Verified candidate identification works correctly
- Verified workload savings calculation
- Verified collapse operation reduces nodes and workload
- Verified cycle detection prevents invalid merges
- Verified all three heuristics work
- Verified main DAGOT-REDUCE algorithm produces results

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
- **Run the core algorithm** that reduces core allocation

**We can now demonstrate the main contribution of the paper!**

---

## What's Next

I still need to implement:
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

# Run collapse tests
python -m pytest tests/test_collapse.py -v

# Run all tests
python -m pytest tests/ -v
```

---

## References

- Tessler, C., Modekurthy, V. P., Fisher, N., & Saifullah, A. (2020). "Bringing Inter-Thread Cache Benefits to Federated Scheduling" - arXiv:2002.12516