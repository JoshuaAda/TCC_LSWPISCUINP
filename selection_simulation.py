import json
import numpy as np


def selection(requests, workflow_list, prob_list):
    pass


def ending_workflows(time_list, workflows_blocked):
    pass

user_request_list = []
prob_list = []
workflows_blocked = []
time_remaining = []
test_time = 10000
time_cost_all = 0
money_cost_all = 0
w1 = 1
w2 = 1
for t in range(test_time):
    # Generate random uniform values and compare with p
    requests = np.random.rand(len(user_request_list)) < user_request_list
    workflows_blocked, time_list = selection(user_request_list, workflows_blocked, prob_list)
    time_list = time_list - 1
    workflows_blocked, time_cost, money_cost = ending_workflows(time_list, workflows_blocked)
    time_cost_all += time_cost
    money_cost_all += money_cost
overall_cost = w1 * time_cost_all + w2 * money_cost_all