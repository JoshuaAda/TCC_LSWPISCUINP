import json
import numpy as np
if __name__ == "__main__":
    parameter_config_path="settings/parameters_1.json"
    weights_config_path="settings/weights_2.json"
    num_weights=10
    weights=[]
    for i in range(num_weights + 1):
        for j in range(num_weights + 1 - i):
            w1 = i / num_weights
            w2 = j / num_weights
            w3 = (1 - w1 - w2)
            weights.append([w1, w2, w3])

    num_weights_util=11
    num_weights=11
    with open(parameter_config_path, "r") as f:
        parameter_general_config = json.load(f)
    w_3=np.linspace(0,10,num_weights_util)+0.0001
    w_1 = np.linspace(0, 1, num_weights)+0.0001
    w_2 = (1.0001-w_1)+0.0001
    for k in range(len(w_3)):
        for m in range(len(w_2)):
            parameter_general_config["w_1"]=w_1[m]
            parameter_general_config["w_2"]=w_2[m]
            parameter_general_config["w_3"] = w_3[k]
            parameter_config_path=f"settings/parameters_{k*num_weights_util+m+2}.json"
            with open(parameter_config_path, "w") as f:
                json.dump(parameter_general_config, f, indent=4)
    with open(weights_config_path, "w") as f:
        json.dump(weights, f, indent=4)