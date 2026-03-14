from gurobipy import *
import numpy as np
from typing import Any, Dict
import time


def solve_opt(deployment_workflow: Dict[str, Any],deployment_cloud: Dict[str, Any], gap=0,w_1=1,w_2=1,w_3=1,provider_name_list=[],provider_cost_list=[],heuristic=False):

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
    num_nodes = num_nodes_cloud + num_nodes_tiny
 


    model= Model("FaaS")
    if gap>0:
        model.setParam('MIPGap', gap)
    C=np.zeros((num_functions,num_nodes))
    D=np.zeros((num_functions, num_nodes,num_nodes))
    L=np.zeros((num_nodes, num_nodes))
    b=np.zeros((num_paths,num_functions))
    a=np.zeros((num_functions,num_functions))
    Speed=np.ones((num_functions, num_nodes))
    ram_max=np.ones((num_nodes,1))*1e8
    request=np.zeros((num_nodes,1))
    ram=np.zeros((num_functions,1))
    Time=np.zeros((num_functions,1))
    #prob_request=np.zeros((num_functions,1))
    D_in=np.zeros((num_nodes,1))
    input_list=deployment_workflow['input_functions']
    m_start=[list(deployment_workflow['functions']).index(func) for func in input_list]
    end_list=deployment_workflow['output_functions']
    m_end=[list(deployment_workflow['functions']).index(func) for func in end_list]
    leave_nodes=[]
    for m in range(num_functions):
        for i in range(num_nodes):
            if deployment_cloud['providers'][f"provider_{i}"]['name']!="tinyfaas":
                Speed[m,i]=deployment_workflow["functions"][f"function_{m}"]['speedup']#+deployment_cloud["providers"][f"provider_{i}"]['speedup']
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
    for k in range(num_leaves):
        request[k]=deployment_cloud['providers'][f"provider_{leave_nodes[k]}"]["request_rate"]
    for j in range( num_functions):
        ram[j] =  deployment_workflow['functions'][ workflow_functions[j]]['ram']
        Time[j] =  deployment_workflow['functions'][ workflow_functions[j]]['time']
        #requests =  deployment_workflow['functions'][ workflow_functions[j]]['requests']
        data_dependencies =  deployment_workflow['functions'][ workflow_functions[j]]['data_dependencies']
        #prob_request[j]= deployment_workflow['functions'][ workflow_functions[j]]['prob_request']
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

                    if deployment_cloud['providers'][f"provider_{k}"]["name"]!=deployment_cloud['providers'][f"provider_{m}"]["name"]:
                        if deployment_cloud['providers'][f"provider_{k}"]["name"]!='tinyfaas':
                            pricing_data_sent = deployment_cloud['providers'][providers[k]][
                            'pricing_data_sent']
                            D[j,k,m]=D[j,k,m]+data_send*pricing_data_sent# *prob_request[j]
                        if deployment_cloud['providers'][f"provider_{m}"]["name"]!='tinyfaas':
                            pricing_data_sent = deployment_cloud['providers'][providers[m]][
                            'pricing_data_sent']
                            D[j,k,m]=D[j,k,m]+data_send*pricing_data_sent #*prob_request[j]
            for key in data_dependencies.keys():
                value = data_dependencies[key]
                #provider_name=provider_name_list[int(key[9:])]
                pricing_Storage_Transfer =  provider_cost_list[key]["pricing_Storage_Transfer"]#deployment_cloud['providers'][key][
                    #'pricing_Storage_Transfer']
                if key!=  deployment_cloud["providers"][providers[k]]["name"]:
            #        D[j,k]=data_send
                    C[j,k]=C[j,k]+pricing_Storage_Transfer*value
            if deployment_cloud['providers'][f"provider_{k}"]["name"]=='tinyfaas':
                C[j,k]+=0
            else:
                pricing_RAM =  deployment_cloud['providers'][ providers[k]]['pricing_RAM']
                #pricing_StartRequest =  deployment_cloud['providers'][ providers[k]]['pricing_StartRequest']
                C[j,k]+=pricing_RAM*ram[j]*Time[j]#Speed#prob_request[j]*#+pricing_StartRequest*requests

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
    #w_1=1
    #w_2=1
    #w_3=1
    if heuristic:
        t1=time.time()
        P_list = []
        # for model in  model_list:

        P = np.zeros((num_functions * num_workflows, num_nodes))
        S = np.zeros((num_functions * num_workflows, num_nodes))
        H = np.zeros((num_leaves, num_workflows))
        T = np.zeros((num_workflows, 1))
        M=np.zeros((num_nodes,1))
        p = np.zeros((num_workflows,num_functions))

        for l in range(len(P)):
            P[l,0]=1
        for l in range(len(H)):
            H[l,0]=1
        t2=time.time()
        t=t2-t1

    else:
        P=model.addVars( num_functions* num_workflows, num_nodes,vtype=GRB.BINARY, name="P")
        S = model.addVars(num_functions * num_workflows, num_nodes, vtype=GRB.CONTINUOUS, name="S")
        H=model.addVars(num_leaves,num_workflows,vtype=GRB.BINARY, name="H")
        T=model.addVars(num_workflows,lb=0, ub=float('inf'),vtype=GRB.CONTINUOUS, name="T")
        M = model.addVars(num_nodes, vtype=GRB.CONTINUOUS, name="M")
        p = model.addVars(num_functions*num_workflows,vtype=GRB.CONTINUOUS,name="p")
        obj=0
        for n in range( num_workflows):
            for k in range( num_leaves):
                obj=obj+request[k][0]*H[k,n]*w_2*T[n]
                for m in range( num_functions):
                    for i in range(num_nodes):
                        obj=obj+request[k][0]*H[k,n]*(w_1*(P[m+n* num_functions,i]*C[m,i]+S[m+n* num_functions,i]))#S[m+n* num_functions,i]*D[m,i]
                        #for m_s in range(num_functions):
                            #for j in range(num_nodes):
                                #obj=obj+H[k,n]*P[m+n*num_functions,i]*P[m_s+n*num_functions,j]*D[m,i]*a[m,m_s]
        already_placed=np.zeros((num_workflows,num_functions))
        for m in range(num_functions):
            func_set=deployment_workflow["functions"][f"function_{m}"]["function_set"]
            for n in func_set:
                model.addConstr(P[n*num_functions+m,0]==1,"Already placed workflow functions")
                already_placed[n,m]+=1
        for n in range( num_workflows):
            for k in range( num_leaves):
                for i in range(num_nodes):
                    for m in m_start:
                        obj=obj+request[k][0]*H[k,n]*( P[n*num_functions+m,i]*w_1*D_in[i]+w_2*L[leave_nodes[k],i]*P[n*num_functions+m,i])# P[n*num_functions+m,i]*w_1*D_in[i]
                    for m in m_end:
                        obj= obj+request[k][0]*H[k,n]*(w_1*D[m,i,k]*P[n*num_functions+m, i]+w_2*L[leave_nodes[k], i] * P[n*num_functions+m, i])


        for n in range(num_workflows):
            for m in range(num_functions):
                model.addConstr(p[n*num_functions+m]==quicksum(quicksum(request[k][0]*H[k,n]*P[n*num_functions,i]*Time[m]*Speed[m][i] for k in range(num_leaves)) for i in range(num_nodes)))
                obj+=w_3*p[n*num_functions+m]**2
        for i in range(num_nodes):
            curr_util=deployment_cloud["providers"][f"provider_{i}"]["utilization"]

            if i ==0:
                model.addConstr(M[i] == (quicksum(quicksum(request[k][0]*H[k,n]*(quicksum(P[n * num_functions + m, i]*Time[m]*ram[m] for m in range(num_functions))-sum([already_placed[n,m]*Time[m]*ram[m] for m in range(num_functions)])) for k in range(num_leaves)) for n in range(num_workflows)))/ram_max[i]+curr_util,
                                "Aux cons")
            else:
                model.addConstr(M[i] == (quicksum(quicksum(
                    quicksum(request[k][0]*H[k, n] * P[n * num_functions + m, i]*Time[m]*ram[m] for m in range(num_functions)) for k in
                    range(num_leaves)) for n in range(num_workflows)))/ram_max[i]+curr_util,
                                "Aux cons")
            obj+=w_3*M[i]**2#quicksum(H[r,n]*M[i,n] for r in range(num_leaves))
        #for k in range(num_nodes):
        #    obj+=w_3*quicksum(quicksum(P[n*num_functions+m,k] for m in range(num_functions)) for n in range(num_workflows))**2
        #for n in range(num_workflows):
        #    obj+=w_3*quicksum(H[k,n] for k in range(num_leaves))**2
        model.setObjective(obj,GRB.MINIMIZE)
        #T_path=np.zeros((num_workflows,num_paths))
        for n in range( num_workflows):
            for m in range( num_functions):
                model.addConstr(quicksum(P[m+n* num_functions,i] for i in range( num_nodes))==1,"only one placed")

        if deployment_workflow["selection_list"]!={}:
            #if deployment_workflow["selection_list"] != [-1]:
            #    for k in range(num_leaves-1):
            #        for n in range(num_workflows):
            #            model.addConstr(H[k+1,n]==deployment_workflow["selection_list"][n])
            #model.addConstr(quicksum(H[0,n] for n in range(num_workflows))==num_workflows)
            for n in  deployment_workflow["selection_list"]:
                for k in range(num_leaves):
                    model.addConstr(H[k,n]==1)
        else:
            for k in range(num_leaves):
                model.addConstr(quicksum(H[k, n] for n in range(num_workflows)) == 1, "only one selected")
        #for n in range( num_workflows):
        #    model.addConstr(quicksum(H[k,n] for k in range( num_leaves))>=1,"place differently")
        #for i in range( num_nodes):
        #    model.addConstr(quicksum(quicksum(P[n*num_functions+m,i]*ram[m] for m in range(num_functions)) for n in range(num_workflows))<= ram_max[i] #*prob_request , "RAM_constraint")
        for n in range(num_workflows):
            for s in range(num_paths):
                model.addConstr(T[n]>=quicksum(quicksum(quicksum(quicksum(P[n*num_functions+m,i]*P[n*num_functions+m_s,j]*L[i,j]*a[m,m_s]*b[s,m] for m_s in range(num_functions)) for j in range(num_nodes))+P[n*num_functions+m,i]*b[s,m]*Speed[m,i]*Time[m] for m in range(num_functions)) for i in range(num_nodes)),'Time constraint')#=quicksum(quicksum(L[leave_nodes[k],i]*P[n*num_functions+m,i] for k in range(num_leaves)) for m in m_start)+quicksum(quicksum(L[leave_nodes[k],i]*P[n*num_functions+m,i] for k in range(num_leaves)) for m in m_end)#quicksum(quicksum(P[n*num_functions+m,i]*P[n*num_functions+m_s,j]*L[i,j]*a[m,m_s] for m_s in range(num_functions)) for j in range(num_nodes))*b[s,m]+

        for n in range(num_workflows):
            for m in range(num_functions):
                for i in range(num_nodes):
                    model.addConstr(S[n*num_functions+m,i]==quicksum(quicksum(
                        P[n * num_functions + m, i] * P[n * num_functions + m_s, j] *
                        a[m, m_s]*D[m,i,j] for m_s in
                        range(num_functions)) for j in range(num_nodes)),'Adding aux variable')#

        #if num>0:
        #    model.addConstr(quicksum(P[j,num-1] for j in range( num_functions))==0,"node_0_constr")
        model.setParam('OutputFlag', 1)
        model.update()
        P_list = []
        # for model in  model_list:
        t1=time.time()
        try:
            model.optimize()

            t2=time.time()
            t=t2-t1
            P = np.zeros((num_functions * num_workflows, num_nodes))
            S = np.zeros((num_functions * num_workflows, num_nodes))
            H = np.zeros((num_leaves, num_workflows))
            T = np.zeros((num_workflows, 1))
            M=  np.zeros((num_nodes,1))
            p= np.zeros((num_workflows*num_functions,1))
            r = 0
            s = 0
            for index,v in enumerate(model.getVars()):
                if index<num_functions*num_workflows*num_nodes:
                    P[s, r] = round(v.x)
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
                    H[s, r] = round(v.x)
                    r = r + 1
                    if r == num_workflows:
                        s = s + 1
                        r = 0
                    if s == num_leaves:
                        s=0
                elif index<2*num_functions*num_workflows*num_nodes+num_leaves*num_workflows+num_workflows:
                    T[s] = v.x
                    s = s + 1
                    if s==num_workflows:
                        s=0
                elif index<2*num_functions*num_workflows*num_nodes+num_leaves*num_workflows+num_workflows+num_nodes:
                    M[s] =v.x
                    s=s+1
                    if s==num_nodes:
                        s=0
                else:
                    p[s]=v.x
                    s=s+1
            obj=model.getObjective()
        except:
            pass
    P_list.append(P)
    #print(obj)
    print(P)

    print(H)
    print(M)
    print(p)
    return model,P,H,L,T,C,D,D_in,Time,a,b,Speed,S,t,M



