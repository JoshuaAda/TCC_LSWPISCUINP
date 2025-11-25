import json
import numpy as np
if __name__ == "__main__":
    parameter_config_path="settings/parameters_1.json"
    num_weights=10
    weights=[]
    for i in range(num_weights + 1):
        for j in range(num_weights + 1 - i):
            w1 = i / num_weights
            w2 = j / num_weights
            w3 = (1 - w1 - w2)*100
            weights.append([w1, w2, w3])

    num_weights=100
    with open(parameter_config_path, "r") as f:
        parameter_general_config = json.load(f)
    w_1=np.linspace(0,1,num_weights)
    for k in range(num_weights):
        parameter_general_config["w_1"]=w_1[k]#weights[k][0]
        parameter_general_config["w_2"]=1-w_1[k]#w_1[k]#weights[k][1]
        parameter_general_config["w_3"] = 0#1-w_1[k]#weights[k][2]
        parameter_config_path=f"settings/parameters_{k+2}.json"
        with open(parameter_config_path, "w") as f:
            json.dump(parameter_general_config, f, indent=4)
