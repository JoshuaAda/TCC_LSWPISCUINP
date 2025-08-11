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

        general_config_path=f"cloud/run_{num_run}/general_config.json"
        with open(general_config_path, "r") as f:
                cloud_general_config = json.load(f)
        num_leaves=cloud_general_config["num_leaves"]
        num_workflows= parameter_general_config["num_workflows"]
        num_levels=parameter_general_config["num_levels"]
        num_other_first_level=len(parameter_general_config["provider_list"])-1
        num_nodes_in_level = cloud_general_config["num_nodes_in_level"]
        num_probs=0



        time_cost_all = 0
        money_cost_all = 0
        w_1 = parameter_general_config["w_1"]
        w_2 = parameter_general_config["w_2"]
        provider_list=cloud_general_config["provider_list"]
        predecessor_list=cloud_general_config["predecessor_list"]
        num_nodes_in_level_list=cloud_general_config["num_nodes_in_level"]
        num_other=len(provider_list[-1])-num_leaves
        for t in range(num_workflows):

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
                for k in range(num_leaves):
                        leave_k=k+num_other
                        ind_r=0
                        num_curr_nodes=0
                        for node_len in num_nodes_in_level_list[-1]:
                            num_curr_nodes+=node_len
                            if num_curr_nodes>leave_k:
                                break
                            ind_r += 1
                        pred_k=ind_r
                        for r in range(num_levels-2):
                                pred_k=predecessor_list[num_levels-r-2][pred_k]
                        pred_k=pred_k-num_other_first_level
                        selected_workflow = H[pred_k].index(1)
                        time_cost=0
                        money_cost=0
                        time_cost+=T[selected_workflow][0]

                        for m in range(num_functions-1):
                                selected_place=P[selected_workflow*num_functions+m].index(1)
                                if m == 0:
                                        time_cost += L[pred_k][selected_place]
                                        money_cost += D_in[selected_place][0]
                                next_selected_place = P[selected_workflow*num_functions+m+1].index(1)
                                money_cost += C[m][selected_place]
                                #time_cost += L[selected_place][next_selected_place]
                                money_cost += S[m+selected_workflow* num_functions][selected_place]
                        selected_place = P[selected_workflow * num_functions + num_functions-1].index(1)
                        money_cost += C[num_functions-1] [selected_place]
                        time_cost += L[selected_place][pred_k]
                        money_cost += S[num_functions-1 + selected_workflow * num_functions] [selected_place]
                        time_cost_all+=time_cost
                        money_cost_all+=money_cost
                num_prob=1


                for r in range(num_levels):
                        curr_node = 0
                        ind = 0
                        num_other_level=
                        for s in range(len(num_nodes_in_level[r])):
                                workflow_path = f"workflows/run_{num_run}/requirements_workflow_{t}_{num_prob}.json"
                                placement_path = f"placement/run_{num_run}/opt_{t}_{num_prob}.json"
                                with open(workflow_path, "r") as f:
                                        workflow_config = json.load(f)
                                with open(placement_path, "r") as f:
                                        placement_config = json.load(f)
                                for k in range(num_leaves):


                                        leave_k = k + num_other
                                        ind_r = 0
                                        num_curr_nodes = 0
                                        for node_len in num_nodes_in_level_list[-1]:
                                                num_curr_nodes += node_len
                                                if num_curr_nodes > leave_k:
                                                        break
                                                ind_r += 1
                                        pred_k = ind_r
                                        for d in range(num_levels - 2-r):
                                                pred_k = predecessor_list[num_levels - d - 2][pred_k]
                                        pred_k = pred_k - num_other_level
                                        selected_workflow = H[pred_k].index(1)
                                        time_cost = 0
                                        money_cost = 0


                                        for m in range(num_functions - 1):
                                                selected_place = P[selected_workflow * num_functions + m].index(1)
                                                if m == 0:
                                                        time_cost += L[pred_k][selected_place]
                                                        money_cost += D_in[selected_place][0]
                                                next_selected_place = P[selected_workflow * num_functions + m + 1].index(1)
                                                money_cost += C[m][selected_place]
                                                time_cost += L[selected_place][next_selected_place]
                                                money_cost += S[m + selected_workflow * num_functions][selected_place]
                                        selected_place = P[selected_workflow * num_functions + num_functions - 1].index(1)
                                        money_cost += C[num_functions - 1][selected_place]
                                        time_cost += L[selected_place][pred_k]
                                        money_cost += S[num_functions - 1 + selected_workflow * num_functions][selected_place]
                                        time_cost_all += time_cost
                                        money_cost_all += money_cost
                                num_prob+=1

        overall_cost = w_1 * time_cost_all + w_2 * money_cost_all
        print(overall_cost)
        results_path = f"results/run_{num_run}/results.json"
        if not os.path.exists(os.path.join("results",f"run_{num_run}")):
                os.mkdir(os.path.join("results",f"run_{num_run}"))
        results={}
        results['overall_cost']=overall_cost
        results['money_cost']=money_cost_all
        results['time_cost']=time_cost_all
        with open(results_path, "w") as f:
                json.dump(results, f, indent=4)
