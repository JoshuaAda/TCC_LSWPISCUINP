import numpy as np
import json
import networkx as nx
import os
import re
def update_cloud_config(requirements_cloud_config, requirements_workflow_config, P):
    num_functions = requirements_workflow_config["num_functions"]
    for i in range(P.shape[1]):
        ram_add = 0
        for k in range(P.shape[0]):
            m = int(k % num_functions)
            ram_add += P[k, i] * requirements_workflow_config["functions"][f"function_{m}"]["ram"] #* \
                       #requirements_workflow_config["functions"][f"function_{m}"]["prob_request"]
        requirements_cloud_config["providers"][f"provider_{i}"]["max_Ram_curr"] = \
        requirements_cloud_config["providers"][f"provider_{i}"]["max_RAM_curr"] - ram_add
    return requirements_cloud_config


def update_requirements_config(requirements_workflow_config, P,H, current_node,current_leave_k, num_nodes,seed=42):
    np.random.seed(seed)
    num_functions = requirements_workflow_config["num_functions"]
    num_workflows = requirements_workflow_config["deployment_number"]
    n_list = []
    if len(P) == 0:
        num_workflows = 0
    else:
        for n in range(num_workflows):
            if all(P[n * num_functions:(n + 1) * num_functions, current_node] == 0):
                num_workflows -= 1
            else:
                n_list.append(n)
        requirements_workflow_config["active_workflow_list"]=n_list
        if current_leave_k==-1:
            selection_list=[current_leave_k]
        else:
            selection_list=H[current_leave_k,:].tolist()
        requirements_workflow_config["selection_list"]=selection_list
        for m in range(num_functions):
            liste = []
            for n in range(num_workflows):
                num = n_list[n]
                if P[num * num_functions + m, current_node] == 0:
                    liste.append(n)
            requirements_workflow_config["functions"][f"function_{m}"]["function_set"] = liste
    for m in range(num_functions):
        if requirements_workflow_config["functions"][f"function_{m}"]["data_dependencies"] != {}:
            key = \
            [key for key in requirements_workflow_config["functions"][f"function_{m}"]["data_dependencies"].keys()][0]
            #provider = np.random.randint(num_nodes)
            value = requirements_workflow_config["functions"][f"function_{m}"]["data_dependencies"][key]
            #requirements_workflow_config["functions"][f"function_{m}"]["data_dependencies"]={}
            #match = re.search(r'provider_(\d+)', key)
            #number = int(match.group(1))
            #if number==current_node:
            requirements_workflow_config["functions"][f"function_{m}"]["data_dependencies"][
            key] = value#f"provider_{provider}"
    requirements_workflow_config["deployment_number"] = num_workflows
    return requirements_workflow_config


def generate_connected_graph_with_paths(n_nodes, n_parallel_paths=2, seed=42):
    # assert n_nodes >= 4, "Need at least 4 nodes to have interesting parallel paths"
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    G = nx.DiGraph()

    nodes = list(range(n_nodes))
    start, finish = 0, n_nodes - 1
    G.add_nodes_from(nodes)

    # Add parallel paths
    available_nodes = set(nodes[1:-1])
    path_nodes = list(available_nodes)

    rng.shuffle(path_nodes)
    chunks = np.array_split(path_nodes, n_parallel_paths)
    path_list = []

    for chunk in chunks:
        # for m,c in enumerate(chunk):
        #    c= int(c)
        #    chunk[m]=c
        path = [start] + chunk.tolist() + [finish]
        path_list.append(path)
        for u, v in zip(path[:-1], path[1:]):
            G.add_edge(u, v)

    # Ensure connectivity by adding extra random edges
    n_extra_edges = rng.integers(low=1, high=n_nodes)
    for _ in range(n_extra_edges):
        u, v = rng.choice(nodes, 2, replace=False)
        if not G.has_edge(u, v) and u != v:
            G.add_edge(u, v)

    return G, path_list


def generate_random_workflows(num_workflows,num_opts, config_random_workflows,provider_name, num_run=0,seed=42):
    np.random.seed(seed)
    if not os.path.exists(os.path.join("workflows",f"run_{num_run}")):
        os.mkdir(os.path.join("workflows",f"run_{num_run}"))
    deploy_min=config_random_workflows["deploy_min"]
    deploy_max=config_random_workflows["deploy_max"]
    func_min=config_random_workflows["func_min"]
    func_max = config_random_workflows["func_max"]
    input_data_max = config_random_workflows["input_data_max"]
    time_min  = config_random_workflows["time_min"]
    time_max  = config_random_workflows["time_max"]
    speedup_min  = config_random_workflows["speedup_min"]
    speedup_max  = config_random_workflows["speedup_max"]
    ram_min  = config_random_workflows["ram_min"]
    ram_max  = config_random_workflows["ram_max"]
    #prob_min  = config_random_workflows["prob_min"]
    #prob_max  = config_random_workflows["prob_max"]
    data_sent_min  = config_random_workflows["data_sent_min"]
    data_sent_max  = config_random_workflows["data_sent_max"]
    data_dependencies_prob  = config_random_workflows["data_dependencies_prob"]
    data_dependencies_max = config_random_workflows["data_dependencies_max"]
    data_dependecies_list = ['None', 0]

    workflow_name_list = []
    for i in range(num_workflows):
        workflow_name = f"requirements_workflow_{i}"
        workflow_name_list.append(workflow_name)
        config = dict()
        config["deployment_number"] = np.random.randint(deploy_min, deploy_max)
        num_functions = np.random.randint(func_min, func_max)
        config["num_functions"] = num_functions
        config["num_requests"] = {}
        config["selection_list"] = {}
        # for node in range(num_nodes):
        #    name=f"provider_{node}"
        #    value=np.random.uniform(0,1)
        #    config["num_requests"][name]=value
        # config["num_requests"]={}
        n_parallel_paths = np.random.randint(1, num_functions - 1)
        G, paths = generate_connected_graph_with_paths(num_functions, n_parallel_paths=n_parallel_paths, seed=i)
        config["functions"] = {}
        config["paths"] = {
            "num_paths": n_parallel_paths,
        }
        config["input_data"] = np.random.uniform(0, input_data_max)
        config["input_functions"] = ["function_0"]
        config["output_functions"] = [f"function_{num_functions - 1}"]
        for m in range(len(paths)):
            config["paths"].update({str(m): paths[m]})

        for k in range(num_functions):
            p_list=[(data_dependencies_prob)/(len(provider_name)-1) for k in range(len(provider_name)-1)]+[1-data_dependencies_prob]
            value=np.random.choice(len(provider_name), 1, p=p_list)[0]
            string = provider_name[value]#f"provider_{value}"
            if provider_name[value]=="tinyfaas":
                config["functions"][f"function_{k}"] = {
                    "name": f"function_{k}",
                    "time": np.random.uniform(time_min, time_max),
                    "speedup": np.random.uniform(speedup_min, speedup_max),
                    "ram": np.random.uniform(ram_min, ram_max),
                    #"prob_request": np.random.uniform(prob_min, prob_max),
                    "data_send": np.random.uniform(data_sent_min, data_sent_max),
                    "data_dependencies": {},  # np.random.uniform(1,3)
                    "function_set": {}
                }
            else:
                config["functions"][f"function_{k}"] = {
                    "name": f"function_{k}",
                    "time": np.random.uniform(time_min, time_max),
                    "speedup": np.random.uniform(speedup_min, speedup_max),
                    "ram": np.random.uniform(ram_min, ram_max),
                    #"prob_request": np.random.uniform(prob_min, prob_max),
                    "data_send": np.random.uniform(data_sent_min, data_sent_max),
                    "data_dependencies": {string: np.random.uniform(0, data_dependencies_max)},  # np.random.uniform(1,3)
                    "function_set": {}
                }

        for k in range(num_opts):
            path = os.path.join(f"workflows/run_{num_run}", f"requirements_workflow_{i}_{k}.json")
            with open(path, "w") as f:
                json.dump(config, f, indent=4)
    config_requirements={}

    config_requirements["num_workflows"]=num_workflows
    config_requirements["workflow_list"]=workflow_name_list
    path = os.path.join(f"workflows/run_{num_run}", f"workflow_config.json")
    with open(path, "w") as f:
        json.dump(config_requirements, f, indent=4)
    return workflow_name_list


def generate_cloud(num_levels=2, num_run=0,provider_name=["aws","google", "tinyfaas"],num_tiny_first=2,provider_cost_list=[],provider_dev=[],config_random_cloud=[],seed=42):
    np.random.seed(42)
    if not os.path.exists(os.path.join("cloud",f"run_{num_run}")):
        os.mkdir(os.path.join("cloud",f"run_{num_run}"))
    speedup_min=config_random_cloud["speedup_min"]
    speedup_max=config_random_cloud["speedup_max"]
    speedup_deviation=config_random_cloud["speedup_dev"]
    nodes_min=config_random_cloud["nodes_min"]
    nodes_max= config_random_cloud["nodes_max"]
    lat_min= config_random_cloud["lat_min"]
    lat_max= config_random_cloud["lat_max"]
    base_decrease=config_random_cloud["base_decrease"]
    num_nodes_in_level = []
    num_leaves_in_level = []
    provider_list = []
    leave_list = []
    predecessor_list = []

    num_opt = 0
    node_list=[]
    for r in range(num_levels):
        if r == 0:
            num_tiny = num_tiny_first
            num_nodes = num_tiny_first+len(provider_name)-1
            node_list.append([[0]])
            num_nodes_in_level.append([num_nodes])
            provider_list.append([provider_name[k] for k in range(num_nodes - num_tiny)] + ["tinyfaas" for k in range(num_tiny)])
            num_leaves_in_level.append([num_tiny])
            leave_list.append([False for k in range(num_nodes - num_tiny)] + [True for k in range(num_tiny)])
            predecessor_list = [[-1]]
            num_opt=0
            curr_node=1

        else:
            node_list.append([])
            num_nodes_in_level.append([])
            num_leaves_in_level.append([])
            provider_list.append([])
            leave_list.append([])
            predecessor_list.append([])
            ind = 0
            for k, num_node in enumerate(num_nodes_in_level[-2]):

                predecessor_list[-1] = predecessor_list[-1] + [k + num_opt for d in range(num_node)]
                node_list[-1] =node_list[-1]+ [d+curr_node for d in range(num_node)]


                for s in range(num_node):
                    value = np.random.randint(nodes_min, nodes_max)
                    num_nodes_in_level[-1].append(value)
                    #print(s)
                    if provider_list[-2][ind] != "tinyfaas":
                        num_leaves_in_level[-1].append(1)
                    else:
                        num_leaves_in_level[-1].append(value)

                    for m in range(num_nodes_in_level[-1][-1]):
                        provider_list[-1].append(provider_list[-2][ind])
                        if m == 0:
                            leave_list[-1].append(True)
                        else:
                            if provider_list[-1][-1] != "tinyfaas":
                                leave_list[-1].append(False)

                            else:
                                leave_list[-1].append(True)
                    ind += 1
                curr_node += num_node
            num_opt+=len(num_nodes_in_level[-2])

    curr_node = 0
    num_leaves_ges=0
    for provider in provider_list[-1]:
        if provider == "tinyfaas":
            num_leaves_ges+=1
    latencies_list=[[]]
    speedup_list=[]
    for k in range(num_levels):

        if k == 0:

            num_leaves = num_leaves_in_level[k][0]
            num_clouds_in_level = 1
            num_nodes = num_nodes_in_level[k][0]  # np.random.randint(3,10)
            L = np.zeros((num_nodes, num_nodes))
            rand_latencies = np.random.uniform(0, 1, (int(num_nodes * (num_nodes - 1) / 2), 1))
            ind = 0

            for r in range(num_nodes):
                for t in range(r, num_nodes):
                    if r != t:
                        L[r, t] = rand_latencies[ind]
                        L[t, r] = rand_latencies[ind]
                        ind += 1

            #predecessor_list = ["None" for k in range(num_nodes)]
            nodes_list = [[k for k in range(num_nodes)]]
            name_list = [["aws"]]
            # curr_node+=num_nodes
            cloud_name = f"requirements_cloud_{k}_{0}.json"
            path = os.path.join(f"cloud/run_{num_run}", cloud_name)
            speedup_list.append([np.random.uniform(speedup_min, speedup_max) for k in range(num_nodes)])
            # var_prob=np.random.choice(0,1,p=[0.2])
            config = {
                "name": f"cloud_{k}_{0}",
                "num_nodes": num_nodes,
                "num_leaves": num_leaves,
                "providers": {
                    "provider_" + str(0): {
                        "name": provider_list[0][0],
                        "leave": leave_list[0][0],
                        "estimated_latency": list(L[0, :]),
                        "max_RAM_curr": np.inf,
                        "speedup":speedup_list[-1][0],
                        "pricing_Storage_Transfer": provider_cost_list[provider_list[0][0]]["pricing_Storage_Transfer"],
                        "pricing_RAM": provider_cost_list[provider_list[0][0]]["pricing_RAM"],  # 2.5e-06,
                        "pricing_data_sent": provider_cost_list[provider_list[0][0]]["pricing_data_sent"],
                    }
                },
            }
            latencies_list[-1].append(list(L[0, :]))
            curr_node += 1
            ram_list = [[np.inf]]
            for s in range(num_nodes - 1):
                #var_prob = np.random.choice(2, 1, p=[0, 1.0])[0]
                name_list[0].append("tinyfaas")
                #if var_prob == 0:
                ram_list[0].append(np.inf)
                #else:
                #    ram_list[0].append(np.random.uniform(2000, 10000))
                config["providers"].update({
                    "provider_" + str(s + 1): {
                        "name": provider_list[0][s + 1],
                        "estimated_latency": list(L[s + 1, :]),  # np.random.uniform(0.01, 0.1),
                        "leave": leave_list[0][s + 1],  # provider_name[var_prob] == "tinyfaas",
                        "max_RAM_curr": ram_list[0][s + 1],
                        "speedup":speedup_list[-1][s+1],
                        "pricing_Storage_Transfer": provider_cost_list[provider_list[0][s+1]]["pricing_Storage_Transfer"],
                        "pricing_RAM": provider_cost_list[provider_list[0][s+1]]["pricing_RAM"],  # 2.5e-06,
                        "pricing_data_sent": provider_cost_list[provider_list[0][s+1]]["pricing_data_sent"],
                    }
                })
                curr_node += 1
                latencies_list[-1].append(list(L[s + 1, :]),)
            with open(path, "w") as f:
                json.dump(config, f, indent=4)

        else:
            num_clouds_in_level = sum(num_nodes_in_level[k - 1])  # len(nodes_list[-1])
            name_list.append([])
            ram_list.append([])
            latencies_list.append([])
            speedup_list.append([])
            curr_node_level = 0
            for m in range(sum(num_nodes_in_level[k - 1])):
                num_leaves = num_leaves_in_level[k][m]
                num_nodes = num_nodes_in_level[k][m]  # np.random.randint(3,10)
                L = np.zeros((num_nodes, num_nodes))
                for r in range(num_nodes):
                    speedup_list[-1].append(speedup_list[-2][m]+np.random.uniform(-speedup_deviation,speedup_deviation))
                rand_latencies = np.random.uniform(lat_min / (base_decrease ** (k)), lat_max / (base_decrease ** (k)),
                                                   (int(num_nodes * (num_nodes - 1) / 2), 1))
                ind = 0
                for r in range(num_nodes):
                    for t in range(r, num_nodes):
                        if r != t:
                            L[r, t] = rand_latencies[ind]
                            L[t, r] = rand_latencies[ind]
                            ind += 1
                # predecessor_list.append([m for k in range(num_nodes)])

                if ram_list[-2][m] == np.inf:
                    ram = [np.inf for k in range(num_nodes)]
                else:

                    ram_sum = ram_list[-2][m]
                    ram = (ram_sum * np.random.dirichlet(np.ones(num_nodes))).tolist()
                ram_list[-1] = ram_list[-1].copy() + ram.copy()
                # name=name_list[-2][m]

                # name_list[-1].append([name for k in range(num_nodes)])
                nodes_list.append([k + curr_node for k in range(num_nodes)])
                # curr_node+=num_nodes
                cloud_name = f"requirements_cloud_{k}_{m}.json"
                path = os.path.join(f"cloud/run_{num_run}", cloud_name)
                config = {
                    "name": f"cloud_{k}_{m}",
                    "num_nodes": num_nodes,
                    "num_leaves": num_leaves,
                    "providers": {
                        "provider_" + str(0): {
                            "name": provider_list[k][curr_node_level],  # name,
                            "leave": leave_list[k][curr_node_level],
                            "estimated_latency": list(L[:, 0]),
                            "speedup":speedup_list[-1][m],
                            "max_RAM_curr": ram[0],
                            "pricing_Storage_Transfer": provider_cost_list[provider_list[k][curr_node_level]]["pricing_Storage_Transfer"]+np.random.uniform(-provider_dev["pricing_Storage_Transfer"],provider_dev["pricing_Storage_Transfer"]),
                            "pricing_RAM": provider_cost_list[provider_list[k][curr_node_level]]["pricing_RAM"]+np.random.uniform(-provider_dev["pricing_RAM"],provider_dev["pricing_RAM"]),  # 2.5e-06,
                            "pricing_data_sent": provider_cost_list[provider_list[k][curr_node_level]]["pricing_data_sent"]+np.random.uniform(-provider_dev["pricing_data_sent"],provider_dev["pricing_data_sent"]),
                        }
                    },
                }
                latencies_list[-1].append(list(L[:, 0]))
                curr_node += 1
                curr_node_level += 1
                for s in range(num_nodes - 1):
                    config["providers"].update({
                        "provider_" + str(s + 1): {
                            "name": provider_list[k][curr_node_level],
                            "estimated_latency": list(L[:, s + 1]),
                            "leave": leave_list[k][curr_node_level],
                            "speedup":speedup_list[-1][m],
                            # name == "tinyfaas" and s+1>=num_nodes-num_leaves,
                            "max_RAM_curr": ram[s + 1],
                            "pricing_Storage_Transfer": provider_cost_list[provider_list[k][curr_node_level]]["pricing_Storage_Transfer"]+np.random.uniform(-provider_dev["pricing_Storage_Transfer"],provider_dev["pricing_Storage_Transfer"]),
                            "pricing_RAM": provider_cost_list[provider_list[k][curr_node_level]]["pricing_RAM"]+np.random.uniform(-provider_dev["pricing_RAM"],provider_dev["pricing_RAM"]),  # 2.5e-06,
                            "pricing_data_sent": provider_cost_list[provider_list[k][curr_node_level]]["pricing_data_sent"]+np.random.uniform(-provider_dev["pricing_data_sent"],provider_dev["pricing_data_sent"])
                        }
                    })
                    curr_node += 1
                    curr_node_level += 1
                    latencies_list[-1].append(list(L[:, s+1]))
                with open(path, "w") as f:
                    json.dump(config, f, indent=4)
    ges_nodes = 0
    for k in range(num_levels):
        for value in num_nodes_in_level[k]:
            ges_nodes += value
    cloud_general_config={}
    cloud_general_config["num_leaves"]=num_leaves_ges
    cloud_general_config["ges_nodes"] = ges_nodes
    cloud_general_config["node_list"] = node_list
    cloud_general_config["predecessor_list"] = predecessor_list
    cloud_general_config["leave_list"] = leave_list
    cloud_general_config["ram_list"]=ram_list
    cloud_general_config["speedup_list"] = speedup_list
    cloud_general_config["provider_list"] = provider_list
    cloud_general_config["latencies_list"] = latencies_list
    cloud_general_config["num_nodes_in_level"] = num_nodes_in_level
    cloud_general_config["num_leaves_in_level"] = num_leaves_in_level
    path_general_config=f"cloud/run_{num_run}/general_config.json"
    with open(path_general_config, "w") as f:
        json.dump(cloud_general_config, f, indent=4)

def generate_full_cloud(config,num_run,provider_cost_list,num_levels):
    path=os.path.join(f"cloud/run_{num_run}", "requirements_cloud_full.json")
    full_config={}
    predecessor_list=config["predecessor_list"]
    num_nodes=sum(config["num_nodes_in_level"][-1])
    full_config["num_nodes"]=num_nodes
    full_config["num_leaves"] = config["num_leaves"]
    full_config["providers"]={}
    ram_list=config["ram_list"][-1]
    speedup_list=config["speedup_list"][-1]
    leave_list=config["leave_list"][-1]
    provider_list=config["provider_list"][-1]
    num_nodes_in_level=config["num_nodes_in_level"]
    curr_len_k=num_nodes_in_level[-1][0]
    curr_k=0
    ind_k=0
    for k in range(len(provider_list)):
        if curr_k==curr_len_k:
            ind_k+=1
            curr_len_k=num_nodes_in_level[-1][ind_k]
            curr_k=0
        full_config["providers"][f"provider_{k}"]={}
        full_config["providers"][f"provider_{k}"]["name"]=provider_list[k]
        full_config["providers"][f"provider_{k}"]["leave"] = (leave_list[k] and (provider_list[k]=="tinyfaas"))
        full_config["providers"][f"provider_{k}"]["max_RAM_curr"] = ram_list[k]
        full_config["providers"][f"provider_{k}"]["speedup"] =  speedup_list[k]
        full_config["providers"][f"provider_{k}"]["pricing_Storage_Transfer"] = provider_cost_list[provider_list[k]]["pricing_Storage_Transfer"]
        full_config["providers"][f"provider_{k}"]["pricing_RAM"] = provider_cost_list[provider_list[k]]["pricing_RAM"]
        full_config["providers"][f"provider_{k}"]["pricing_data_sent"] = provider_cost_list[provider_list[k]]["pricing_data_sent"]
        level_start=[]
        num_opt=0
        for r in range(num_levels):
            level_start.append(num_opt)
            num_opt+=len(predecessor_list[r])

        latencies_list=[]
        curr_len_m = num_nodes_in_level[-1][0]
        curr_m = 0
        ind_m = 0
        for m in range(len(provider_list)):
            if curr_m == curr_len_m:
                ind_m += 1
                curr_len_m = num_nodes_in_level[-1][ind_m]
                curr_m=0
            latency=0
            pred_k=ind_k
            pred_m=ind_m
            if pred_k==pred_m:
                latency=config["latencies_list"][-1][k][curr_m]
            else:
                latency+=config["latencies_list"][-1][m][0]
                latency+=config["latencies_list"][-1][k][0]
                next_ind_k=ind_k
                next_ind_m=ind_m
                pred_k=predecessor_list[-1][ind_k]  - level_start[-2]
                pred_m=predecessor_list[-1][ind_m]  - level_start[-2]

                for r in range(num_levels-1):

                    if pred_k==pred_m:
                        find_m=next_ind_m
                        for num_node in num_nodes_in_level[num_levels-r-2]:
                           find_m=find_m-num_node
                           if find_m<0:
                               find_m+=num_node
                               break
                        latency += config["latencies_list"][num_levels -r - 2][next_ind_k][find_m]
                        break
                    else:
                        next_ind_k=pred_k
                        next_ind_m=pred_m
                        pred_k=predecessor_list[num_levels -r -2][next_ind_k]  - level_start[num_levels - r - 2]
                        pred_m=predecessor_list[num_levels -r -2][next_ind_m]  - level_start[num_levels - r - 2]
                        latency += config["latencies_list"][num_levels - r - 1][next_ind_k][0]
                        latency += config["latencies_list"][num_levels - r - 1][next_ind_m][0]
            curr_m+=1
            latencies_list.append(latency)
        curr_k+=1
        full_config["providers"][f"provider_{k}"]["estimated_latency"]=latencies_list
    with open(path, "w") as f:
        json.dump(full_config, f, indent=4)