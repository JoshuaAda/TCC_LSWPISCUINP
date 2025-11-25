import os
import json
import numpy as np


def load_solution(run_id, workflow_id, problem_id):
    """Helper: load optimization result for a given subproblem."""
    sol_path = os.path.join("placement", f"run_{run_id}", f"opt_{workflow_id}_{problem_id}.json")
    with open(sol_path, "r") as f:
        return json.load(f)


def compute_critical_path_time(P, L, Speed, time_vec, a, b,
                               workflow_idx, num_functions, num_nodes):
    """
    Compute execution time of a workflow considering parallel branches.
    Uses adjacency matrix 'a' and branch membership 'b'.
    """

    # Map functions to the node where they are placed
    placement = {
        m: np.argmax(P[workflow_idx * num_functions + m, :])
        for m in range(num_functions)
    }

    # Execution times of functions at their nodes
    exec_times = {}
    for m in range(num_functions):
        node_m = placement[m]
        exec_times[m] = Speed[m, node_m] * time_vec[m][0]

    # Build adjacency list with communication latency
    graph = {m: [] for m in range(num_functions)}
    for m in range(num_functions):
        for m_s in range(num_functions):
            if a[m, m_s] == 1:  # dependency
                node_m = placement[m]
                node_ms = placement[m_s]
                comm_latency = L[node_m, node_ms]
                graph[m].append((m_s, comm_latency))

    # DFS with memoization to compute longest path from each node
    longest = {}

    def dfs(func):
        if func in longest:
            return longest[func]
        max_succ = 0
        for succ, comm_latency in graph[func]:
            max_succ = max(max_succ, comm_latency + dfs(succ))
        longest[func] = exec_times[func] + max_succ
        return longest[func]

    # For each branch (path), compute the max completion time
    branch_times = []
    num_paths = b.shape[0]
    for s in range(num_paths):
        funcs_in_branch = [m for m in range(num_functions) if b[s, m] == 1]
        if not funcs_in_branch:
            continue
        branch_time = max(dfs(m) for m in funcs_in_branch)
        branch_times.append(branch_time)

    return max(branch_times) if branch_times else 0.0


def simulate_request(run_id, workflow_id, cloud_config, num_levels):
    """
    Simulate execution cost for all leaves of a given workflow.
    Returns dict: {leaf_id: {"workflow": id, "latency": x, "exec_time": y, "cost": z}}
    """
    results = {}

    # --- load the first (top-level) solution ---
    top_sol = load_solution(run_id, workflow_id, 0)
    H = np.array(top_sol["H"])  # shape (num_leaves, num_workflows)

    # Iterate over all leaf nodes (requests)
    num_leaves = H.shape[0]
    for k in range(num_leaves):
        # Find assigned workflow for this leaf
        assigned = np.where(H[k, :] == 1)[0]
        if len(assigned) == 0:
            continue  # no workflow assigned
        n = assigned[0]  # workflow index

        total_latency = 0.0
        total_cost = 0.0
        exec_time = 0.0

        # Traverse down through all levels
        for level in range(num_levels):
            sol = load_solution(run_id, workflow_id, level)
            P = np.array(sol["P"])
            C = np.array(sol["C"])
