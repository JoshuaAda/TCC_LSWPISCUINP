# Large-scale workflow placement in serverless computing using integer nonlinear programming
Under revision for Transaction on Cloud Computing
## How to use/Evaluate the results

a) Install the necessary dependencies:

```pip install -r requirements.txt```

b) Simple example:
Run the placement problem

```placement.py --num_run=0```

Calculate the costs through simulation by running

```selection_simulation.py --num_run=0```

c) Scaling experiments:

For the first comparison against the heuristic run:

```scaling_experiments.py```

In the command line run

```run_time_case_study_heuristic.bat```

To visualize or show the data run

```visualization_time_heuristic.py num_run=123```

Change 

For the second comparison against the centralized approach run:

```scaling_experiments.py```

In the command line run

```run_time_case_study.bat```

To visualize or show the data run

```visualization_time.py num_run=126```

d) Sensitivity to weights

To generate the different parameter files run

```generate_different_weights.py```

In the command line run

```run_case_study.bat```

To generate the images of the Paerto fronts run

```visualization.py --num_run=2```
