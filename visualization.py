import scienceplots
import matplotlib.pyplot as plt
import sys
import os
import json
import argparse
plt.style.use('science')

sys.path.append('./../plotTEX')
import config_mpl

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
    num_weights=10
    for k in range(num_weights):
        import_path = os.path.join('results', f'run_{k+2}','results.json')
        with open(import_path, "r") as f:  # requirements_workflow_0.json
            results = json.load(f)
        time_cost.append(results["time_cost"])
        money_cost.append(results["money_cost"])
    if not os.path.exists(export_path):
        raise Exception(f'The folder {export_path} where the figures will be saved does not exist.')
    else:
        print(f'Saving to folder {export_path}.')
    format_type = 'pgf'

    fig=plt.figure()
    plt.plot(time_cost,money_cost)
    fig.savefig(os.path.join(export_path, f'results_{num_run}.' + format_type), format=format_type)

    format_type = 'svg'
    fig.savefig(os.path.join(export_path, f'results_{num_run}.' + format_type), format=format_type)