#!/usr/bin/env python3
"""
A bureau optimization problem solver.

Part of the assignment for Combinatorial optimization class at FEE CTU.

Sources:
	- https://cw.fel.cvut.cz/b192/_media/courses/ko/semester_project_cocontest_2020.pdf
"""

# Imports
import gurobipy as grb
import sys
import numpy as np

# Input
bureaucrat_order = []
duration = []
with open(sys.argv[1]) as f:
    citizenCount, bureaucratCount = [int(x) for x in f.readline().split()]
    for i in range(citizenCount):
        tmp = [int(x) for x in f.readline().split()]
        bureaucrat_order.append(tmp[::2])
        duration.append(tmp[1::2])

# Formulating ILP

# model -----------------------------------------------------
model = grb.Model()
# - ADD VARIABLES
# minimizing variable z
Fmax = model.addVar(vtype=grb.GRB.CONTINUOUS, name="Fmax")

# bureaucrat finish time
F = model.addVars(bureaucratCount, vtype=grb.GRB.CONTINUOUS, lb=0, name='F')

# task starting time
starting_time = {}
tasks_by_bureaucrats = [[] for i in range(bureaucratCount)]
for i in range(citizenCount):
    for j in range(len(bureaucrat_order[i])):
        starting_time[i, j] = model.addVar(vtype=grb.GRB.CONTINUOUS, lb=0, name="starting_time")
        tasks_by_bureaucrats[bureaucrat_order[i][j]].append([i, j])
        print(bureaucrat_order[i][j],i ,j)

# initialize the value of 'big M'
M = sum([sum(d) for d in duration])

# - ADD CONSTRAINTS
# F[i] <= Fmax
model.addConstrs(F[i] <= Fmax for i in range(bureaucratCount))
# finish time: s[i,j] + d[i,j] <= F
for i in range(citizenCount):
    for j in range(len(bureaucrat_order[i])):
        model.addConstr(starting_time[i, j] + duration[i][j] <= F[bureaucrat_order[i][j]])

# customer journey - tasks must go after one another as ordered
for i in range(citizenCount):
    for j in range(len(bureaucrat_order[i]) - 1):
        model.addConstr(starting_time[i, j] + duration[i][j] <= starting_time[i, j + 1])

# do not overlap tasks:
# also if overlap possible, add a binary variable to act as or together with M
preceeds = {}
for bureaucrat_task_index in range(len(tasks_by_bureaucrats)):
    for index in range(len(tasks_by_bureaucrats[bureaucrat_task_index])-1):
        i1, j1 = tasks_by_bureaucrats[bureaucrat_task_index][index]
        for i2, j2 in tasks_by_bureaucrats[bureaucrat_task_index][index+1:]:
            if i1 != i2 or j1 != j2:
                print("a for: ", bureaucrat_task_index, i1, i2)
                preceeds[bureaucrat_task_index, i1, i2] = model.addVar(vtype=grb.GRB.BINARY, name="preceeds")
                model.addConstr(starting_time[i1, j1] + duration[i1][j1] <= starting_time[i2, j2] + M * (1-preceeds[bureaucrat_task_index, i1, i2]))
                model.addConstr(starting_time[i2, j2] + duration[i2][j2] <= starting_time[i1, j1] + M * preceeds[bureaucrat_task_index, i1, i2])

# - SET OBJECTIVE
# minimize Cmax
model.setObjective(Fmax, grb.GRB.MINIMIZE)

# call the solver -------------------------------------------
model.optimize()

# write solution to a file ----------------------------------------
with open(sys.argv[2], "w") as f:
    f.write(str(int(round(Fmax.X))) + '\n')
    for bureaucrat_tasks in tasks_by_bureaucrats:
        start_time_values = [starting_time[i, j].X for i, j in bureaucrat_tasks]
        # duration_values = [duration[i][j] for i, j in bureaucrat_tasks]
        citizen_index = [i for i, j in bureaucrat_tasks]
        vals = np.array(start_time_values)
        sort_index = np.argsort(vals)
        tmp_str = " ".join([str(citizen_index[i]) for i in sort_index])
        f.write(tmp_str + "\n")

