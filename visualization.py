import scienceplots
import matplotlib
import matplotlib.pyplot as plt

from matplotlib import cm
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
    num_weights=66
    weights_path = os.path.join('settings', 'weights_2.json')
    with open(weights_path, "r") as f:  # requirements_workflow_0.json
        weights = json.load(f)
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


    #fig=plt.figure()
    weights1=np.array(weights)[:,0].tolist()
    weights2=np.array(weights)[:,1].tolist()
    weights3= np.array(weights)[:,2].tolist()
    #plt.scatter(weights3,selection_cost)
    #plt.show()
    fig=plt.figure()#,ax=plt.subplots(1,1,figsize=(config_mpl.textwidth, config_mpl.textwidth / config_mpl.golden_ratio),sharex="col")
    ax=fig.add_subplot(projection='3d')

    #for k,simplex in enumerate(hull.simplices):
    #    tri = points[simplex]
    #    if k<75:
     #       ax.plot_trisurf(tri[:, 0], tri[:, 1], tri[:, 2], alpha=0.3, edgecolor='gray')

    #ax.plot([money for money in money_cost if money<1200],[selection_cost[k] for k,money in enumerate(money_cost) if money <1200])#_trisurf(time_cost,money_cost,selection_cost,triangles=hull.simplices)
    #ax.scatter(time_cost,selection_cost,money_cost)


    points = np.vstack((time_cost[1:], selection_cost[1:], money_cost[1:])).T
    hull = ConvexHull(points)
    #for simplex, normal in zip(hull.simplices, hull.equations[:, :3]):
    #    # For minimization: normals must have all components <= 0
    #    if np.all(normal <= 0):
    #        tri = points[simplex]
    #        try:
    #            ax.plot_trisurf(tri[:, 0], tri[:, 1], tri[:, 2],alpha=0.4,edgecolor='gray')
    #        except:
    #            print('hi')
    ax.plot_trisurf(time_cost, selection_cost,money_cost, antialiased=True,cmap=cm.coolwarm,label=r"Pareto front")
    ax.scatter(time_cost[0], selection_cost[0], money_cost[0],label=r"$w=(0,\, 1,\, 0)^T$")
    ax.scatter(time_cost[10], selection_cost[10], money_cost[10],label=r"$w=(0,\, 0,\, 1)^T$" )
    ax.scatter(time_cost[65], selection_cost[65], money_cost[65],label=r"$w=(1,\, 0,\, 0)^T$")
    ax.set_zlabel(r'Monetary cost $[\$]$')
    ax.set_xlabel(r'Time [s]')
    ax.set_ylabel(r"Selection cost []")
    ax.xaxis.set_label_coords(0.5, -10)
    ax.legend()
    fig.savefig(os.path.join(export_path, f'results_{num_run}.' + format_type), format=format_type)
    plt.show()
    format_type = 'svg'
    fig.savefig(os.path.join(export_path, f'results_{num_run}.' + format_type), format=format_type)