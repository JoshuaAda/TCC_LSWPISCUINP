import scienceplots
import matplotlib
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

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
    selection_cost=[]
    num_weights=99
    for k in range(num_weights):
        import_path = os.path.join('results', f'run_{k+2}','results.json')
        with open(import_path, "r") as f:  # requirements_workflow_0.json
            results = json.load(f)
        time_cost.append(results["time_cost"])
        money_cost.append(results["money_cost"])
        selection_cost.append(results["select_cost"])
    if not os.path.exists(export_path):
        raise Exception(f'The folder {export_path} where the figures will be saved does not exist.')
    else:
        print(f'Saving to folder {export_path}.')
    format_type = 'pgf'
    points=np.vstack((time_cost,money_cost,selection_cost)).T
    hull=ConvexHull(points)
    fig=plt.figure()#,ax=plt.subplots(1,1,figsize=(config_mpl.textwidth, config_mpl.textwidth / config_mpl.golden_ratio),sharex="col")
    ax=fig.add_subplot()#(projection='3d')
    #ax.plot([money for money in money_cost if money<1200],[selection_cost[k] for k,money in enumerate(money_cost) if money <1200])#_trisurf(time_cost,money_cost,selection_cost,triangles=hull.simplices)
    ax.plot(money_cost,time_cost)
    ax.set_xlabel(r'Money $[\euro{}]$')
    ax.set_ylabel(r'Time [s]')
    #ax.set_zlabel(r"Selection cost []")
    fig.savefig(os.path.join(export_path, f'results_{num_run}.' + format_type), format=format_type)
    #plt.show()
    format_type = 'svg'
    fig.savefig(os.path.join(export_path, f'results_{num_run}.' + format_type), format=format_type)