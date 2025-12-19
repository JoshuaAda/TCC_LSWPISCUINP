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
                                func_nums=np.where(np.array(b[s])==1)[0].tolist()

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
                                                        pricing_RAM=curr_cloud['providers'][f"provider_{selected_place}"]['pricing_RAM']
                                                        #pricing_Storage_Transfer=curr_cloud['providers'][f"provider_{selected_place}"]['pricing_Storage_Transfer']
                                                        C_func[m] += pricing_RAM*ram*time#speedup
                                                        k_curr=get_leaf(selected_place,opt_num)
                                                        placement_func[m,k_curr]=1
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
                        for k in range(num_nodes_all):
                                placement_overall+=sum(placement_func[:,k])**2
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
                        time_cost_all+=time_cost
                        money_cost_all+=money_cost
                select_cost=np.sum(workflow_overall**2)+np.sum(invocations**2)#+placement_overall##+np.sum(placement_overall**2)#num_prob=1
                #print(select_cost)
                select_cost_all+=select_cost

        overall_cost = w_1 * money_cost_all+ w_2 * time_cost_all+w_3*select_cost_all
        #print(select_cost_all)
        print(overall_cost)
        results_path = f"results/run_{num_run}/results.json"
        if not os.path.exists(os.path.join("results",f"run_{num_run}")):
                os.mkdir(os.path.join("results",f"run_{num_run}"))
        results={}
        results['overall_cost']=overall_cost
        results['money_cost']=money_cost_all
        results['select_cost'] = select_cost_all
        results['time_cost']=time_cost_all

        if comparison:
                time_cost_all=0
                money_cost_all=0
                select_cost_all=0
                time_cost=0
                money_cost=0

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
                        #for k in range(num_leaves):
                        #        for m in range(num_deployment):
                                        #for i in range(num_nodes):
                                         #       select_cost += (H[k][n]*sum([P[num_functions*n+m][i] for m in range(num_functions)])) ** 2
                        for n in range(num_deployment):
                                select_cost += sum([H[k][n] for k in range(num_leaves)]) ** 2
                                print(select_cost)
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
                                        func_nums = np.where(np.array(b[s]) == 1)[0].tolist()

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

                                time_cost_all += time_cost
                                money_cost_all += money_cost
                        select_cost_all += select_cost
                        select_cost_all+=np.sum(invocations**2)
                overall_cost = w_1 * money_cost_all+w_2 * time_cost_all+w_3*select_cost_all
                print(overall_cost)
                results['overall_cost_comparison'] = overall_cost[0]

        with open(results_path, "w") as f:
                json.dump(results, f, indent=4)