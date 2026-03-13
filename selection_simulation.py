import json
import numpy as np
import argparse
import os
if __name__ == "__main__":


        parser = argparse.ArgumentParser()
        parser.add_argument("--num_run", required=True, type=int)
        args = parser.parse_args()
        num_run = args.num_run

        placement_path=f"placement/run_{num_run}"
        parameter_config_path=f"settings/parameters_{num_run}.json"
        with open(parameter_config_path, "r") as f:
                parameter_general_config = json.load(f)
        provider_cost_list=parameter_general_config["provider_cost_list"]
        general_config_path=f"cloud/run_{num_run}/general_config.json"
        with open(general_config_path, "r") as f:
                cloud_general_config = json.load(f)
        num_leaves=cloud_general_config["num_leaves"]
        num_workflows= parameter_general_config["num_workflows"]
        num_levels=parameter_general_config["num_levels"]

        num_other_first_level=len(parameter_general_config["provider_list"])-1
        num_nodes_in_level = cloud_general_config["num_nodes_in_level"]
        num_probs=0
        comparison=parameter_general_config["comparison"]
        heuristic=parameter_general_config["heuristic"]

        time_cost_all = 0
        money_cost_all = 0
        w_1 = parameter_general_config["w_1"]
        w_2 = parameter_general_config["w_2"]
        w_3 = parameter_general_config["w_3"]
        provider_list=cloud_general_config["provider_list"]
        predecessor_list=cloud_general_config["predecessor_list"]
        num_nodes_in_level_list=cloud_general_config["num_nodes_in_level"]
        num_other=len(provider_list[-1])-num_leaves
        ind_start_list=[0]
        for value in predecessor_list:
                ind_start_list.append(len(value)+ind_start_list[-1])

        def upward_trajectory(leave_k):

                pos_list=[]
                pred_k_list=[]
                lat_upward_list=[]
                for r in range(num_levels-1,-1,-1):
                        ind_r = 0
                        num_curr_nodes = 0
                        for node_len in num_nodes_in_level_list[r]:
                                num_curr_nodes += node_len
                                if num_curr_nodes > leave_k:
                                        pos=leave_k-num_curr_nodes+node_len
                                        pos_list.append(pos)
                                        break
                                ind_r += 1


                        pred_k = ind_r
                        pred_k_list.append(pred_k)

                        placement_path = f"placement/run_{num_run}/opt_{t}_{pred_k+ind_start_list[r]}.json"
                        with open(placement_path, "r") as f:
                                curr_placement = json.load(f)
                        L=curr_placement["L"]

                        lat_upward=L[0][pos]
                        lat_upward_list.append(lat_upward)
                        leave_k=pred_k

                pos_list.reverse()
                pred_k_list.reverse()
                lat_upward_list.reverse()
                #pred_k = pred_k - num_other_first_level
                return pred_k_list,lat_upward_list,pos_list

        def find_opt(opt_num,selected_place, r):
                prev_value=opt_num - ind_start_list[r-1]
                if prev_value>0:
                        num_curr_nodes=0
                        for node_len in num_nodes_in_level_list[r-1][0:prev_value]:
                                num_curr_nodes += node_len
                        return selected_place+ind_start_list[r]+num_curr_nodes
                else:
                        return selected_place + ind_start_list[r]
        def find_correct_workflow(curr_selected_workflow,workflow_list):
                index=workflow_list.index(curr_selected_workflow)
                return index#curr_selected_workflow
        def get_leaf(selected_place,opt_num):
                num_curr_nodes=0
                ### TODO -1 just because of first level change
                for node_len in num_nodes_in_level_list[-1][0:opt_num-ind_start_list[-2]]:
                        num_curr_nodes += node_len
                num_curr_nodes+=selected_place
                return num_curr_nodes


        np.random.seed(42)
        sim_time = parameter_general_config["simulation_time"]
        time_cost_all = 0
        money_cost_all = 0
        select_cost_all = 0
        time_cost = 0
        money_cost = 0
        request_rates = np.zeros((num_workflows, num_leaves))
        for t in range(num_workflows):
                cloud_name = f"requirements_cloud_full.json"
                path_cloud = os.path.join(f"cloud/run_{num_run}", cloud_name)
                with open(path_cloud, "r") as f:
                        cloud_config = json.load(f)
                for k in range(num_leaves):
                        request_rates[t, k] = cloud_config["providers"][f"provider_{k + num_other}"]["request_rate"]
        requests = np.zeros((sim_time, num_workflows, num_leaves))
        # prepare structures for a minimal discrete-time scheduler (dt=1)
        # load full cloud to get global node RAM capacities
        cloud_full_path = os.path.join(f"cloud/run_{num_run}", "requirements_cloud_full.json")
        with open(cloud_full_path, 'r') as f:
                cloud_full = json.load(f)
        num_nodes_global = cloud_full.get('num_nodes', 0)
        node_ram_max = [cloud_full['providers'][f'provider_{i}'].get('max_RAM_curr', 1e9) if cloud_full['providers'][f'provider_{i}'].get('name')=="tinyfaas" else np.inf for i in
                        range(num_nodes_global)]

        # Precompute per-workflow, per-leaf selected places, durations and rams
        perwf = {}


        # helper to reconstruct full P and H from decomposed per-level opt files
        def reconstruct_full_solution(w):
                # returns sol_conf dict with keys P (list of rows) and H (list)
                wf_path = os.path.join(f"workflows/run_{num_run}", f"requirements_workflow_{w}_0.json")
                try:
                        with open(wf_path, 'r') as f:
                                wf_conf = json.load(f)
                except Exception:
                        wf_conf = {}
                deployment_number=wf_conf["deployment_number"]
                num_funcs = wf_conf.get('num_functions', 0)
                # total global nodes
                num_nodes_all = cloud_full.get('num_nodes', 0)
                # initialize P_full rows: we'll create one row per (deployment * function)
                # We don't know deployment count per se here; we'll create rows for one deployment placeholder
                P_full = [[0 for _ in range(num_nodes_all)] for _ in range(num_funcs)]
                # H_full: for each leaf, one-hot vector over top-level workflows
                # length should match number of top-level workflows (num_workflows)
                H_full = [[0 for _ in range(deployment_number)] for _ in range(num_leaves)]

                # try to load full placement if available (to reuse latencies and path matrices a/b)
                L_full = []
                a_full = []
                b_full = []
                full_path = os.path.join(f"placement/run_{num_run}", f"opt_{w}_full.json")
                try:
                        with open(full_path, 'r') as f:
                                full_place_tmp = json.load(f)
                                if 'L' in full_place_tmp:
                                        L_full = full_place_tmp.get('L', [])
                                a_full = full_place_tmp.get('a', [])
                                b_full = full_place_tmp.get('b', [])
                                if len(b_full)>1:
                                        for r in range(1,len(b_full)):
                                                b_full[r][0]=0
                                                b_full[r][-1]=0
                except Exception:
                        pass

                # try to load top-level placement for workflow w (opt_{w}_0.json) to get top H if present
                top_path = os.path.join(f"placement/run_{num_run}", f"opt_{w}_0.json")
                try:
                        with open(top_path, 'r') as f:
                                top_place = json.load(f)
                except Exception:
                        top_place = {}

                for leaf in range(num_leaves):
                        # determine selected workflow at top level if possible
                        try:
                                pred_k_list, lat_upward_list, pos_list = upward_trajectory(leaf + num_other)
                        except Exception:
                                pred_k_list, lat_upward_list, pos_list = ([], [], [])
                        sel_work = 0
                        try:
                                Htop = top_place.get('H', [])
                                if Htop:
                                        sel_work = int(
                                                np.where(np.array(Htop[pred_k_list[1] - num_other_first_level]) == 1)[
                                                        0][0])
                        except Exception:
                                sel_work = 0
                        # mark H_full one-hot (length = num_workflows)
                        try:
                                vec = [0] * deployment_number
                                if 0 <= sel_work < deployment_number:
                                        vec[int(sel_work)] = 1
                                H_full[leaf] = vec
                        except Exception:
                                H_full[leaf] = [0 for _ in range(num_workflows)]

                        # for each function, walk levels to find global node
                        for m in range(num_funcs):
                                prev_selected_place = 0
                                opt_num = 0
                                curr_selected_workflow = sel_work
                                k_curr = 0
                                for r in range(num_levels):
                                        if r != 0:
                                                opt_num = find_opt(opt_num, prev_selected_place, r)
                                        placement_path = f"placement/run_{num_run}/opt_{w}_{opt_num}.json"
                                        try:
                                                with open(placement_path, 'r') as f:
                                                        curr_placement = json.load(f)
                                        except Exception:
                                                curr_placement = {}

                                        curr_P = curr_placement.get('P', [])
                                        curr_workflow = {}
                                        try:
                                                workflow_path = f"workflows/run_{num_run}/requirements_workflow_{w}_{opt_num}.json"
                                                with open(workflow_path, 'r') as f:
                                                        curr_workflow = json.load(f)
                                        except Exception:
                                                curr_workflow = {}

                                        if r == 0:
                                                # top-level: selected_workflow already known
                                                try:
                                                        if curr_P:
                                                                selected_place = int(np.where(np.array(curr_P[
                                                                                                               curr_selected_workflow * num_funcs + m]) == 1)[
                                                                                             0][0])
                                                        else:
                                                                selected_place = 0
                                                except Exception:
                                                        selected_place = 0
                                        else:
                                                # map curr_selected_workflow into local index if needed
                                                try:
                                                        if 'active_workflow_list' in curr_workflow and curr_workflow[
                                                                'active_workflow_list']:
                                                                curr_selected_workflow = find_correct_workflow(
                                                                        curr_selected_workflow,
                                                                        curr_workflow['active_workflow_list'])
                                                except Exception:
                                                        pass
                                                try:
                                                        if curr_P:
                                                                selected_place = int(np.where(np.array(curr_P[
                                                                                                               curr_selected_workflow * num_funcs + m]) == 1)[
                                                                                             0][0])
                                                        else:
                                                                selected_place = 0
                                                except Exception:
                                                        selected_place = 0

                                        # record L if available at any level
                                        if not L_full and 'L' in curr_placement:
                                                L_full = curr_placement.get('L', L_full)

                                        # if last level, translate to global node index
                                        if r == num_levels - 1:
                                                try:
                                                        k_curr = get_leaf(selected_place, opt_num)
                                                except Exception:
                                                        k_curr = selected_place

                                        prev_selected_place = selected_place

                                # set P_full row: combine using sel_work index offset
                                try:
                                        row_idx = sel_work * num_funcs + m
                                except Exception:
                                        row_idx = m
                                # ensure P_full has enough rows
                                if row_idx >= len(P_full):
                                        # extend rows
                                        for _ in range(row_idx - len(P_full) + 1):
                                                P_full.append([0 for _ in range(num_nodes_all)])
                                if 0 <= k_curr < num_nodes_all:
                                        P_full[row_idx][k_curr] = 1

                return {'P': P_full, 'H': H_full, 'L': L_full, 'a': a_full, 'b': b_full}


        for w in range(num_workflows):
                wf_path = os.path.join(f"workflows/run_{num_run}", f"requirements_workflow_{w}_0.json")
                sol_path = os.path.join(f"placement/run_{num_run}", f"opt_{w}_full.json")
                node_path = os.path.join(f"cloud/run_{num_run}", f"requirements_cloud_full.json")
                try:
                        with open(wf_path, 'r') as f:
                                wf_conf = json.load(f)
                        with open(node_path, 'r') as f:
                                node_conf = json.load(f)
                except Exception:
                        wf_conf = {}
                        node_conf = {}
                # Build the decomposed (reconstructed) placement for this workflow
                # (always use reconstruction here so the first part uses the decomposed solution)
                sol_conf = {}
                try:
                        sol_conf = reconstruct_full_solution(w)
                except Exception:
                        sol_conf = {}
                P = sol_conf.get('P', [])
                H = sol_conf.get('H', [])
                L = sol_conf.get('L', [])
                Speed = sol_conf.get('Speed', None)
                a = sol_conf.get('a', [])
                b = sol_conf.get('b', [])
                num_funcs = wf_conf.get('num_functions', 0)
                perwf[w] = {}
                for leaf in range(num_leaves):
                        sel_work = 0
                        try:
                                sel_work = int(np.where(np.array(H[leaf]) == 1)[0][0]) if H else 0
                        except Exception:
                                sel_work = 0
                        # selected places for each function (global node indices as in full placement)
                        selected_places = []
                        for m in range(num_funcs):
                                try:
                                        row = P[sel_work * num_funcs + m]
                                        selected_places.append(int(np.where(np.array(row) == 1)[0][0]))
                                except Exception:
                                        selected_places.append(0)

                        # durations (ceil) and ram per function given the selected node
                        durations = [0] * num_funcs
                        rams = [0] * num_funcs
                        for m in range(num_funcs):
                                node = selected_places[m]
                                node_name=node_conf["providers"][f"provider_{node}"]["name"]
                                try:
                                        func_conf = wf_conf['functions'][f"function_{m}"]
                                        base_time = func_conf.get('time', 0)
                                        if Speed:
                                                try:
                                                        speedup = float(np.array(Speed)[m][node])
                                                except Exception:
                                                        speedup = func_conf.get('speedup', 1)
                                        else:
                                                if node_name != "tinyfaas":
                                                        speedup = func_conf.get('speedup', 1)
                                                else:
                                                        speedup=1
                                        dur = int(np.ceil(speedup * base_time))
                                        durations[m] = dur
                                        rams[m] = func_conf.get('ram', 0)
                                except Exception:
                                        durations[m] = 0
                                        rams[m] = 0

                        perwf[w][leaf] = {
                                'selected_places': selected_places,
                                'deployment': int(sel_work),
                                'durations': durations,
                                'rams': rams,
                                'L': L
                        }
                # store workflow-level path matrices so simulation can compute base_T correctly
                perwf[w]['a'] = a
                perwf[w]['b'] = b
                try:
                        perwf[w]['num_paths'] = wf_conf.get('paths', {}).get('num_paths', 0)
                except Exception:
                        perwf[w]['num_paths'] = 0

        curr_utilization = np.zeros((num_nodes_global, 1))
        #func_blocked = np.zeros((num_workflows, num_functions))
        # node_active holds tuples (end_time, ram)
        node_active = [[] for _ in range(num_nodes_global)]
        # ram area accumulator for utilization
        ram_area = [0.0] * num_nodes_global

        # minimal per-workflow/leaf waiting accumulator
        waiting_acc = np.zeros((num_workflows, num_leaves))

        # per-time-step per-node utilization (samples of used RAM)
        per_node_util = np.zeros((sim_time, num_nodes_global), dtype=float)

        # per-request logs: collect arrival, start (approx), end, base_T, wait, workflow, leaf
        request_logs = []
        req_id_counter = 0
        req_done_list = []

        rng = np.random.default_rng(42)

        for cur_t in range(sim_time):
                # generate arrivals for this second
                requests[cur_t] = rng.poisson(request_rates)
                # choose simulation mode: lazy_start toggles whether functions are started only when reached
                lazy_start = parameter_general_config.get('lazy_start', False)
                if lazy_start:
                        # LAZY START MODE: enqueue requests and only start functions when their turn arrives
                        # prune finished entries at the second boundary to keep node_active small
                        for ni in range(num_nodes_global):
                                node_active[ni] = [entry for entry in node_active[ni] if entry[0] > cur_t]

                        # initialize pending queue on first iteration
                        if cur_t == 0:
                                pending_requests = []

                        # enqueue arrivals for this second (FIFO)
                        for w in range(num_workflows):
                                for leaf in range(num_leaves):
                                        n = int(requests[cur_t, w, leaf])
                                        if n <= 0:
                                                continue
                                        info = perwf.get(w, {}).get(leaf, None)
                                        if info is None:
                                                continue
                                        sel_places = info['selected_places']
                                        durs = info['durations']
                                        rams = info['rams']
                                        Lmat = info['L']
                                        deployment_id = int(info.get('deployment', w))
                                        # compute base_T using workflow path definitions 'a' (max over paths)
                                        base_T_paths = []
                                        a_mat = perwf[w].get('a', [])
                                        b_mat = perwf[w].get('b', [])
                                        num_paths_local = perwf[w].get('num_paths', 0)
                                        for s in range(num_paths_local):
                                                func_nums = np.where(np.array(b_mat[s])==1)[0].tolist() if isinstance(b_mat, (list, np.ndarray)) and len(b_mat) > s else []
                                                        #a_mat, list) and len(a_mat) > s else []
                                                tot = 0
                                                for idx_m in func_nums:
                                                        tot += durs[idx_m]
                                                        # determine next place
                                                        if idx_m < len(func_nums) - 1:
                                                                next_m = func_nums[func_nums.index(idx_m) + 1]
                                                                next_place = sel_places[next_m]
                                                        else:
                                                                next_place = leaf + num_other
                                                        try:
                                                                tot += int(np.ceil(Lmat[sel_places[idx_m]][next_place]))
                                                        except Exception:
                                                                pass
                                                base_T_paths.append(tot)
                                        base_T = max(base_T_paths) if base_T_paths else 0

                                        for i in range(n):
                                                req = {
                                                        'id': int(req_id_counter),
                                                        'workflow': int(w),
                                                        'leaf': int(leaf),
                                                        'arrival': int(cur_t),
                                                        'deployment': int(info.get('deployment', w)),
                                                        'sel_places': sel_places,
                                                        'durs': durs,
                                                        'rams': rams,
                                                        'L': Lmat,
                                                        'base_T': int(base_T),
                                                        'next_idx': 0,
                                                        'start_times': [],
                                                        'end_times': []
                                                }
                                                pending_requests.append(req)
                                                req_id_counter += 1

                        # attempt to start functions for pending requests in FIFO order
                        still_pending = []
                        for req in pending_requests:
                                w = req['workflow']
                                leaf = req['leaf']
                                sel_places = req['sel_places']
                                durs = req['durs']
                                rams = req['rams']
                                Lmat = req['L']
                                idx = req['next_idx']
                                num_funcs = len(durs)

                                if idx >= num_funcs:
                                        # already finished; record completion
                                        if req['end_times']:
                                                last_node = sel_places[-1]
                                                last_end = req['end_times'][-1]
                                                try:
                                                        final_transfer = int(np.ceil(Lmat[last_node][leaf + num_other]))
                                                except Exception:
                                                        final_transfer = 0
                                                req_done = last_end + final_transfer
                                        else:
                                                req_done = req['arrival']
                                        req_done_list.append(req_done)
                                        wait = max(0, req_done - req['arrival'] - req['base_T'])
                                        waiting_acc[w, leaf] += wait
                                        # log
                                        request_logs.append({
                                                'id': req['id'],
                                                'workflow': w,
                                                'leaf': leaf,
                                                'arrival': req['arrival'],
                                                'start': req['start_times'][0] if req['start_times'] else req[
                                                        'arrival'],
                                                'end': req_done,
                                                'base_T': req['base_T'],
                                                'wait': int(wait)
                                        })
                                        continue

                                # check if predecessor finished and transfer completed
                                ready = False
                                if idx == 0:
                                        ready = True
                                else:
                                        if len(req['end_times']) >= idx:
                                                prev_end = req['end_times'][idx - 1]
                                                prev_node = sel_places[idx - 1]
                                                try:
                                                        next_place = sel_places[idx]
                                                except Exception:
                                                        next_place = leaf + num_other
                                                try:
                                                        transfer = int(np.ceil(Lmat[prev_node][next_place]))
                                                except Exception:
                                                        transfer = 0
                                                if prev_end + transfer <= cur_t:
                                                        ready = True

                                if not ready:
                                        still_pending.append(req)
                                        continue

                                # try to start this function at current time cur_t
                                node = sel_places[idx]
                                dur = durs[idx]
                                ram_req = rams[idx]
                                used = sum(entry[1] for entry in node_active[node] if entry[0] > cur_t)
                                deployment_id = req.get('deployment', w)
                                func_busy = any(
                                        len(entry) >= 4 and entry[0] > cur_t and entry[2] == deployment_id and entry[3] == idx for
                                        entry in node_active[node])
                                if used + ram_req <= node_ram_max[node] and (not func_busy):
                                        # start now
                                        start = cur_t
                                        endt = start + dur
                                        node_active[node].append((endt, ram_req, deployment_id, idx, req['id'],w))
                                        req['start_times'].append(start)
                                        req['end_times'].append(endt)
                                        req['next_idx'] += 1
                                        # if there are more functions, keep in pending to try next in later ticks
                                        if req['next_idx'] < num_funcs:
                                                still_pending.append(req)
                                        else:
                                                # will be recorded as finished on next loop iteration
                                                still_pending.append(req)
                                else:
                                        still_pending.append(req)

                        pending_requests = still_pending

                        # update ram_area and per-node util for this second
                        for ni in range(num_nodes_global):
                                used_now = sum(entry[1] for entry in node_active[ni] if entry[0] > cur_t)
                                ram_area[ni] += used_now
                                per_node_util[cur_t, ni] = used_now
                else:
                        # RESERVE-ALL MODE (existing logic)
                        # prune finished entries at the second boundary to keep node_active small
                        for ni in range(num_nodes_global):
                                node_active[ni] = [entry for entry in node_active[ni] if entry[0] > cur_t]
                        # enqueue and schedule arrivals (FIFO within this second)
                        for w in range(num_workflows):
                                for leaf in range(num_leaves):
                                        n = int(requests[cur_t, w, leaf])
                                        if n <= 0:
                                                continue
                                        info = perwf.get(w, {}).get(leaf, None)
                                        if info is None:
                                                continue
                                        sel_places = info['selected_places']
                                        durs = info['durations']
                                        rams = info['rams']
                                        Lmat = info['L']
                                        deployment_id = int(info.get('deployment', w))
                                        # compute static base path time for this request (max over paths)
                                        base_T_paths = []
                                        a_mat = perwf[w].get('a', [])
                                        b_mat = perwf[w].get('b', [])
                                        num_paths_local = perwf[w].get('num_paths', 0)
                                        for s in range(num_paths_local):
                                                func_nums = np.where(np.array(b_mat[s])==1)[0].tolist() if isinstance(b_mat, (list, np.ndarray)) and len(b_mat) > s else []
                                                        #a_mat, list) and len(a_mat) > s else []
                                                tot = 0
                                                for idx_m in func_nums:
                                                        tot += durs[idx_m]
                                                        # transfer to next
                                                        # determine next place
                                                        # if last function, next is leaf (k+num_other)
                                                        # else next selected place
                                                        # avoid index errors
                                                        if idx_m < len(func_nums) - 1:
                                                                next_m = func_nums[func_nums.index(idx_m) + 1]
                                                                next_place = sel_places[next_m]
                                                        else:
                                                                next_place = leaf + num_other
                                                        try:
                                                                tot += int(np.ceil(Lmat[sel_places[idx_m]][next_place]))
                                                        except Exception:
                                                                pass
                                                base_T_paths.append(tot)
                                        base_T = max(base_T_paths) if base_T_paths else 0

                                        # schedule n requests sequentially (spaced within the second FIFO)
                                        for i in range(n):
                                                arrival = cur_t
                                                path_finish_times = []
                                                # for each path, simulate sequential function execution with resource checks
                                                a_mat = perwf[w].get('a', [])
                                                b_mat = perwf[w].get('b', [])
                                                num_paths_local = perwf[w].get('num_paths', 0)
                                                for s in range(num_paths_local):
                                                        func_nums = np.where(np.array(b_mat[s])==1)[0].tolist() if isinstance(b_mat, (list, np.ndarray)) and len(b_mat) > s else []
                                                                #a_mat, list) and len(a_mat) > s else []
                                                        curr_time = arrival
                                                        for idx_m in func_nums:
                                                                node = sel_places[idx_m]
                                                                dur = durs[idx_m]
                                                                ram_req = rams[idx_m]
                                                                # find earliest start time when node has enough free RAM
                                                                # AND when the same (workflow, function) is not already running anywhere
                                                                while True:
                                                                        # current used RAM on this node at curr_time
                                                                        used = sum(
                                                                                entry[1] for entry in node_active[node]
                                                                                if entry[0] > curr_time)
                                                                        # only consider same-function instances running on the same node
                                                                        func_busy_ends = [entry[0] for entry in
                                                                                          node_active[node] if
                                                                                          len(entry) >= 4 and entry[
                                                                                                  0] > curr_time and
                                                                                          entry[2] == deployment_id and entry[
                                                                                                  3] == idx_m and entry[4] == w]
                                                                        #print(used + ram_req)
                                                                        if used + ram_req <= node_ram_max[node] and (
                                                                        not func_busy_ends):
                                                                                #print('start')
                                                                                start = curr_time
                                                                                break
                                                                        # advance to earliest finishing task relevant to capacity or function lock
                                                                        future_ends_node = [entry[0] for entry in
                                                                                            node_active[node] if
                                                                                            entry[0] > curr_time]
                                                                        future_ends = future_ends_node + func_busy_ends
                                                                        if future_ends:
                                                                                curr_time = int(min(future_ends))
                                                                        else:
                                                                                start = curr_time
                                                                                break
                                                                endt = start + dur

                                                                node_active[node].append((endt, ram_req, deployment_id, idx_m,w))
                                                                # after finishing, add transfer latency before next function can start
                                                                # determine next place
                                                                idx_pos = func_nums.index(idx_m)
                                                                if idx_pos < len(func_nums) - 1:
                                                                        next_m = func_nums[idx_pos + 1]
                                                                        next_place = sel_places[next_m]
                                                                else:
                                                                        next_place = leaf + num_other
                                                                try:
                                                                        transfer = int(np.ceil(Lmat[node][next_place]))
                                                                except Exception:
                                                                        transfer = 0
                                                                curr_time = endt + transfer
                                                        path_finish_times.append(curr_time)
                                                req_done = max(path_finish_times) if path_finish_times else arrival
                                                req_done_list.append(req_done-arrival)
                                                wait = (req_done - arrival) - base_T
                                                if wait < 0:
                                                        wait = 0
                                                #print(w)
                                                #print(wait)
                                                waiting_acc[w, leaf] += wait#(req_done-arrival)#wait
                                                # record a compact request log entry
                                                req_log = {
                                                        'id': int(req_id_counter),
                                                        'workflow': int(w),
                                                        'leaf': int(leaf),
                                                        'arrival': int(arrival),
                                                        'start': int(arrival + wait),
                                                        'end': int(req_done),
                                                        'base_T': int(base_T),
                                                        'wait': int(wait)
                                                }
                                                request_logs.append(req_log)
                                                req_id_counter += 1
                        # update ram_area for utilization (sample at integer second)
                        for ni in range(num_nodes_global):
                                # node_active entries may now include (end, ram, w, m)
                                used_now = sum(entry[1] for entry in node_active[ni] if entry[0] > cur_t)
                                ram_area[ni] += used_now
                                per_node_util[cur_t, ni] = used_now

        overall_requests = np.zeros((num_workflows, num_leaves))
        for t in range(num_workflows):
                for k in range(num_leaves):
                        overall_requests[t, k] = sum(requests[:, t, k])
        select_cost_all=0
        for t in range(num_workflows):
                select_cost=0
                workflow_path=f"workflows/run_{num_run}/requirements_workflow_{t}_0.json"
                placement_path=f"placement/run_{num_run}/opt_{t}_0.json"
                with open(workflow_path, "r") as f:
                        workflow_config = json.load(f)
                with open(placement_path, "r") as f:
                        placement_config = json.load(f)
                num_functions=workflow_config["num_functions"]
                H=placement_config['H']
                T=placement_config['T']
                P=placement_config['P']
                C=placement_config['C']
                D=placement_config['D']
                D_in=placement_config['D_in']
                L=placement_config['L']
                S=placement_config['S']
                num_paths= workflow_config['paths']['num_paths']
                b = placement_config['b']
                a = placement_config['a']
                num_deployment=workflow_config["deployment_number"]
                workflow_overall=np.zeros((num_deployment))
                num_nodes_all=sum(num_nodes_in_level[-1])
                invocations=np.zeros(num_nodes_all)
                placement_overall=0#np.zeros((num_nodes_all))
                for k in range(num_leaves):

                        pred_k_list, lat_upward_list,pos_list = upward_trajectory(k+num_other)

                        selected_workflow = H[
                                pred_k_list[1] - num_other_first_level].index(1)

                        workflow_overall[selected_workflow]+=1
                        time_cost=0
                        money_cost=0
                        #time_cost+=T[selected_workflow][0]
                        T_paths= np.zeros((num_paths,1))

                        D_func = np.zeros((num_functions, 1))
                        C_func = np.zeros((num_functions, 1))
                        placement_func = np.zeros((num_functions,num_nodes_all))
                        for s in range(num_paths):

                                pred_k_list, lat_upward_list, pos_list = upward_trajectory(k + num_other)
                                L_func = np.zeros((num_functions, 1))
                                #b_mat = perwf[w].get('b', [])
                                func_nums = np.where(np.array(b[s])==1)[0].tolist() #if isinstance(b_mat, (list, np.ndarray)) and len(b_mat) > s else []

                                for m in func_nums:
                                        #L_func[m] = lat_upward_list[0]
                                        #L_func[m]=L[pred_k][selected_place]
                                        prev_selected_place = 0
                                        opt_num=0
                                        for r in range(num_levels):
                                                if r!=0:
                                                        opt_num=find_opt(opt_num,prev_selected_place,r)
                                                placement_path=f"placement/run_{num_run}/opt_{t}_{opt_num}.json"
                                                workflow_path = f"workflows/run_{num_run}/requirements_workflow_{t}_{opt_num}.json"
                                                cloud_path = f"cloud/run_{num_run}/requirements_cloud_{r}_{opt_num-ind_start_list[r]}.json"
                                                with open(placement_path, "r") as f:
                                                        curr_placement = json.load(f)
                                                with open(cloud_path, "r") as f:
                                                        curr_cloud = json.load(f)
                                                with open(workflow_path, "r") as f:
                                                        curr_workflow = json.load(f)

                                                curr_P=curr_placement['P']
                                                curr_L = curr_placement['L']
                                                if r==0:

                                                        curr_selected_workflow = selected_workflow
                                                        selected_place = P[selected_workflow * num_functions + m].index(
                                                                1)
                                                else:

                                                        curr_selected_workflow=find_correct_workflow(curr_selected_workflow,curr_workflow["active_workflow_list"])
                                                if curr_P==[]:
                                                        selected_place=0
                                                else:
                                                        selected_place=curr_P[curr_selected_workflow*num_functions+m].index(1)

                                                if r==0:
                                                        data_dependencies = curr_workflow['functions'][f"function_{m}"][
                                                                'data_dependencies']
                                                        for key in data_dependencies.keys():
                                                                value = data_dependencies[key]
                                                                pricing_Storage_Transfer = provider_cost_list[key]["pricing_Storage_Transfer"]
                                                                if key != curr_cloud["providers"][f"provider_{selected_place}"][
                                                                                "name"]:
                                                                        #        D[j,k]=data_send
                                                                        C_func[m] = C_func[m] + pricing_Storage_Transfer * value
                                                        L_func[m] += curr_L[pred_k_list[1]][selected_place]
                                                        if m==0:
                                                                D_in_0=0
                                                                if pred_k_list[1] != selected_place:
                                                                        pricing_data_sent = curr_cloud['providers'][f"provider_{selected_place}"]['pricing_data_sent']
                                                                        D_in_0=curr_workflow['input_data'] * pricing_data_sent

                                                        if m < len(func_nums) - 1:

                                                                next_selected_place = curr_P[
                                                                        selected_workflow * num_functions + func_nums[
                                                                                m + 1]].index(1)
                                                        else:
                                                                next_selected_place = pred_k_list[1]
                                                        D_func[m]=D[m][selected_place][next_selected_place]
                                                                #if pred_k_list[1] != selected_place:
                                                                #        pricing_data_sent = \
                                                                #        curr_cloud['providers'][f"provider_{selected_place}"][
                                                                #                'pricing_data_sent']
                                                                #        D_func[m] = curr_workflow["functions"][f"function_{m}"]["data_send"] * pricing_data_sent

                                                else:
                                                        if pred_k_list[r]==opt_num-ind_start_list[r]:

                                                                with open(placement_path, "r") as f:
                                                                        curr_placement = json.load(f)


                                                                curr_L = curr_placement['L']
                                                                L_func[m] += curr_L[pos_list[r]][selected_place]
                                                        else:
                                                                L_func[m] += curr_L[0][selected_place]
                                                                L_func[m] += lat_upward_list[r]#curr_L[0][pos_list[0]]
                                                #else:
                                                #        L_func[m]+=curr_L[][selected_place]

                                                if r == num_levels-1:
                                                        if curr_cloud['providers'][f"provider_{selected_place}"][
                                                                "name"] == "tinyfaas":
                                                                speedup = 1
                                                        else:
                                                                speedup = curr_workflow["functions"][f"function_{m}"][
                                                                        'speedup']
                                                        #speedup = curr_workflow["functions"][f"function_{m}"]['speedup']
                                                        ram = curr_workflow['functions'][f"function_{m}"]['ram']
                                                        time = curr_workflow['functions'][f"function_{m}"]['time']
                                                        T_func = speedup * time
                                                        #print(T_func)
                                                        pricing_RAM=curr_cloud['providers'][f"provider_{selected_place}"]['pricing_RAM']
                                                        #pricing_Storage_Transfer=curr_cloud['providers'][f"provider_{selected_place}"]['pricing_Storage_Transfer']
                                                        C_func[m] += pricing_RAM*ram*time#speedup
                                                        k_curr=get_leaf(selected_place,opt_num)
                                                        placement_func[m,k_curr]=1
                                                        #print(L_func[m])
                                                        T_paths[s]+=(T_func+L_func[m])
                                                        invocations[k_curr]+=1
                                                        #print(L_func[m])
                                                prev_selected_place = selected_place
                                        pred_k_list,lat_upward_list,pos_list=upward_trajectory(k_curr)
                                L_end=0
                                pred_k_list_new, lat_upward_list_new, pos_list_new = upward_trajectory(k+num_other)
                                for r in range(num_levels-1,-1,-1):

                                        if pred_k_list[r] == pred_k_list_new[r]:
                                                opt_num=pred_k_list[r]+ind_start_list[r]
                                                placement_path = f"placement/run_{num_run}/opt_{t}_{opt_num}.json"
                                                with open(placement_path, "r") as f:
                                                        curr_placement = json.load(f)
                                                curr_L = curr_placement['L']
                                                L_end += curr_L[pos_list[r]][pos_list_new[r]]
                                        else:
                                                L_end += lat_upward_list_new[r]
                                                L_end += lat_upward_list[r]
                                T_paths[s]+=L_end
                        #print(L_func)
                        for r in range(num_nodes_all):
                                placement_overall+=sum(placement_func[:,r])**2
                        time_cost+=np.max(T_paths)
                        money_cost+=np.sum(C_func)+np.sum(D_func)+D_in_0



                                        #time_cost += L[pred_k][selected_place]
                                        #money_cost += D_in[selected_place][0]
                                #next_selected_place = P[selected_workflow*num_functions+m+1].index(1)
                                #next_selected_place = P[selected_workflow*num_functions+m+1].index(1)
                                #money_cost += C[m][selected_place]
                                #time_cost += L[selected_place][next_selected_place]
                                #money_cost += S[m+selected_workflow* num_functions][selected_place]
                        #selected_place = P[selected_workflow * num_functions + num_functions-1].index(1)
                        #money_cost += C[num_functions-1] [selected_place]
                        #time_cost += L[selected_place][pred_k]
                        #money_cost += S[num_functions-1 + selected_workflow * num_functions] [selected_place]
                        time_cost_all+=overall_requests[t,k]*time_cost
                        #print("Time workflow "+str(t)+": "+str(time_cost))
                        #print("Money workflow " + str(t) + ": " + str(money_cost))
                        money_cost_all+=overall_requests[t,k]*money_cost
                select_cost=np.sum(workflow_overall**2)+np.sum(invocations**2)#+placement_overall##+np.sum(placement_overall**2)#num_prob=1
                #print(select_cost)
                select_cost_all+=select_cost

        overall_cost = w_1 * money_cost_all+ w_2 * sum(req_done_list)#(sum(sum(waiting_acc))+time_cost_all)#sum(req_done_list)#time_cost_all+w_3*select_cost_all
        #print(select_cost_all)
        print(sum(sum(waiting_acc)))
        print([overall_cost])
        results_path = f"results/run_{num_run}/results.json"
        if not os.path.exists(os.path.join("results",f"run_{num_run}")):
                os.mkdir(os.path.join("results",f"run_{num_run}"))
        results={}
        results['overall_cost']=overall_cost
        results['money_cost']=money_cost_all
        results['complete_time_cost'] = sum(sum(waiting_acc))#+time_cost_all#sum(req_done_list)
        results['time_cost']=time_cost_all#sum(req_done_list)-sum(sum(waiting_acc))#time_cost_all

        if comparison:
                np.random.seed(42)
                sim_time=parameter_general_config["simulation_time"]
                time_cost_all=0
                money_cost_all=0
                select_cost_all=0
                time_cost=0
                money_cost=0
                request_rates=np.zeros((num_workflows,num_leaves))
                for t in range(num_workflows):
                        cloud_name = f"requirements_cloud_full.json"
                        path_cloud = os.path.join(f"cloud/run_{num_run}", cloud_name)
                        with open(path_cloud, "r") as f:
                                cloud_config = json.load(f)
                        for k in range(num_leaves):
                                request_rates[t,k]=cloud_config["providers"][f"provider_{k+num_other}"]["request_rate"]
                requests=np.zeros((sim_time,num_workflows,num_leaves))
                # prepare structures for a minimal discrete-time scheduler (dt=1)
                # load full cloud to get global node RAM capacities
                cloud_full_path = os.path.join(f"cloud/run_{num_run}", "requirements_cloud_full.json")
                with open(cloud_full_path, 'r') as f:
                        cloud_full = json.load(f)
                num_nodes_global = cloud_full.get('num_nodes', 0)
                node_ram_max = [cloud_full['providers'][f'provider_{i}'].get('max_RAM_curr', 1e9) if cloud_full['providers'][f'provider_{i}'].get('name')=="tinyfaas" else np.inf for i in
                        range(num_nodes_global)]
                # Precompute per-workflow, per-leaf selected places, durations and rams
                perwf = {}
                # helper to reconstruct full P and H from decomposed per-level opt files
                def reconstruct_full_solution(w):
                        # returns sol_conf dict with keys P (list of rows) and H (list)
                        wf_path = os.path.join(f"workflows/run_{num_run}", f"requirements_workflow_{w}_0.json")
                        try:
                                with open(wf_path, 'r') as f:
                                        wf_conf = json.load(f)
                        except Exception:
                                wf_conf = {}
                        num_funcs = wf_conf.get('num_functions', 0)
                        # total global nodes
                        num_nodes_all = cloud_full.get('num_nodes', 0)
                        # initialize P_full rows: we'll create one row per (deployment * function)
                        # We don't know deployment count per se here; we'll create rows for one deployment placeholder
                        P_full = [[0 for _ in range(num_nodes_all)] for _ in range(num_funcs)]
                        # H_full: for each leaf, selected workflow index (we'll store as one-hot length 1 per leaf)
                        H_full = [[0] for _ in range(num_leaves)]

                        # try to load full placement L if available (to reuse latencies)
                        L_full = []
                        full_path = os.path.join(f"placement/run_{num_run}", f"opt_{w}_full.json")
                        try:
                                with open(full_path, 'r') as f:
                                        full_place_tmp = json.load(f)
                                        if 'L' in full_place_tmp:
                                                L_full = full_place_tmp.get('L', [])
                        except Exception:
                                pass

                        # try to load top-level placement for workflow w (opt_{w}_0.json) to get top H if present
                        top_path = os.path.join(f"placement/run_{num_run}", f"opt_{w}_0.json")
                        try:
                                with open(top_path, 'r') as f:
                                        top_place = json.load(f)
                        except Exception:
                                top_place = {}

                        for leaf in range(num_leaves):
                                # determine selected workflow at top level if possible
                                try:
                                        pred_k_list, lat_upward_list, pos_list = upward_trajectory(leaf + num_other)
                                except Exception:
                                        pred_k_list, lat_upward_list, pos_list = ([], [], [])
                                sel_work = 0
                                try:
                                        Htop = top_place.get('H', [])
                                        if Htop:
                                                sel_work = int(np.where(np.array(Htop[pred_k_list[1] - num_other_first_level]) == 1)[0][0])
                                except Exception:
                                        sel_work = 0
                                # mark H_full one-hot (length 1 per earlier assumptions)
                                try:
                                        H_full[leaf] = [int(sel_work)]
                                except Exception:
                                        H_full[leaf] = [0]

                                # for each function, walk levels to find global node
                                for m in range(num_funcs):
                                        prev_selected_place = 0
                                        opt_num = 0
                                        curr_selected_workflow = sel_work
                                        k_curr = 0
                                        for r in range(num_levels):
                                                if r != 0:
                                                        opt_num = find_opt(opt_num, prev_selected_place, r)
                                                placement_path = f"placement/run_{num_run}/opt_{w}_{opt_num}.json"
                                                try:
                                                        with open(placement_path, 'r') as f:
                                                                curr_placement = json.load(f)
                                                except Exception:
                                                        curr_placement = {}

                                                curr_P = curr_placement.get('P', [])
                                                curr_workflow = {}
                                                try:
                                                        workflow_path = f"workflows/run_{num_run}/requirements_workflow_{w}_{opt_num}.json"
                                                        with open(workflow_path, 'r') as f:
                                                                curr_workflow = json.load(f)
                                                except Exception:
                                                        curr_workflow = {}

                                                if r == 0:
                                                        # top-level: selected_workflow already known
                                                        try:
                                                                if curr_P:
                                                                        selected_place = int(np.where(np.array(curr_P[curr_selected_workflow * num_funcs + m]) == 1)[0][0])
                                                                else:
                                                                        selected_place = 0
                                                        except Exception:
                                                                selected_place = 0
                                                else:
                                                        # map curr_selected_workflow into local index if needed
                                                        try:
                                                                if 'active_workflow_list' in curr_workflow and curr_workflow['active_workflow_list']:
                                                                        curr_selected_workflow = find_correct_workflow(curr_selected_workflow, curr_workflow['active_workflow_list'])
                                                        except Exception:
                                                                pass
                                                        try:
                                                                if curr_P:
                                                                        selected_place = int(np.where(np.array(curr_P[curr_selected_workflow * num_funcs + m]) == 1)[0][0])
                                                                else:
                                                                        selected_place = 0
                                                        except Exception:
                                                                selected_place = 0

                                                # record L if available at any level
                                                if not L_full and 'L' in curr_placement:
                                                        L_full = curr_placement.get('L', L_full)

                                                # if last level, translate to global node index
                                                if r == num_levels - 1:
                                                        try:
                                                                k_curr = get_leaf(selected_place, opt_num)
                                                        except Exception:
                                                                k_curr = selected_place

                                                prev_selected_place = selected_place

                                        # set P_full row: combine using sel_work index offset
                                        try:
                                                row_idx = sel_work * num_funcs + m
                                        except Exception:
                                                row_idx = m
                                        # ensure P_full has enough rows
                                        if row_idx >= len(P_full):
                                                # extend rows
                                                for _ in range(row_idx - len(P_full) + 1):
                                                        P_full.append([0 for _ in range(num_nodes_all)])
                                        if 0 <= k_curr < num_nodes_all:
                                                P_full[row_idx][k_curr] = 1

                        return {'P': P_full, 'H': H_full, 'L': L_full}
                for w in range(num_workflows):
                        wf_path = os.path.join(f"workflows/run_{num_run}", f"requirements_workflow_{w}_0.json")
                        sol_path = os.path.join(f"placement/run_{num_run}", f"opt_{w}_full.json")
                        node_path = os.path.join(f"cloud/run_{num_run}", f"requirements_cloud_full.json")
                        try:
                                with open(wf_path, 'r') as f:
                                        wf_conf = json.load(f)
                                with open(node_path, 'r') as f:
                                        node_conf = json.load(f)
                        except Exception:
                                wf_conf = {}
                                node_conf = {}
                        # decide whether to use decomposed reconstruction or centralized full placement
                        decomposed_mode = False#parameter_general_config.get('decomposed_mode', False)
                        sol_conf = {}
                        if decomposed_mode:
                                try:
                                        sol_conf = reconstruct_full_solution(w)
                                except Exception:
                                        sol_conf = {}
                        else:
                                try:
                                        with open(sol_path, 'r') as f:
                                                sol_conf = json.load(f)
                                except Exception:
                                        sol_conf = {}
                                # fallback: if full placement missing, try to reconstruct from decomposed pieces
                                if not sol_conf.get('P'):
                                        try:
                                                sol_conf = reconstruct_full_solution(w)
                                        except Exception:
                                                sol_conf = sol_conf or {}
                        P = sol_conf.get('P', [])
                        H = sol_conf.get('H', [])
                        L = sol_conf.get('L', [])
                        Speed = sol_conf.get('Speed', None)
                        a = sol_conf.get('a', [])
                        b = sol_conf.get('b', [])
                        if len(b) > 1:
                                for r in range(1, len(b)):
                                        b[r][0] = 0
                                        b[r][-1] = 0
                        num_funcs = wf_conf.get('num_functions', 0)
                        perwf[w] = {}
                        for leaf in range(num_leaves):
                                sel_work = 0
                                try:
                                        sel_work = int(np.where(np.array(H[leaf]) == 1)[0][0]) if H else 0
                                except Exception:
                                        sel_work = 0
                                # selected places for each function (global node indices as in full placement)
                                selected_places = []
                                for m in range(num_funcs):
                                        try:
                                                row = P[sel_work * num_funcs + m]
                                                selected_places.append(int(np.where(np.array(row) == 1)[0][0]))
                                        except Exception:
                                                selected_places.append(0)

                                # durations (ceil) and ram per function given the selected node
                                durations = [0] * num_funcs
                                rams = [0] * num_funcs
                                for m in range(num_funcs):
                                        node = selected_places[m]
                                        node_name = node_conf["providers"][f"provider_{node}"]["name"]
                                        try:
                                                func_conf = wf_conf['functions'][f"function_{m}"]
                                                base_time = func_conf.get('time', 0)
                                                if Speed:
                                                        try:
                                                                speedup = float(np.array(Speed)[m][node])
                                                        except Exception:
                                                                speedup = func_conf.get('speedup', 1)
                                                else:
                                                        if node_name != "tinyfaas":
                                                                speedup = func_conf.get('speedup', 1)
                                                        else:
                                                                speedup = 1
                                                        #speedup = func_conf.get('speedup', 1)
                                                dur = int(np.ceil(speedup * base_time))
                                                durations[m] = dur
                                                rams[m] = func_conf.get('ram', 0)
                                        except Exception:
                                                durations[m] = 0
                                                rams[m] = 0

                                perwf[w][leaf] = {
                                        'selected_places': selected_places,
                                        'deployment': int(sel_work),
                                        'durations': durations,
                                        'rams': rams,
                                        'L': L
                                }
                        # store workflow-level path matrices so simulation can compute base_T correctly
                        perwf[w]['a'] = a
                        perwf[w]['b'] = b
                        try:
                                perwf[w]['num_paths'] = wf_conf.get('paths', {}).get('num_paths', 0)
                        except Exception:
                                perwf[w]['num_paths'] = 0

                curr_utilization=np.zeros((num_nodes_global,1))
                func_blocked=np.zeros((num_workflows,num_functions))
                # node_active holds tuples (end_time, ram)
                node_active = [[] for _ in range(num_nodes_global)]
                # ram area accumulator for utilization
                ram_area = [0.0] * num_nodes_global

                # minimal per-workflow/leaf waiting accumulator
                waiting_acc = np.zeros((num_workflows, num_leaves))

                # per-time-step per-node utilization (samples of used RAM)
                per_node_util = np.zeros((sim_time, num_nodes_global), dtype=float)

                # per-request logs: collect arrival, start (approx), end, base_T, wait, workflow, leaf
                request_logs = []
                req_id_counter = 0
                req_done_list=[]
                rng = np.random.default_rng(42)
                for cur_t in range(sim_time):
                        # generate arrivals for this second
                        requests[cur_t]=rng.poisson(request_rates)#np.random.poisson(request_rates)
                        # choose simulation mode: lazy_start toggles whether functions are started only when reached
                        lazy_start = parameter_general_config.get('lazy_start', False)
                        if lazy_start:
                                # LAZY START MODE: enqueue requests and only start functions when their turn arrives
                                # prune finished entries at the second boundary to keep node_active small
                                for ni in range(num_nodes_global):
                                        node_active[ni] = [entry for entry in node_active[ni] if entry[0] > cur_t]

                                # initialize pending queue on first iteration
                                if cur_t == 0:
                                        pending_requests = []

                                # enqueue arrivals for this second (FIFO)
                                for w in range(num_workflows):
                                        for leaf in range(num_leaves):
                                                n = int(requests[cur_t, w, leaf])
                                                if n <= 0:
                                                        continue
                                                info = perwf.get(w, {}).get(leaf, None)
                                                if info is None:
                                                        continue
                                                sel_places = info['selected_places']
                                                durs = info['durations']
                                                rams = info['rams']
                                                Lmat = info['L']
                                                # compute base_T using workflow path definitions 'a' (max over paths)
                                                base_T_paths = []
                                                a_mat = perwf[w].get('a', [])
                                                b_mat = perwf[w].get('b', [])
                                                num_paths_local = perwf[w].get('num_paths', 0)
                                                for s in range(num_paths_local):
                                                        func_nums = np.where(np.array(b_mat[s])==1)[0].tolist() if isinstance(b_mat, (list, np.ndarray)) and len(b_mat) > s else []
                                                        tot = 0
                                                        for idx_m in func_nums:
                                                                tot += durs[idx_m]
                                                                # determine next place
                                                                if idx_m < len(func_nums) - 1:
                                                                        next_m = func_nums[func_nums.index(idx_m) + 1]
                                                                        next_place = sel_places[next_m]
                                                                else:
                                                                        next_place = leaf + num_other
                                                                try:
                                                                        tot += int(np.ceil(Lmat[sel_places[idx_m]][next_place]))
                                                                except Exception:
                                                                        pass
                                                        base_T_paths.append(tot)
                                                base_T = max(base_T_paths) if base_T_paths else 0

                                                deployment_id = int(info.get('deployment', w))
                                                for i in range(n):
                                                        req = {
                                                                'id': int(req_id_counter),
                                                                'workflow': int(w),
                                                                'leaf': int(leaf),
                                                                'arrival': int(cur_t),
                                                                'deployment': int(info.get('deployment', w)),
                                                                'sel_places': sel_places,
                                                                'durs': durs,
                                                                'rams': rams,
                                                                'L': Lmat,
                                                                'base_T': int(base_T),
                                                                'next_idx': 0,
                                                                'start_times': [],
                                                                'end_times': []
                                                        }
                                                        pending_requests.append(req)
                                                        req_id_counter += 1

                                # attempt to start functions for pending requests in FIFO order
                                still_pending = []
                                for req in pending_requests:
                                        w = req['workflow']
                                        leaf = req['leaf']
                                        sel_places = req['sel_places']
                                        durs = req['durs']
                                        rams = req['rams']
                                        Lmat = req['L']
                                        idx = req['next_idx']
                                        num_funcs = len(durs)

                                        if idx >= num_funcs:
                                                # already finished; record completion
                                                if req['end_times']:
                                                        last_node = sel_places[-1]
                                                        last_end = req['end_times'][-1]
                                                        try:
                                                                final_transfer = int(np.ceil(Lmat[last_node][leaf + num_other]))
                                                        except Exception:
                                                                final_transfer = 0
                                                        req_done = last_end + final_transfer
                                                else:
                                                        req_done = req['arrival']
                                                req_done_list.append(req_done)
                                                wait = max(0, req_done - req['arrival'] - req['base_T'])
                                                waiting_acc[w, leaf] += wait
                                                # log
                                                request_logs.append({
                                                        'id': req['id'],
                                                        'workflow': w,
                                                        'leaf': leaf,
                                                        'arrival': req['arrival'],
                                                        'start': req['start_times'][0] if req['start_times'] else req['arrival'],
                                                        'end': req_done,
                                                        'base_T': req['base_T'],
                                                        'wait': int(wait)
                                                })
                                                continue

                                        # check if predecessor finished and transfer completed
                                        ready = False
                                        if idx == 0:
                                                ready = True
                                        else:
                                                if len(req['end_times']) >= idx:
                                                        prev_end = req['end_times'][idx-1]
                                                        prev_node = sel_places[idx-1]
                                                        try:
                                                                next_place = sel_places[idx]
                                                        except Exception:
                                                                next_place = leaf + num_other
                                                        try:
                                                                transfer = int(np.ceil(Lmat[prev_node][next_place]))
                                                        except Exception:
                                                                transfer = 0
                                                        if prev_end + transfer <= cur_t:
                                                                ready = True

                                        if not ready:
                                                still_pending.append(req)
                                                continue

                                        # try to start this function at current time cur_t
                                        node = sel_places[idx]
                                        dur = durs[idx]
                                        ram_req = rams[idx]
                                        used = sum(entry[1] for entry in node_active[node] if entry[0] > cur_t)
                                        deployment_id = req.get('deployment', w)
                                        func_busy = any(len(entry) >= 4 and entry[0] > cur_t and entry[2] == deployment_id and entry[3] == idx for entry in node_active[node])
                                        if used + ram_req <= node_ram_max[node] and (not func_busy):
                                                # start now
                                                start = cur_t
                                                endt = start + dur
                                                node_active[node].append((endt, ram_req, deployment_id, idx, req['id'],w))
                                                req['start_times'].append(start)
                                                req['end_times'].append(endt)
                                                req['next_idx'] += 1
                                                # if there are more functions, keep in pending to try next in later ticks
                                                if req['next_idx'] < num_funcs:
                                                        still_pending.append(req)
                                                else:
                                                        # will be recorded as finished on next loop iteration
                                                        still_pending.append(req)
                                        else:
                                                still_pending.append(req)

                                pending_requests = still_pending

                                # update ram_area and per-node util for this second
                                for ni in range(num_nodes_global):
                                        used_now = sum(entry[1] for entry in node_active[ni] if entry[0] > cur_t)
                                        ram_area[ni] += used_now
                                        per_node_util[cur_t, ni] = used_now
                        else:
                                # RESERVE-ALL MODE (existing logic)
                                # prune finished entries at the second boundary to keep node_active small
                                for ni in range(num_nodes_global):
                                        node_active[ni] = [entry for entry in node_active[ni] if entry[0] > cur_t]
                                # enqueue and schedule arrivals (FIFO within this second)
                                for w in range(num_workflows):
                                        for leaf in range(num_leaves):
                                                n = int(requests[cur_t, w, leaf])
                                                if n <= 0:
                                                        continue
                                                info = perwf.get(w, {}).get(leaf, None)
                                                if info is None:
                                                        continue
                                                sel_places = info['selected_places']
                                                durs = info['durations']
                                                rams = info['rams']
                                                Lmat = info['L']
                                                # compute static base path time for this request (max over paths)
                                                base_T_paths = []
                                                a_mat = perwf[w].get('a', [])
                                                num_paths_local = perwf[w].get('num_paths', 0)
                                                for s in range(num_paths_local):
                                                        b_mat = perwf[w].get('b', [])
                                                        func_nums = np.where(np.array(b_mat[s])==1)[0].tolist() if isinstance(b_mat, (list, np.ndarray)) and len(b_mat) > s else []
                                                        tot = 0
                                                        for idx_m in func_nums:
                                                                tot += durs[idx_m]
                                                                # transfer to next
                                                                # determine next place
                                                                # if last function, next is leaf (k+num_other)
                                                                # else next selected place
                                                                # avoid index errors
                                                                if idx_m < len(func_nums) - 1:
                                                                        next_m = func_nums[func_nums.index(idx_m)+1]
                                                                        next_place = sel_places[next_m]
                                                                else:
                                                                        next_place = leaf + num_other
                                                                try:
                                                                        tot += int(np.ceil(Lmat[sel_places[idx_m]][next_place]))
                                                                except Exception:
                                                                        pass
                                                        base_T_paths.append(tot)
                                                base_T = max(base_T_paths) if base_T_paths else 0

                                                # schedule n requests sequentially (spaced within the second FIFO)
                                                deployment_id = int(info.get('deployment', w))
                                                for i in range(n):
                                                        arrival = cur_t
                                                        path_finish_times = []
                                                        # for each path, simulate sequential function execution with resource checks
                                                        b_mat = perwf[w].get('b', [])
                                                        num_paths_local = perwf[w].get('num_paths', 0)
                                                        for s in range(num_paths_local):
                                                                func_nums = np.where(np.array(b_mat[s]) == 1)[0].tolist() if isinstance(b_mat, list) and len(b_mat) > s else []
                                                                curr_time = arrival
                                                                for idx_m in func_nums:
                                                                        node = sel_places[idx_m]
                                                                        dur = durs[idx_m]
                                                                        ram_req = rams[idx_m]
                                                                        # find earliest start time when node has enough free RAM
                                                                        # AND when the same (workflow, function) is not already running anywhere
                                                                        while True:
                                                                                # current used RAM on this node at curr_time
                                                                                used = sum(entry[1] for entry in node_active[node] if entry[0] > curr_time)
                                                                                # only consider same-function instances running on the same node
                                                                                func_busy_ends = [entry[0] for entry in
                                                                                          node_active[node] if
                                                                                          len(entry) >= 4 and entry[
                                                                                                  0] > curr_time and
                                                                                          entry[2] == deployment_id and entry[
                                                                                                  3] == idx_m and entry[4] == w]#[entry[0] for entry in node_active[node] if len(entry) >= 4 and entry[0] > curr_time and entry[2] == deployment_id and entry[3] == idx_m]
                                                                                #print(used + ram_req)
                                                                                if used + ram_req <= node_ram_max[node] and (not func_busy_ends):
                                                                                        start = curr_time
                                                                                        break

                                                                                # advance to earliest finishing task relevant to capacity or function lock
                                                                                future_ends_node = [entry[0] for entry in node_active[node] if entry[0] > curr_time]
                                                                                future_ends = future_ends_node + func_busy_ends
                                                                                if future_ends:
                                                                                        curr_time = int(min(future_ends))
                                                                                else:
                                                                                        start = curr_time
                                                                                        break
                                                                        endt = start + dur
                                                                        # include workflow/function metadata so we can enforce per-(w,m) blocking
                                                                        node_active[node].append((endt, ram_req, deployment_id, idx_m,w))
                                                                        # after finishing, add transfer latency before next function can start
                                                                        # determine next place
                                                                        idx_pos = func_nums.index(idx_m)
                                                                        if idx_pos < len(func_nums) - 1:
                                                                                next_m = func_nums[idx_pos + 1]
                                                                                next_place = sel_places[next_m]
                                                                        else:
                                                                                next_place = leaf + num_other
                                                                        try:
                                                                                transfer = int(np.ceil(Lmat[node][next_place]))
                                                                        except Exception:
                                                                                transfer = 0
                                                                        curr_time = endt + transfer
                                                                path_finish_times.append(curr_time)
                                                        req_done = max(path_finish_times) if path_finish_times else arrival
                                                        req_done_list.append(req_done-arrival)
                                                        wait = (req_done - arrival) - base_T
                                                        if wait < 0:
                                                                wait = 0
                                                        #print(w)
                                                        #print(wait)
                                                        waiting_acc[w, leaf] += wait#(req_done-arrival)#wait
                                                        # record a compact request log entry
                                                        req_log = {
                                                                'id': int(req_id_counter),
                                                                'workflow': int(w),
                                                                'leaf': int(leaf),
                                                                'arrival': int(arrival),
                                                                'start': int(arrival + wait),
                                                                'end': int(req_done),
                                                                'base_T': int(base_T),
                                                                'wait': int(wait)
                                                        }
                                                        request_logs.append(req_log)
                                                        req_id_counter += 1
                                # update ram_area for utilization (sample at integer second)
                                for ni in range(num_nodes_global):
                                        # node_active entries may now include (end, ram, w, m)
                                        used_now = sum(entry[1] for entry in node_active[ni] if entry[0] > cur_t)
                                        ram_area[ni] += used_now
                                        per_node_util[cur_t, ni] = used_now


                overall_requests=np.zeros((num_workflows,num_leaves))
                for t in range(num_workflows):
                        for k in range(num_leaves):
                                overall_requests[t,k]=sum(requests[:,t,k])

                for t in range(num_workflows):

                        cloud_name = f"requirements_cloud_full.json"
                        sol_name = f"opt_{t}"
                        path_cloud = os.path.join(f"cloud/run_{num_run}", cloud_name)
                        path_workflow = os.path.join(f"workflows/run_{num_run}", f"requirements_workflow_{t}" + "_0.json")
                        path_solution = os.path.join(f"placement/run_{num_run}", sol_name + "_full.json")

                        with open(path_cloud, "r") as f:
                                cloud_config = json.load(f)
                        with open(path_workflow, "r") as f:  # requirements_workflow_0.json
                                workflow_config = json.load(f)
                        with open(path_solution, "r") as f:  # requirements_workflow_0.json
                                placement_config = json.load(f)
                        num_functions = workflow_config["num_functions"]
                        num_deployment = workflow_config["deployment_number"]
                        num_nodes=cloud_config["num_nodes"]
                        H = placement_config['H']
                        T = placement_config['T']
                        P = placement_config['P']
                        C = placement_config['C']
                        D = placement_config['D']
                        D_in = placement_config['D_in']
                        L = placement_config['L']
                        S = placement_config['S']
                        num_paths = workflow_config['paths']['num_paths']
                        b = placement_config['b']
                        a = placement_config['a']
                        select_cost=0
                        invocations=np.zeros((num_nodes))
                #        #for k in range(num_leaves):
                #        #        for m in range(num_deployment):
                #                        #for i in range(num_nodes):
                #                         #       select_cost += (H[k][n]*sum([P[num_functions*n+m][i] for m in range(num_functions)])) ** 2
                #        for n in range(num_deployment):
                #                select_cost += sum([H[k][n] for k in range(num_leaves)]) ** 2
                #                print(select_cost)
                        for k in range(num_leaves):
                                #pred_k, lat_upward = upward_trajectory(k + num_other)
                                pred_k=k+num_other
                                selected_workflow = H[k].index(1)
                                time_cost = 0
                                money_cost = 0
                                # time_cost+=T[selected_workflow][0]
                                T_paths = np.zeros((num_paths, 1))
                                D_func = np.zeros((num_functions, 1))
                                C_func = np.zeros((num_functions, 1))
                                L_func = np.zeros((num_functions, 1))
                                for s in range(num_paths):
                                        pred_k = k + num_other
                                        #b_mat = perwf[w].get('b', [])
                                        func_nums = np.where(np.array(b[s]) == 1)[0].tolist() #if isinstance(b_mat, (list, np.ndarray)) and len(b_mat) > s else []

                                        for r,m in enumerate(func_nums):
                                                #L_func[m] = lat_upward
                                                selected_place = P[selected_workflow * num_functions + m].index(1)
                                                if m<len(func_nums)-1:

                                                        next_selected_place=P[selected_workflow * num_functions + func_nums[r+1]].index(1)
                                                else:
                                                        next_selected_place=pred_k
                                                curr_selected_workflow = selected_workflow

                                                L_func[m] = L[pred_k][selected_place]
                                                #print(L_func[m])
                                                if m == 0:
                                                        #D_in=0
                                                        pricing_data_sent = cloud_config['providers'][
                                                                f"provider_{selected_place}"][
                                                                'pricing_data_sent']
                                                        D_in_0 = D_in[selected_place]#workflow_config[
                                                               #        'input_data'] * pricing_data_sent
                                                #else:

                                                pricing_data_sent = \
                                                        cloud_config['providers'][
                                                                f"provider_{selected_place}"][
                                                                'pricing_data_sent']
                                                D_func[m] =D[m][selected_place][next_selected_place]# \
                                                #workflow_config["functions"][f"function_{m}"][
                                                #        "data_send"] * pricing_data_sent

                                                if cloud_config['providers'][f"provider_{selected_place}"]["name"]=="tinyfaas":
                                                        speedup=1
                                                else:
                                                        speedup = workflow_config["functions"][f"function_{m}"][
                                                                'speedup']
                                                ram = workflow_config['functions'][f"function_{m}"]['ram']
                                                time = workflow_config['functions'][f"function_{m}"][
                                                        'time']
                                                T_func = speedup * time
                                                data_dependencies = workflow_config['functions'][f"function_{m}"][
                                                        'data_dependencies']
                                                for key in data_dependencies.keys():
                                                        value = data_dependencies[key]
                                                        pricing_Storage_Transfer = provider_cost_list[key][
                                                                "pricing_Storage_Transfer"]
                                                        if key != cloud_config["providers"][f"provider_{selected_place}"][
                                                                "name"]:
                                                                #        D[j,k]=data_send
                                                                C_func[m] = C_func[m] + pricing_Storage_Transfer * value
                                                pricing_RAM = \
                                                cloud_config['providers'][f"provider_{selected_place}"][
                                                        'pricing_RAM']
                                                C_func[m] += pricing_RAM * ram  * time#speedup
                                                #k_curr = get_leaf(selected_place, opt_num)
                                                T_paths[s] += (T_func+L_func[m])
                                                pred_k=selected_place
                                                invocations[selected_place]+=1

                                        T_paths[s]+=L[selected_place][k+num_other]

                                #print(T_paths)
                                time_cost += np.max(T_paths)
                                #print(np.sum(C_func))
                                #print(np.sum(D_func))
                                #print(D_in_0)
                                #print(D_func)

                                money_cost += np.sum(C_func) + np.sum(D_func) + D_in_0

                                # time_cost += L[pred_k][selected_place]
                                # money_cost += D_in[selected_place][0]
                                # next_selected_place = P[selected_workflow*num_functions+m+1].index(1)
                                # money_cost += C[m][selected_place]
                                # time_cost += L[selected_place][next_selected_place]
                                # money_cost += S[m+selected_workflow* num_functions][selected_place]
                                # selected_place = P[selected_workflow * num_functions + num_functions-1].index(1)
                                # money_cost += C[num_functions-1] [selected_place]
                                # time_cost += L[selected_place][pred_k]
                                # money_cost += S[num_functions-1 + selected_workflow * num_functions] [selected_place]

                                time_cost_all += overall_requests[t,k]*time_cost
                                money_cost_all += overall_requests[t,k]*money_cost
                        #select_cost_all += select_cost
                        #select_cost_all+=np.sum(invocations**2)
        overall_cost = w_1 * money_cost_all+w_2 * sum(req_done_list)#(sum(sum(waiting_acc))+time_cost_all)#sum(req_done_list)#time_cost_all#+w_3*select_cost_all
        print(overall_cost)
        results['overall_cost_comparison'] = overall_cost[0]

        # write the high-level results
        with open(results_path, "w") as f:
                json.dump(results, f, indent=4)

        # write detailed simulation traces so you can inspect utilization, requests and waiting
        detailed = {
                'per_node_utilization': per_node_util.tolist(),
                'request_logs': request_logs,
                'waiting_acc': waiting_acc.tolist()
        }
        detailed_path = os.path.join(f"results/run_{num_run}", f"detailed_simulation_run_{num_run}.json")
        with open(detailed_path, 'w') as f:
                json.dump(detailed, f, indent=2)