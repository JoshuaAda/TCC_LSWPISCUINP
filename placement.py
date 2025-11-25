import argparse
import os.path
from cloud_workflow_setup import *
from optimization import *
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script that adds 3 numbers from CMD"
    )
    parser.add_argument("--num_run", required=True, type=int)
    args = parser.parse_args()
    num_run=args.num_run

    parameter_config_path=f"settings/parameters_{num_run}.json"
    with open(parameter_config_path, "r") as f:
        parameter_general_config = json.load(f)
    seed= parameter_general_config["seed"]
    w_1=parameter_general_config["w_1"]
    w_2=parameter_general_config["w_2"]
    w_3=parameter_general_config["w_3"]
    num_levels=parameter_general_config["num_levels"]
    num_workflows=parameter_general_config["num_workflows"]
    provider_list=parameter_general_config["provider_list"]#["aws","tinyfaas"]
    num_tiny_first=parameter_general_config["num_tiny_first"]
    comparison=parameter_general_config["comparison"]
    provider_cost_list=parameter_general_config["provider_cost_list"]
    provider_dev=parameter_general_config["provider_cost_deviation"]
    comparison_gap=parameter_general_config["comparison_gap"]
    config_random_workflows=parameter_general_config["config_random_workflows"]
    config_random_cloud=parameter_general_config["config_random_cloud"]
    generate_cloud(num_levels,num_run=num_run,provider_name=provider_list,provider_dev=provider_dev,num_tiny_first=num_tiny_first,provider_cost_list=provider_cost_list,config_random_cloud=config_random_cloud,seed=seed)
    general_config_path = f"cloud/run_{num_run}/general_config.json"
    with open(general_config_path, "r") as f:
        cloud_general_config = json.load(f)

    ges_nodes=cloud_general_config["ges_nodes"]
    num_nodes_in_level=cloud_general_config["num_nodes_in_level"]
    predecessor_list=cloud_general_config["predecessor_list"]
    num_leaves_ges=cloud_general_config["num_leaves"]
    result_dict={}
    time_list=[]
    workflow_name_list=generate_random_workflows(num_workflows=num_workflows,config_random_workflows=config_random_workflows,provider_name=provider_list, num_opts=ges_nodes,num_run=num_run,seed=seed)
    # load the deployment configuration
    t1=time.time()
    for d,workflow_name in enumerate(workflow_name_list):
        #P_list = []
        num_prob = 0

        for k in range(num_levels):
            curr_node=0
            ind=0
            for s in range(len(num_nodes_in_level[k])):
                curr_leave_k = -1
                if ind==num_nodes_in_level[k-1][curr_node]:
                    ind=0
                    curr_node+=1
                cloud_name = f"requirements_cloud_{k}_{s}.json"
                sol_name=f"opt_{d}"
                if not os.path.exists(os.path.join("placement", f"run_{num_run}")):
                    os.mkdir(os.path.join("placement", f"run_{num_run}"))

                path_cloud = os.path.join(f"cloud/run_{num_run}", cloud_name)
                path_workflow = os.path.join(f"workflows/run_{num_run}", workflow_name+"_"+str(num_prob)+".json")
                path_solution = os.path.join(f"placement/run_{num_run}", sol_name+"_"+str(num_prob)+".json")

                with open(path_cloud, "r") as f:
                    requirements_cloud_config = json.load(f)
                with open(path_workflow, "r") as f:#requirements_workflow_0.json
                    requirements_workflow_config = json.load(f)

                if k>0:
                    path_predecessor = os.path.join(f"placement/run_{num_run}", sol_name + "_" + str(predecessor_list[k][s]) + ".json")
                    with open(path_workflow, "r") as f:  # requirements_workflow_0.json
                        requirements_workflow_config = json.load(f)
                    with open(path_predecessor, "r") as f:  # requirements_workflow_0.json
                        solution = json.load(f)
                    if requirements_cloud_config["providers"]["provider_0"]["name"]=="tinyfaas":
                        curr_leave_k+=1
                    requirements_workflow_config=update_requirements_config(requirements_workflow_config,np.array(solution['P']),np.array(solution['H']),ind,curr_leave_k,requirements_cloud_config["num_nodes"],seed=seed)#P_list[predecessor_list[k][s]]
                    with open(path_workflow, "w") as f:
                        json.dump(requirements_workflow_config, f, indent=4)
                model,P,H,L,T,C,D,D_in,Time,a,b,Speed,S=solve_opt(requirements_workflow_config,requirements_cloud_config,gap=0,w_1=w_1,w_2=w_2,w_3=w_3,provider_name_list=provider_list,provider_cost_list=provider_cost_list)
                solution=dict()
                solution['P']=P.tolist()
                solution['H']=H.tolist()
                solution['L'] = L.tolist()
                solution['T'] = T.tolist()
                solution['C'] = C.tolist()
                solution['D'] = D.tolist()
                solution['D_in'] = D_in.tolist()
                solution['time'] = Time.tolist()
                solution['a'] = a.tolist()
                solution['b'] = b.tolist()
                solution['Speed'] = Speed.tolist()
                solution['S']=S.tolist()
                with open(path_solution, "w") as f:
                    json.dump(solution, f, indent=4)
                #P_list.append(P)
                num_prob += 1
                ind+=1

                requirements_cloud_config=update_cloud_config(requirements_cloud_config,requirements_workflow_config,P)
                with open(path_cloud, "w") as f:
                    json.dump(requirements_cloud_config, f, indent=4)
    t2=time.time()
    overall_time = [t2 - t1]
    if comparison:
        heuristic=parameter_general_config["heuristic"]

        generate_full_cloud(cloud_general_config,num_run,provider_cost_list,num_levels)
        t1 = time.time()
        for s,workflow_name in enumerate(workflow_name_list):
            cloud_name = f"requirements_cloud_full.json"
            sol_name = f"opt_{s}"
            path_cloud = os.path.join(f"cloud/run_{num_run}", cloud_name)
            path_workflow = os.path.join(f"workflows/run_{num_run}", workflow_name + "_0.json")
            path_solution = os.path.join(f"placement/run_{num_run}", sol_name + "_full.json")

            with open(path_cloud, "r") as f:
                requirements_cloud_config = json.load(f)
            with open(path_workflow, "r") as f:  # requirements_workflow_0.json
                requirements_workflow_config = json.load(f)

            model,P,H,L,T,C,D,D_in,Time,a,b,Speed,S = solve_opt(requirements_workflow_config, requirements_cloud_config,comparison_gap,w_1,w_2,w_3,provider_list,provider_cost_list,heuristic)
            solution = dict()
            solution['P'] = P.tolist()
            solution['H'] = H.tolist()
            solution['L'] = L.tolist()
            solution['T'] = T.tolist()
            solution['C'] = C.tolist()
            solution['D'] = D.tolist()
            solution['D_in'] = D_in.tolist()
            solution['time'] = Time.tolist()
            solution['a'] = a.tolist()
            solution['b'] = b.tolist()
            solution['Speed'] = Speed.tolist()
            solution['S'] = S.tolist()
            with open(path_solution, "w") as f:
                json.dump(solution, f, indent=4)
        t2=time.time()
        comparison_time=[t2-t1]
    result_dict["time_list"]=time_list
    result_dict["overall_time"]=overall_time
    if comparison:
        result_dict["comparison_time"] = comparison_time
    if not os.path.exists(os.path.join("results", f"run_{num_run}")):
        os.mkdir(os.path.join("results", f"run_{num_run}"))
    results_path = f"results/run_{num_run}/time.json"
    with open(results_path, "w") as f:
        json.dump(result_dict,f, indent=4)
        #new_deployment_list=create_deployment_configs(requirements_workflow_config,requirements_cloud_config)
        #deployment_config=optimizer.deployment
        #for k,deployment_config in enumerate(new_deployment_list):
        #    with open(os.path.abspath("deployment_workflow_"+str(k)+".json"), "w") as f:
        #        json.dump(deployment_config, f,indent=4)
        #    # create the choreography/pre-fetching code to the functions and deploy them
        #    deployer.setup.createDeployment(deployment_config, functions_src, functions_dst)
        #    #deployer.setup.deploy(functions_dst)

        #    # create a workflow bucket that will be used to pass arguments around during the workflows
        #    s3 = boto3.client(
        #        aws_access_key_id=deployment_config["credentials"]["aws"]["aws_access_key_id"],
        #        aws_secret_access_key=deployment_config["credentials"]["aws"]["aws_secret_access_key"],
        #        service_name="s3"
        #    )
        #    deployer.setup.createBucket(s3, deployment_config["workflowBucketName"])

'''
import json
import os.path

import boto3
from optimization import *#optimization
import deployer.setup

if __name__ == "__main__":
    # load the deployment configuration
    with open(os.path.abspath("requirements_cloud_0.json"), "r") as f:
        requirements_cloud_config = json.load(f)
    with open(os.path.abspath("requirements_workflow_0.json"), "r") as f:
        requirements_workflow_config = json.load(f)
    # directories with function/deployment code
    functions_src = os.path.abspath("functions")
    functions_dst = os.path.abspath("deployment")
    model,P=setup_model(requirements_workflow_config,requirements_cloud_config)
    new_deployment_list=create_deployment_configs(requirements_workflow_config,requirements_cloud_config,P)
    #deployment_config=optimizer.deployment
    for k,deployment_config in enumerate(new_deployment_list):
        with open(os.path.abspath("deployment_workflow_"+str(k)+".json"), "w") as f:
            json.dump(deployment_config, f,indent=4)
        # create the choreography/pre-fetching code to the functions and deploy them
        deployer.setup.createDeployment(deployment_config, functions_src, functions_dst)
        #deployer.setup.deploy(functions_dst)

        # create a workflow bucket that will be used to pass arguments around during the workflows
        s3 = boto3.client(
            aws_access_key_id=deployment_config["credentials"]["aws"]["aws_access_key_id"],
            aws_secret_access_key=deployment_config["credentials"]["aws"]["aws_secret_access_key"],
            service_name="s3"
        )
        deployer.setup.createBucket(s3, deployment_config["workflowBucketName"])
'''