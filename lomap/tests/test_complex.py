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
from lomap import Fsa, Ts, Wfse, ts_times_wfse_times_fsa
from lomap.algorithms import product, dijkstra, modified_dijkstra
import matplotlib.pyplot as plt
import numpy as np
import os

def fsa_constructor():

    # Define the set of atomic propositions
    ap = set(['T1', 'T2', 'T3', 'T4','T5', 'O','B','O2'])

        # specs = ['(F T4 & (!O2 U (T4 & X T4)) )']
        # specs  = ['(! O U (F T1 & X (F T2)))'] 
        # specs = ['(!O U (T1 & X T1))'] 

    

    # Desired behavior: Substitute first two instances of T4 by two T5. Substitute the next one by one T3, go to T2. Substitute T1 by T2. 

    # Current issue: Final states set empty


    specs = ['( !O2 U F(T4 & X T4) & X (F T4 & F T2 & (! T2 U T4)) & X (F T4 & F T1 & (!O U T1)))']



    fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`
    for spec in specs:
        fsa.from_formula(spec)

    return fsa


def ts_constructor():

    ts = Ts(directed=True, multi=False)
    ts.g = nx.DiGraph()
    ts.g.add_nodes_from([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14])

    ts.g.add_weighted_edges_from([(0,6,1), (6,5,1),(6,7,2),(6,8,2),(7,14,1),(14,4,1),(8,9,1),(7,10,4),(5,6,1),(5,5,1),
                                  (9,10,1),(10,11,4),(11,1,4),(8,10,4),(8,12,1),
                                  (12,3,1),(3,3,1),(3,12,1),(12,13,3),(13,2,1),(2,2,1),(1,1,1),(4,14,1), (14,7,1),(4,4,1), (5,5,1)])  ## 14 is obstacle 2 
 
    ts.init[(0)] = 1

    ## Add lables to TS nodes

    ts.g.add_node((1), attr_dict={'prop': set(['T1'])})  
    ts.g.add_node((2), attr_dict={'prop': set(['T2'])})
    ts.g.add_node((3), attr_dict={'prop': set(['T3'])})
    ts.g.add_node((4), attr_dict={'prop': set(['T4'])})
    ts.g.add_node((5), attr_dict={'prop': set(['T5'])})
    ts.g.add_node((10), attr_dict={'prop': set(['O'])})
    ts.g.add_node((14), attr_dict={'prop': set(['O2'])})
    ts.g.add_node((9), attr_dict={'prop': set(['B'])})


    ## Visualize the TS
    # nx.draw(ts.g , with_labels=True, node_color='b')
    # plt.show()

    return ts


def wfse_constructor():
    ap = set(['T1', 'T2', 'T3', 'T4','T5','O','B', 'O2']) # set of atomic propositions
    wfse = Wfse(props=ap, multi=False)
    wfse.init = set() # HACK

    # add states
    wfse.g.add_nodes_from(['q0', 'q1', 'q2', 'q3','q4','q5','q6','q7','q8'])

    # add transitions
    pass_through_symbols = [(symbol, symbol, 1) for symbol in wfse.prop_bitmaps
                            if symbol >= 0]
    # print('pass through symbols:', pass_through_symbols)
    wfse.g.add_edge('q0', 'q0', attr_dict={'symbols': pass_through_symbols})
    # wfse.g.add_edge('q4', 'q4', attr_dict={'symbols': pass_through_symbols})
    # wfse.g.add_edge('q6', 'q6', attr_dict={'symbols': pass_through_symbols})


    in_symbol = wfse.bitmap_of_props(set(['T5']))
    out_symbol = wfse.bitmap_of_props(set(['T4']))
    # out_symbol = -1
    weighted_symbols = [(in_symbol, out_symbol, 5)]
    wfse.g.add_edge('q0', 'q4', attr_dict={'symbols': weighted_symbols})

    wfse.g.add_edge('q4', 'q4', attr_dict={'symbols': weighted_symbols})


    in_symbol = wfse.bitmap_of_props(set())
    out_symbol = wfse.bitmap_of_props(set())
    weighted_symbols = [(in_symbol,out_symbol,1)]
    # wfse.g.add_edge('q4', 'q5', attr_dict={'symbols': weighted_symbols})

    wfse.g.add_edge('q4', 'q5', attr_dict={'symbols': weighted_symbols})
    wfse.g.add_edge('q5', 'q5', attr_dict={'symbols': weighted_symbols})


    in_symbol = wfse.bitmap_of_props(set(['T5']))
    out_symbol = wfse.bitmap_of_props(set(['T4']))
    # out_symbol = -1
    weighted_symbols = [(in_symbol, out_symbol, 5)]
    wfse.g.add_edge('q5', 'q2', attr_dict={'symbols': weighted_symbols})

    # weighted_symbols = [(-1,-1,1)]
    # wfse.g.add_edge('q5', 'q0', attr_dict={'symbols': weighted_symbols})

    in_symbol = wfse.bitmap_of_props(set())
    out_symbol = wfse.bitmap_of_props(set())
    weighted_symbols = [(in_symbol,out_symbol,1)]
    # wfse.g.add_edge('q4', 'q5', attr_dict={'symbols': weighted_symbols})

    wfse.g.add_edge('q2', 'q2', attr_dict={'symbols': weighted_symbols})

    in_symbol = wfse.bitmap_of_props(set(['T3']))
    # out_symbol = wfse.bitmap_of_props(set(['T4']))
    out_symbol = -1
    weighted_symbols = [(in_symbol, out_symbol, 3)]
    wfse.g.add_edge('q2', 'q6', attr_dict={'symbols': weighted_symbols})

    out_symbol = -1

    weighted_symbols = [(in_symbol, out_symbol, 1)]
    wfse.g.add_edge('q6', 'q7', attr_dict={'symbols': weighted_symbols})


    in_symbol = wfse.bitmap_of_props(set())
    out_symbol = wfse.bitmap_of_props(set())
    weighted_symbols = [(in_symbol,out_symbol,1)]
    # wfse.g.add_edge('q4', 'q5', attr_dict={'symbols': weighted_symbols})

    wfse.g.add_edge('q7', 'q7', attr_dict={'symbols': weighted_symbols})

    weighted_symbols = [(-1, -1, 1)]
    wfse.g.add_edge('q7', 'q0', attr_dict={'symbols': weighted_symbols})

    in_symbol = -1
    # out_symbol = wfse.bitmap_of_props(set())
    out_symbol= wfse.bitmap_of_props(set(['T4'])) 
    # weighted_symbols = [(in_symbol, out_symbol, 2)]
    weighted_symbols = [(in_symbol, out_symbol, 10)]
    wfse.g.add_edge('q0', 'q1', attr_dict={'symbols': weighted_symbols})
    # weighted_symbols = [(-1, -1, 0)]    
    # wfse.g.add_edge('q1', 'q0', attr_dict={'symbols': weighted_symbols})    

    in_symbol = wfse.bitmap_of_props(set(['T2']))
    out_symbol = wfse.bitmap_of_props(set(['T1']))
    # out_symbol = -1
    weighted_symbols = [(in_symbol, out_symbol, 7)]
    wfse.g.add_edge('q1', 'q8', attr_dict={'symbols': weighted_symbols})
    weighted_symbols = [(-1, -1, 1)]

    wfse.g.add_edge('q8', 'q0', attr_dict={'symbols': weighted_symbols})


    # set the initial state
    wfse.init.add('q0')

    # set the final state
    wfse.final.add('q0')
    # wfse.final.add('q4')


    # nx.draw(wfse.g, with_labels=True)
    # nx.draw_networkx_edge_labels(wfse.g,pos=nx.spring_layout(wfse.g))
    # plt.show()

    return wfse


def main():


    print("path:<><><>><><>",os.path.dirname(nx.__file__))

    print("Please enter case number:\n1. Canonical\n2. Deletion\n3. Substitution \n 4 \n 5")
    # task_case = raw_input()

    fsa = fsa_constructor()
    print(fsa)
    ts = ts_constructor()
    # print(ts)
    wfse = wfse_constructor()
    # print(wfse)

    product_model = ts_times_wfse_times_fsa(ts, wfse, fsa)

    print('Product: Init:', product_model.init) # initial states
    print('Product: Final:', product_model.final) # final states
    print('product_model_edges:', product_model.g.edges(data=True))
    print('TS_edge_data:', ts.g.edges(data=True))
    print('\n\n\n')


    # get initial state in product model -- should be only one
    # Convert the sets of initial and final states into lists
    init_states = list(product_model.init)
    final_states = list(product_model.final)
    dijkstra_length = []    # This list stores the Dijkstra path lengths for all final states 


    # for parameter in np.arange(0.1,1,0.1):

        # Iterate over all final states and find the correponding path lenths and paths
    for each_state in product_model.final:
        print(each_state)
        length = nx.dijkstra_path_length(product_model.g, init_states[0], each_state,weight='weight')
            # length = modified_dijkstra.dijkstra_path_length(product_model.g, init_states[0], each_state,weight='weight', parameter=parameter)


        dijkstra_length.append(length)
        print("length:",dijkstra_length)


        if (not dijkstra_length):
            robot_current_state = ts.init
            print("No feasible final states, deleting the tasks...")
            return

        # Get the index corresponding to the minimum cost and retrieve the corresponding final state

        pa_optimal_index = np.argmin(dijkstra_length)
        pa_optimal_final_state = final_states[pa_optimal_index]
        print("pa_optimal_final_state:", pa_optimal_final_state)

        # Find out the min length path with the optimal final state as a target using Dijkstra 


        pa_optimal_path = nx.dijkstra_path(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')
        # pa_optimal_path = modified_dijkstra.dijkstra_path(product_model.g, init_states[0],pa_optimal_final_state,weight='weight',parameter=parameter)


        # pa_optimal_path = dijkstra.source_to_target_dijkstra(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')

        pa_optimal_cost = nx.dijkstra_path_length(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')
        # pa_optimal_cost = modified_dijkstra.dijkstra_path_length(product_model.g, init_states[0],pa_optimal_final_state,weight='weight',parameter=parameter)

        print("TOTAL COST:", pa_optimal_cost)
        # pa_optimal_path = nx.bidirectional_dijkstra(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')
        # pa_optimal_path = nx.astar_path(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')

        print("Optimal_path", pa_optimal_path)

        # Obtain the individual optimal paths for each component 
        ts_optimal_path, wfse_state_path, fsa_state_path = zip(*pa_optimal_path)

        print('TS: Optimal Trajectory:', ts_optimal_path)
        print('WFSE: Optimal Trajectory:', wfse_state_path)
        print('FSA: Optimal Trajectory:', fsa_state_path)

        print('WFSE_nodes_size:', wfse.g.number_of_nodes())
        print('wfse_edges_size:', wfse.g.number_of_edges())
        print('PA_nodes_size:', product_model.g.number_of_nodes())
        print('PA_edges_size:', product_model.g.number_of_edges())


        print('Symbol translations:')
        for ts_state, state, next_state in zip(ts_optimal_path[1:], pa_optimal_path,
                                               pa_optimal_path[1:]):
            transition_data = product_model.g[state][next_state]
            original_symbol, transformed_symbol = transition_data['prop']
            print(ts_state, ':', original_symbol, '->', transformed_symbol)


if __name__ == '__main__':
    main()
