import json
import numpy as np
if __name__ == "__main__":
    parameter_config_path="settings/parameters_1.json"
    num_weights=100
    with open(parameter_config_path, "r") as f:
        parameter_general_config = json.load(f)
    w_1=np.linspace(0,1,num_weights)
    for k in range(num_weights):
        parameter_general_config["w_1"]=w_1[k]
        parameter_general_config["w_2"]=1-w_1[k]
        parameter_config_path=f"settings/parameters_{k+2}.json"
        with open(parameter_config_path, "w") as f:
            json.dump(parameter_general_config, f, indent=4)
