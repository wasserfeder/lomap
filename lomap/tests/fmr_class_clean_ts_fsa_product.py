#! /usr/bin/python

# Test case for using Weighted Finite State Error Systems for task substitution
# Copyright (C) 2020, Cristian-Ioan Vasile (cvasile@lehigh.edu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.



from __future__ import print_function

import networkx as nx
from lomap import Fsa, Ts, Wfse, ts_times_wfse_times_fsa, ts_times_fsa
from lomap.algorithms import product
import matplotlib.pyplot as plt
import numpy as np


def fsa_constructor(task_case):

    # Define the set of atomic propositions
    ap = set(['T1', 'T2', 'T3', 'T4','T5', 'O','B','NB'])


    # Avoid the obstacle region until visiting T1

    if task_case == '1':
        specs = ['F T1 & F B'] #canonical case

    elif task_case == '2':
        specs = ['(!O U T1) & (!O U T4) & (!O U B)']   ## Task deletion case

    elif task_case == '3':
        specs = ['(!O U T1) & (!O U B)']     ## Task substitution case

    else :
        print("invalid input")
        return

    fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`
    for spec in specs:
        fsa.from_formula(spec)

    ## Visualize the automata

    # nx.draw(fsa.g, with_labels=True)
    # plt.show()

    return fsa


def ts_constructor():

    ts = Ts(directed=True, multi=False)
    ts.g = nx.DiGraph()
    ts.g.add_nodes_from([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])

    ts.g.add_weighted_edges_from([(0,6,1), (6,5,1),(5,6,1),(6,7,2),(6,8,2),(7,14,1),(7,10,2),(14,7,1),(14,4,1),(4,14,1),(8,9,1),
                                  (9,10,2),(10,11,3),(11,1,1),(1,11,1),(8,10,4),(8,12,1),
                                  (12,3,1),(3,12,1),(12,13,2),(13,2,1),(2,13,1),(13,15,1),(15,2,1)])

    ts.init[(0)] = 1

    ## Add lables to TS nodes

    ts.g.add_node((1), attr_dict={'prop': set(['T1'])})
    ts.g.add_node((2), attr_dict={'prop': set(['T2'])})
    ts.g.add_node((3), attr_dict={'prop': set(['T3'])})
    ts.g.add_node((4), attr_dict={'prop': set(['T4'])})
    ts.g.add_node((5), attr_dict={'prop': set(['T5'])})
    ts.g.add_node((10), attr_dict={'prop': set(['O'])})
    ts.g.add_node((9), attr_dict={'prop': set(['B'])})
    ts.g.add_node((7), attr_dict={'prop': set(['NB'])})
    ts.g.add_node((12), attr_dict={'prop': set(['NB'])})



    ## Visualize the TS
    # nx.draw(ts.g , with_labels=True, node_color='b')
    # plt.show()

    return ts


def main():


    print("Please enter case number:\n1. Canonical\n2. Deletion\n3. Substitution")
    task_case = input()
    # task_case = raw_input()

    fsa = fsa_constructor(task_case)
    ts = ts_constructor()

    product_model = ts_times_fsa(ts, fsa)

    # get initial state in product model -- should be only one
    # Convert the sets of initial and final states into lists
    init_states = list(product_model.init)
    final_states = list(product_model.final)
    dijkstra_length = []    # This list stores the Dijkstra path lengths for all final states

    # Iterate over all final states and find the correponding path lenths and paths
    for each_state in product_model.final:
        length = nx.dijkstra_path_length(product_model.g, init_states[0], each_state,weight='weight')
        dijkstra_length.append(length)

    if (not dijkstra_length):
        robot_current_state = ts.init
        print("No feasible final states, deleting the tasks...")
        return

    # Get the index corresponding to the minimum cost and retrieve the corresponding final state

    pa_optimal_index = np.argmin(dijkstra_length)
    pa_optimal_final_state = final_states[pa_optimal_index]

    # Find out the min length path with the optimal final state as a target using Dijkstra
    pa_optimal_path = nx.dijkstra_path(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')
    pa_optimal_cost = nx.dijkstra_path_length(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')

    pa_optimal_path = nx.bidirectional_dijkstra(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')
    pa_optimal_path = nx.astar_path(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')

    # Obtain the individual optimal paths for each component
    ts_optimal_path, fsa_state_path = zip(*pa_optimal_path)


    print("solution", pa_optimal_path)
    print("total cost:", pa_optimal_cost)
    print("TS path:", ts_optimal_path)
    print("FSA path:", fsa_state_path)

if __name__ == '__main__':
    main()
