import json
import numpy as np
if __name__ == "__main__":
    parameter_config_path="settings/parameters_1.json"
    num_weights=3
    with open(parameter_config_path, "r") as f:
        parameter_general_config = json.load(f)
    nodes=[2+k for k in range(num_weights)]#np.linspace(3,100,num_weights)
    for k in range(num_weights):
        #parameter_general_config["config_random_cloud"]["nodes_min"]=nodes[k]
        #parameter_general_config["config_random_cloud"]["nodes_max"]=nodes[k]+1
        parameter_general_config["num_levels"]=k+2
        parameter_config_path=f"settings/parameters_{k+123}.json"
        with open(parameter_config_path, "w") as f:
            json.dump(parameter_general_config, f, indent=4)