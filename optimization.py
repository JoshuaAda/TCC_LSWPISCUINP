from gurobipy import *
import numpy as np
from typing import Any, Dict

#def __init__(self,deployment_cloud: Dict[str, Any],deployment_workflow: Dict[str, Any]):

    #model_list=[ setup_model(0)] #for s in range( num_nodes_tiny+1)]



def solve_opt(deployment_workflow: Dict[str, Any],deployment_cloud: Dict[str, Any]):
    #deployment = deployment_cloud
    workflow_functions = list(deployment_workflow['functions'].keys())
    providers = list(deployment_cloud['providers'].keys())
    num_paths = deployment_workflow['paths']['num_paths']
    num_leaves = deployment_cloud['num_leaves']
    num_workflows = deployment_workflow['deployment_number']
    num_functions = len(deployment_workflow['functions'])
    num_nodes_cloud = 0
    num_nodes_tiny = 0
    for key in deployment_cloud['providers'].keys():
        if deployment_cloud['providers'][key]['name'] != 'tinyfaas':
            num_nodes_cloud += 1
        else:
            num_nodes_tiny += 1
    # num_nodes_cloud = len(deployment_cloud['providers']) - 1

    # num_nodes_tiny = len(deployment_cloud['providers']['tinyFaaS']['nodes'])
    num_nodes = num_nodes_cloud + num_nodes_tiny
    #num_branches = deployment_workflow['num_branches']


    model= Model("FaaS")
    C=np.zeros((num_functions,num_nodes))
    D=np.zeros((num_functions, num_nodes,num_nodes))
    L=np.zeros((num_nodes, num_nodes))
    b=np.zeros((num_paths,num_functions))
    a=np.zeros((num_functions,num_functions))
    S=np.ones((num_functions, num_nodes))
    ram_max=np.ones((num_nodes,1))*1e8
    ram=np.zeros((num_functions,1))
    time=np.zeros((num_functions,1))
    prob_request=np.zeros((num_functions,1))
    D_in=np.zeros((num_nodes,1))
    input_list=deployment_workflow['input_functions']
    m_start=[list(deployment_workflow['functions']).index(func) for func in input_list]
    end_list=deployment_workflow['output_functions']
    m_end=[list(deployment_workflow['functions']).index(func) for func in end_list]
    leave_nodes=[]
    for m in range(num_functions):
        for i in range(num_nodes):
            if deployment_cloud['providers'][f"provider_{i}"]['name']!="tinyfaas":
                S[m,i]=deployment_workflow["functions"][f"function_{m}"]['speedup']
    for r in range(len(deployment_cloud['providers'])):
        if deployment_cloud['providers'][f"provider_{r}"]['leave']:
            leave_nodes.append(r)
    #num_leaves=len(leave_nodes)
    #for m in range(num_functions):
    #    func_name=workflow_functions[m]#deployment_workflow['functions'][m]
    #    list_func=deployment_workflow['workflow_dependencies'][func_name]
    #    indices = [list(deployment_workflow['functions']).index(func) for func in list_func]
    #    a[m,indices]=1
    for s in range(num_paths):
        list_func=deployment_workflow['paths'][str(s)]
        indices= [list(deployment_workflow['functions']).index(f"function_{func}") for func in list_func]
        b[s,indices]=1
        for r in range(len(list_func)-1):
            a[list_func[r],list_func[r+1]]=1
    for i in range(num_nodes):
        if deployment_cloud['providers'][f"provider_{i}"]["name"]=='tinyfaas':
            ram_max[i]=deployment_cloud['providers'][f"provider_{i}"]['max_RAM_curr']

    for j in range( num_functions):
        ram[j] =  deployment_workflow['functions'][ workflow_functions[j]]['ram']
        time[j] =  deployment_workflow['functions'][ workflow_functions[j]]['time']
        #requests =  deployment_workflow['functions'][ workflow_functions[j]]['requests']
        data_dependencies =  deployment_workflow['functions'][ workflow_functions[j]]['data_dependencies']
        prob_request[j]= deployment_workflow['functions'][ workflow_functions[j]]['prob_request']
        data_send = deployment_workflow['functions'][ workflow_functions[j]]['data_send']
        for k in range( num_nodes):
            if deployment_cloud['providers'][f"provider_{k}"]["name"]=='tinyfaas':
                #D[j,k]=0
                D_in[k]=0
            else:
                pricing_data_sent = deployment_cloud['providers'][providers[k]]['pricing_data_sent']
                #D[j,k]=prob_request[j]*data_send*pricing_data_sent
                D_in[k]=deployment_workflow['input_data']*pricing_data_sent
            for m in range(num_nodes):

                    if deployment_cloud['providers'][f"provider_{k}"]["name"]!='tinyfaas':
                        pricing_data_sent = deployment_cloud['providers'][providers[k]][
                        'pricing_data_sent']
                        D[j,k,m]=D[j,k,m]+prob_request[j]*data_send*pricing_data_sent
                    if deployment_cloud['providers'][f"provider_{m}"]["name"]!='tinyfaas':
                        pricing_data_sent = deployment_cloud['providers'][providers[m]][
                        'pricing_data_sent']
                        D[j,k,m]=D[j,k,m]+prob_request[j]*data_send*pricing_data_sent
            for key in data_dependencies.keys():
                value = data_dependencies[key]
                pricing_Storage_Transfer =  deployment_cloud['providers'][key][
                    'pricing_Storage_Transfer']
                if deployment_cloud['providers'][key]["name"]!= "tinyfaas":
            #        D[j,k]=data_send
                    C[j,k]=C[j,k]+pricing_Storage_Transfer*value
            if deployment_cloud['providers'][f"provider_{k}"]["name"]=='tinyfaas':
                C[j,k]=0
            else:
                pricing_RAM =  deployment_cloud['providers'][ providers[k]]['pricing_RAM']
                pricing_StartRequest =  deployment_cloud['providers'][ providers[k]]['pricing_StartRequest']
                C[j,k]=prob_request[j]*pricing_RAM*ram[j]*time[j]#+pricing_StartRequest*requests

    for k in range( num_nodes):
        for m in range( num_nodes):
            L[k,m]= deployment_cloud['providers'][f"provider_{k}"]['estimated_latency'][m]
    #for j in range( num_functions):
    #    for k in range( num_nodes):
    #        if k>= num_nodes_tiny:
    #            C[j,k]=1
    #        if k!=1:
    #            D[j,k]=2
    #for k in range( num_nodes):
    #    for m in range( num_nodes):
    #        if k!=m:
    #            L[k,m]=1
    w_1=1
    w_2=1
    w_3=1
    P=model.addVars( num_functions* num_workflows, num_nodes,vtype=GRB.BINARY, name="P")
    S = model.addVars(num_functions * num_workflows, num_nodes, vtype=GRB.CONTINUOUS, name="S")
    H=model.addVars(num_leaves,num_workflows,vtype=GRB.BINARY, name="H")
    T=model.addVars(num_workflows,lb=0, ub=float('inf'),vtype=GRB.CONTINUOUS, name="T")
    obj=0
    for n in range( num_workflows):
        for k in range( num_leaves):
            for m in range( num_functions):
                for i in range(num_nodes):
                    obj=obj+H[k,n]*(w_1*(P[m+n* num_functions,i]*C[m,i]+S[m+n* num_functions,i])+w_2*T[n])#S[m+n* num_functions,i]*D[m,i]
                    #for m_s in range(num_functions):
                        #for j in range(num_nodes):
                            #obj=obj+H[k,n]*P[m+n*num_functions,i]*P[m_s+n*num_functions,j]*D[m,i]*a[m,m_s]
    for n in range( num_workflows):
        for k in range( num_leaves):
            for i in range(num_nodes):
                for m in m_start:
                    obj=obj+H[k,n]*( P[n*num_functions+m,i]*w_1*D_in[i]+w_2*L[leave_nodes[k],i]*P[n*num_functions+m,i])# P[n*num_functions+m,i]*w_1*D_in[i]
                for m in m_end:
                    obj = obj+H[k,n]*(w_1*D[m,i,k]*P[n*num_functions+m, i]+w_2*L[leave_nodes[k], i] * P[n*num_functions+m, i])
    model.setObjective(obj,GRB.MINIMIZE)
    #T_path=np.zeros((num_workflows,num_paths))
    for n in range( num_workflows):
        for m in range( num_functions):
            model.addConstr(quicksum(P[m+n* num_functions,i] for i in range( num_nodes))==1,"only one placed")
    for k in range( num_leaves):
        model.addConstr(quicksum(H[k,n] for n in range( num_workflows))==1,"only one selected")
    for i in range( num_nodes):
        model.addConstr(quicksum(quicksum(P[n*num_functions+m,i]*prob_request[m]*ram[m] for m in range(num_functions)) for n in range(num_workflows))<= ram_max[i]  , "RAM_constraint")
    for n in range(num_workflows):
        for s in range(num_paths):
            model.addConstr(T[n]>=quicksum(quicksum(quicksum(quicksum(P[n*num_functions+m,i]*P[n*num_functions+m_s,j]*L[i,j]*a[m,m_s]*b[s,m] for m_s in range(num_functions)) for j in range(num_nodes))+P[n*num_functions+m,i]*b[s,m]*S[m,i]*time[m] for m in range(num_functions)) for i in range(num_nodes)),'Time constraint')#quicksum(quicksum(P[n*num_functions+m,i]*P[n*num_functions+m_s,j]*L[i,j]*a[m,m_s] for m_s in range(num_functions)) for j in range(num_nodes))*b[s,m]+

    for n in range(num_workflows):
        for m in range(num_functions):
            for i in range(num_nodes):
                model.addConstr(S[n*num_functions+m,i]==quicksum(quicksum(
                    P[n * num_functions + m, i] * P[n * num_functions + m_s, j] *
                    a[m, m_s]*D[m,i,j] for m_s in
                    range(num_functions)) for j in range(num_nodes)),'Adding aux variable')#
    for m in range(num_functions):
        func_set=deployment_workflow["functions"][f"function_{m}"]["function_set"]
        for n in func_set:
            model.addConstr(P[n*num_functions+m,0]==1,"Already placed workflow functions")
    #if num>0:
    #    model.addConstr(quicksum(P[j,num-1] for j in range( num_functions))==0,"node_0_constr")
    model.setParam('OutputFlag', 1)
    model.update()
    P_list = []
    # for model in  model_list:

    model.optimize()
    P = np.zeros((num_functions * num_workflows, num_nodes))
    S = np.zeros((num_functions * num_workflows, num_nodes))
    H = np.zeros((num_leaves, num_workflows))
    T = np.zeros((num_workflows, 1))
    r = 0
    s = 0
    for index,v in enumerate(model.getVars()):
        if index<num_functions*num_workflows*num_nodes:
            P[s, r] = v.x
            r = r + 1
            if r == num_nodes:
                s = s + 1
                r = 0
            if s == num_functions*num_workflows:
                s=0

        elif index<2*num_functions*num_workflows*num_nodes:
            S[s, r] = v.x
            r = r + 1
            if r == num_nodes:
                s = s + 1
                r = 0
            if s == num_functions*num_workflows:
                s=0
        elif index<2*num_functions*num_workflows*num_nodes+num_leaves*num_workflows:
            H[s, r] = v.x
            r = r + 1
            if r == num_workflows:
                s = s + 1
                r = 0
            if s == num_leaves:
                s=0
        elif index<2*num_functions*num_workflows*num_nodes+num_leaves*num_workflows+num_workflows:
            T[s] = v.x
            s = s + 1

    P_list.append(P)
    print(P)
    #print(S)
    print(H)
    print(T)
    return model,P,H

"""
def deploy_to_cloud(deployment_cloud: Dict[str, Any],deployment_workflow: Dict[str, Any],new_deployment,function_number: int,node_number: int):
    workflow_functions = list(deployment_workflow['functions'].keys())
    providers = list(deployment_cloud['providers'].keys())
    num_functions = len(deployment_workflow['functions'])
    num_nodes_cloud = len(deployment_cloud['providers']) - 1
    num_nodes_tiny = len(deployment_workflow['providers']['tinyFaaS']['nodes'])
    num_nodes = num_nodes_cloud + num_nodes_tiny
    num_configs = 2
    old_deploy = deployment_workflow['functions'].copy()
    func_key= workflow_functions[function_number]
    old_values = old_deploy[func_key]
    if node_number== num_nodes_tiny:
        #old_deploy= deployment['functions'][func_key]
       deploy={
        "handler": "wrapper_aws.wrapper_aws",
        "requirements": "./functions/"+func_key+"/requirements.txt",
        "provider": "AWS",
        "method": "POST",
        "region": "us-east-1",
        "time": old_values["time"],
        "ram": old_values["ram"],
        "requests": old_values["requests"]
        },
    elif node_number== num_nodes_tiny+1:
        #old_deploy =  deployment['functions'][func_key]
        deploy={
        "handler": "wrapper_gcp.wrapper_gcp",
        "requirements": "./functions/"+func_key+"/requirements.txt",
        "provider": "google",
        "method": "POST",
        "region": "us-central1",
        "time": old_values["time"],
        "ram": old_values["ram"],
        "requests": old_values["requests"]
        }
    else:
        assert node_number> num_nodes_tiny+1

    new_deployment['functions'][func_key]=deploy
    return new_deployment
def deploy_to_tinyfaas(new_deployment,old_deploy,function_number: int,node_number: int):
    workflow_functions = list(new_deployment['functions'].keys())
    func_key= workflow_functions[function_number]
    #old_deploy= deployment['functions'][func_key]
    old_values=  old_deploy[func_key]
    deploy={
        "handler": "???",
        "requirements": "???",
        "provider": "tinyFaaS",
        "tinyFaaSOptions": {
            "env": "python3",
            "threads": 1,
            "source": "???",
            "deployTo": [
                {
                    "name": "tf-node-"+str(node_number)
                }
            ]
        },
        "time": old_values["time"],
        "ram": old_values["ram"],
        "requests": old_values["requests"]
    }
    new_deployment['functions'][func_key]=deploy

def create_deployment_configs(deployment_workflow,deployment_cloud,P):
    new_deployment_list=[]
    workflow_functions = list(deployment_workflow['functions'].keys())
    providers = list(deployment_cloud['providers'].keys())
    num_functions = len(deployment_workflow['functions'])
    num_nodes_cloud = len(deployment_cloud['providers']) - 1
    num_nodes_tiny = len(deployment_cloud['providers']['tinyfaas']['nodes'])
    num_nodes = num_nodes_cloud + num_nodes_tiny
    num_configs = 2
    for m in range( num_configs):
        new_deployment= deployment_workflow.copy()
        for j in range( num_functions):
            for k in range( num_nodes):
                if k< num_nodes_tiny and P[j,k]==1:
                    new_deployment= deploy_to_tinyfaas(new_deployment,j,k)
                elif P[j,k]==1:
                    new_deployment= deploy_to_cloud(new_deployment,j,k)
        new_deployment_list.append(new_deployment)
    return new_deployment_list
"""

