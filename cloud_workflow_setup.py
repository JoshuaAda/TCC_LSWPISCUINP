import numpy as np
import json
import networkx as nx
import os
def update_cloud_config(requirements_cloud_config, requirements_workflow_config, P):
    num_functions = requirements_workflow_config["num_functions"]
    for i in range(P.shape[1]):
        ram_add = 0
        for k in range(P.shape[0]):
            m = int(k % num_functions)
            ram_add += P[k, i] * requirements_workflow_config["functions"][f"function_{m}"]["ram"] * \
                       requirements_workflow_config["functions"][f"function_{m}"]["prob_request"]
        requirements_cloud_config["providers"][f"provider_{i}"]["max_ram_curr"] = \
        requirements_cloud_config["providers"][f"provider_{i}"]["max_RAM_curr"] - ram_add
    return requirements_cloud_config


def update_requirements_config(requirements_workflow_config, P, current_node, num_nodes):
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
            provider = np.random.randint(num_nodes)
            value = requirements_workflow_config["functions"][f"function_{m}"]["data_dependencies"][key]
            requirements_workflow_config["functions"][f"function_{m}"]["data_dependencies"][
                f"provider_{provider}"] = value
    requirements_workflow_config["deployment_number"] = num_workflows
    return requirements_workflow_config


def generate_connected_graph_with_paths(n_nodes, n_parallel_paths=2, seed=None):
    # assert n_nodes >= 4, "Need at least 4 nodes to have interesting parallel paths"

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


def generate_random_workflows(num_workflows, num_opts=4, num_nodes=3):
    data_dependecies_list = ['None', 0]
    workflow_name_list = []
    for i in range(num_workflows):
        workflow_name = f"requirements_workflow_{i}"
        workflow_name_list.append(workflow_name)
        config = dict()
        config["deployment_number"] = np.random.randint(1, 10)
        num_functions = np.random.randint(3, 10)
        config["num_functions"] = num_functions
        config["num_requests"] = {}
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
        config["input_data"] = np.random.uniform(0, 100)
        config["input_functions"] = ["function_0"]
        config["output_functions"] = [f"function_{num_functions - 1}"]
        for m in range(len(paths)):
            config["paths"].update({str(m): paths[m]})

        for k in range(num_functions):
            string = f"provider_{data_dependecies_list[np.random.choice(2, 1, p=[0.8, 0.2])[0]]}"
            if string == f"provider_None":
                config["functions"][f"function_{k}"] = {
                    "name": f"function_{k}",
                    "time": np.random.uniform(0.1, 1.0),
                    "speedup": np.random.uniform(0.1, 1),
                    "ram": np.random.uniform(0.1, 1.0),
                    "prob_request": np.random.uniform(0.01, 0.99),
                    "data_send": np.random.uniform(1, 100),
                    "data_dependencies": {},  # np.random.uniform(1,3)
                    "function_set": {}
                }
            else:
                config["functions"][f"function_{k}"] = {
                    "name": f"function_{k}",
                    "time": np.random.uniform(0.1, 1.0),
                    "speedup": np.random.uniform(0.1, 1),
                    "ram": np.random.uniform(0.1, 1.0),
                    "prob_request": np.random.uniform(0.01, 0.99),
                    "data_send": np.random.uniform(1, 100),
                    "data_dependencies": {string: np.random.uniform(0, 10000)},  # np.random.uniform(1,3)
                    "function_set": {}
                }

        for k in range(num_opts):
            path = os.path.join("workflows", f"requirements_workflow_{i}_{k}.json")
            with open(path, "w") as f:
                json.dump(config, f, indent=4)
    return workflow_name_list


def generate_cloud(num_levels=2, num_nodes_in_level=[[3], [3, 3, 3]], num_leaves_in_level=[[2], [1, 2, 2]],
                   provider_name=["aws", "tinyfaas"], leave_list=[], provider_list=[], decentralized=True):
    if decentralized:
        curr_node = 0
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

                predecessor_list = ["None" for k in range(num_nodes)]
                nodes_list = [[k for k in range(num_nodes)]]
                name_list = [["aws"]]
                # curr_node+=num_nodes
                cloud_name = f"requirements_cloud_{k}_{0}.json"
                path = os.path.join("cloud", cloud_name)
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
                            "pricing_Storage_Transfer": 0,
                            "max_RAM_curr": np.inf,
                            "pricing_RAM": 5,  # 2.5e-06,
                            "pricing_data_sent": 0.01,
                            "pricing_StartRequest": 4e-07,
                        }
                    },
                }
                curr_node += 1
                ram_list = [[np.inf]]
                for s in range(num_nodes - 1):
                    var_prob = np.random.choice(2, 1, p=[0, 1.0])[0]
                    name_list[0].append(provider_name[var_prob])
                    if var_prob == 0:
                        ram_list[0].append(np.inf)
                    else:
                        ram_list[0].append(np.random.uniform(2000, 10000))
                    config["providers"].update({
                        "provider_" + str(s + 1): {
                            "name": provider_list[0][s + 1],
                            "estimated_latency": list(L[s + 1, :]),  # np.random.uniform(0.01, 0.1),
                            "leave": leave_list[0][s + 1],  # provider_name[var_prob] == "tinyfaas",
                            "pricing_Storage_Transfer": 0,
                            "max_RAM_curr": ram_list[0][s + 1],
                            "pricing_RAM": 0.01667,  # 2.5e-06,
                            "pricing_data_sent": 0.01,
                            "pricing_StartRequest": 4e-07,
                        }
                    })
                    curr_node += 1
                with open(path, "w") as f:
                    json.dump(config, f, indent=4)

            else:
                num_clouds_in_level = sum(num_nodes_in_level[k - 1])  # len(nodes_list[-1])
                name_list.append([])
                ram_list.append([])
                curr_node_level = 0
                for m in range(sum(num_nodes_in_level[k - 1])):
                    num_leaves = num_leaves_in_level[k][m]
                    num_nodes = num_nodes_in_level[k][m]  # np.random.randint(3,10)
                    L = np.zeros((num_nodes, num_nodes))
                    rand_latencies = np.random.uniform(10 / (10 ** (k)), 1000 / (10 ** (k)),
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
                    path = os.path.join("cloud", cloud_name)
                    config = {
                        "name": f"cloud_{k}_{m}",
                        "num_nodes": num_nodes,
                        "num_leaves": num_leaves,
                        "providers": {
                            "provider_" + str(0): {
                                "name": provider_list[k][curr_node_level],  # name,
                                "leave": leave_list[k][curr_node_level],
                                "estimated_latency": list(L[:, 0]),
                                "pricing_Storage_Transfer": 0,
                                "max_RAM_curr": ram[0],
                                "pricing_RAM": 0.01667,  # 2.5e-06,
                                "pricing_data_sent": 0.01,
                                "pricing_StartRequest": 4e-07,
                            }
                        },
                    }
                    curr_node += 1
                    curr_node_level += 1
                    for s in range(num_nodes - 1):
                        config["providers"].update({
                            "provider_" + str(s + 1): {
                                "name": provider_list[k][curr_node_level],
                                "estimated_latency": list(L[:, s + 1]),
                                "leave": leave_list[k][curr_node_level],
                                # name == "tinyfaas" and s+1>=num_nodes-num_leaves,
                                "pricing_Storage_Transfer": 0,
                                "max_RAM_curr": ram[s + 1],
                                "pricing_RAM": 0.01667,  # 2.5e-06,
                                "pricing_data_sent": 0.01,
                                "pricing_StartRequest": 4e-07,
                            }
                        })
                        curr_node += 1
                        curr_node_level += 1
                    with open(path, "w") as f:
                        json.dump(config, f, indent=4)

