import scienceplots
import matplotlib
import matplotlib.pyplot as plt



import sys
import os
import json
import argparse

plt.style.use('science')
matplotlib.use('TkAgg')
sys.path.append('./../plotTEX')
import config_mpl
import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    )
    parser.add_argument("--num_run", required=True, type=int)
    args = parser.parse_args()
    num_run = args.num_run

    # setup export path
    export_path = os.path.join('results',f'run_{num_run}')
    time_cost=[]
    money_cost=[]
    overall_time_cost=[]
    selection_cost=[]
    waiting_time_cost=[]
    num_weights_util=11#66
    num_other_weights=11
    num_weights=121
    weight_1=[k*1 for k in range(num_weights_util)]
    weight_1=[]
    for k in range(num_weights_util):
        for m in range(num_other_weights):
            weight_1.append(1*k)
    weights_path = os.path.join('settings', 'weights_2.json')
    with open(weights_path, "r") as f:  # requirements_workflow_0.json
        weights = json.load(f)
    for k in range(num_weights):
        import_path = os.path.join('results', f'run_{k+2}','results.json')
        with open(import_path, "r") as f:  # requirements_workflow_0.json
            results = json.load(f)
        time_cost.append(results["time_cost"])
        money_cost.append(results["money_cost"])
        #selection_cost.append(results["select_cost"])
        waiting_time_cost.append(results["complete_time_cost"])
        overall_time_cost.append(results["complete_time_cost"]+results["time_cost"])
    if not os.path.exists(export_path):
        raise Exception(f'The folder {export_path} where the figures will be saved does not exist.')
    else:
        print(f'Saving to folder {export_path}.')
    format_type = 'pgf'


    fig=plt.figure()#,ax=plt.subplots(1,1,figsize=(config_mpl.textwidth, config_mpl.textwidth / config_mpl.golden_ratio),sharex="col")
    ax=fig.add_subplot(projection='3d')


    ax.scatter(money_cost[11::],weight_1[11::],overall_time_cost[11::])
    format_type = 'svg'
    fig.savefig(os.path.join(export_path, f'overall.' + format_type), format=format_type)
    for k in range(11):
        #plt.figure()
        fig = plt.figure()  # ,ax=plt.subplots(1,1,figsize=(config_mpl.textwidth, config_mpl.textwidth / config_mpl.golden_ratio),sharex="col")
        ax = fig.add_subplot()
        plt.scatter(money_cost[0+11*k:11+11*k],time_cost[0+11*k:11+11*k])#weight_1[k::11],waiting_time_cost[k::11])#money_cost[0+11*k:11+11*k],time_cost[0+11*k:11+11*k])#weight_1[k::11],waiting_time_cost[k::11])#money_cost[0+11*k:11+11*k],time_cost[0+11*k:11+11*k])#plt.scatter(weight_1[k::11],waiting_time_cost[k::11])#plt.scatter(money_cost[0+11*k:11+11*k],time_cost[0+11*k:11+11*k])##money_cost[0+10*k:10+10*k],time_cost[0+10*k:10+10*k])#time_cost[0+10*k:10+10*k])#weight_1[k::10],overall_time_cost[k::10])#money_cost[0+10*k:10+10*k],time_cost[0+10*k:10+10*k])#####money_cost,weight_1,overall_time_cost)
        ax.set_xlabel(r'Money cost $M$ [$\$$]')
        ax.set_ylabel(r"Basic Time $B$ [s]")
        format_type = 'pdf'
        fig.savefig(os.path.join(export_path, f'pareto_{k}.' + format_type), format=format_type)

    plt.show()
