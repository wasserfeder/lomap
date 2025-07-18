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
'''
This is a case study for the following relaxation problems on an incremental product tree'. Reference:
https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=8404066
https://journals.sagepub.com/doi/pdf/10.1177/0278364920913922
'''
# This code implements a simple case with relaxation
# The approximate product tree between the transition system (TS) and the Relaxed product automaton (WFSE X FSA).
from __future__ import print_function

import networkx as nx
from lomap import Fsa, Ts, Wfse, ts_times_wfse_times_fsa, wfse_times_fsa, ts_times_fsa
from lomap.algorithms import product, product_tree, biased_tree
import matplotlib.pyplot as plt
import numpy as np
import itertools as it
from operator import itemgetter
from lomap.algorithms import construct_biased_tree, biased_tree, uniform_geometry


def fsa_constructor(task_case):

    # Define the set of atomic propositions
    '''
    g - Goal region
    O - obstacle
    '''
    ap = set(['g', 'O', 'g_rel'])

    # Avoid the obstacle region until visiting goal region 'g'

    # No relaxation - WFSE acts as a pass-through
    if task_case == '1':
        specs = ['(!O U g)'] #canonical case

    # elif task_case == '2':
    #     raise NotImplementedError
    #     specs = ['(!O U T1) & (!O U T4)']   ## Task deletion case

    elif task_case == '3':
        specs = ['!O U g_rel']     ## Task substitution case

    else :
        print("invalid input")
        return

    fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`
    for spec in specs:
        fsa.from_formula(spec)

    ## Visualize the FSA

    # nx.draw(fsa.g, with_labels=True)
    # plt.show()

    return fsa


def ts_constructor():

    ts = Ts(directed=True, multi=False)
    ts.g = nx.DiGraph()
    ts.g.add_nodes_from([0,1,2,3,4,5])

    ts.g.add_weighted_edges_from([(0,1,1), (1,2,1),(0,3,1),(3,4,2),(4,5,1)])

    ts.init[(0)] = 1

    ## Add lables to TS nodes

    ts.g.add_node((1), attr_dict={'prop': set(['O'])})
    ts.g.add_node((2), attr_dict={'prop': set(['g'])})
    ts.g.add_node((5), attr_dict={'prop': set(['g_rel'])})
    ts = Ts(directed=True, multi=False)
    ts.g = nx.DiGraph()
    ts.g.add_nodes_from([0,1,2,3,4,5])

    ts.g.add_weighted_edges_from([(0,1,1), (1,2,1),(0,3,1),(3,4,2),(4,5,1)])

    ts.init[(0)] = 1

    ## Add lables to TS nodes

    ts.g.add_node((1), attr_dict={'prop': set(['O'])})
    ts.g.add_node((2), attr_dict={'prop': set(['g'])})
    ts.g.add_node((5), attr_dict={'prop': set(['g_rel'])})

    # # Visualize the TS
    # nx.draw(ts.g , with_labels=True, node_color='b')
    # plt.show()

    return ts


    ## Visualize the TS
    # nx.draw(ts.g , with_labels=True, node_color='b')
    # plt.show()

    return ts


def wfse_constructor(task_case):
    ap = set(['g', 'O', 'g_rel']) # set of atomic propositions
    wfse = Wfse(props=ap, multi=False)
    wfse.init = set() # HACK
    # add states
    wfse.g.add_nodes_from(['q0', 'q1', 'q2'])

    # add transitions
    # pass_through transitions
    pass_through_symbols = [(symbol, symbol, 1) for symbol in wfse.prop_bitmaps
                            if symbol >= 0]
    wfse.g.add_edge('q0', 'q0', attr_dict={'symbols': pass_through_symbols})

    user_preference = task_case


    if (user_preference == '2'):

        print("deletion")
        in_symbol = -1
        out_symbol= wfse.bitmap_of_props(set(['T1']))
        weighted_symbols = [(in_symbol, out_symbol, 10)]
        wfse.g.add_edge('q0', 'q1', attr_dict={'symbols': weighted_symbols})

    if (user_preference == '3'):
        print("substitution")

        # Substitute T2 by T1 with a penalty 2
        in_symbol = wfse.bitmap_of_props(set(['T2']))
        out_symbol = wfse.bitmap_of_props(set(['T1']))

        weighted_symbols = [(in_symbol, out_symbol, 5)]
        wfse.g.add_edge('q0', 'q2', attr_dict={'symbols': weighted_symbols})

        weighted_symbols = [( -1, out_symbol, 0)]
        wfse.g.add_edge('q2', 'q0', attr_dict={'symbols': weighted_symbols})

        # Substitute T3 by T1 with a penalty 4
        in_symbol = wfse.bitmap_of_props(set(['T3']))
        out_symbol = wfse.bitmap_of_props(set(['T1']))
        weighted_symbols = [(in_symbol, out_symbol, 8)]
        wfse.g.add_edge('q0', 'q3', attr_dict={'symbols': weighted_symbols})
        weighted_symbols = [(-1, out_symbol, 0)]
        wfse.g.add_edge('q3', 'q0', attr_dict={'symbols': weighted_symbols})

        # Substitute T4 by T1 with a penalty 6
        in_symbol = wfse.bitmap_of_props(set(['T4']))
        out_symbol = wfse.bitmap_of_props(set(['T1']))
        weighted_symbols = [(in_symbol, out_symbol, 11)]
        wfse.g.add_edge('q0', 'q4', attr_dict={'symbols': weighted_symbols})
        weighted_symbols = [(-1, out_symbol, 0)]
        wfse.g.add_edge('q4', 'q0', attr_dict={'symbols': weighted_symbols})


        # Substitute T5 by T1 with a penalty 8
        in_symbol = wfse.bitmap_of_props(set(['T5']))
        out_symbol = wfse.bitmap_of_props(set(['T1']))
        weighted_symbols = [(in_symbol, out_symbol, 14)]
        wfse.g.add_edge('q0', 'q5', attr_dict={'symbols': weighted_symbols})
        weighted_symbols = [(-1, out_symbol, 0)]
        wfse.g.add_edge('q5', 'q0', attr_dict={'symbols': weighted_symbols})

    # set the initial state
    wfse.init.add('q0')

    # set the final state
    wfse.final.add('q0')
    # wfse.final.add('q1')


    # nx.draw(wfse.g, with_labels=True)
    # nx.draw_networkx_edge_labels(wfse.g,pos=nx.spring_layout(wfse.g))
    # plt.show()

    return wfse


def main():


    print("Please enter case number:\n1. Canonical\n2. Deletion\n3. Substitution")
    task_case = input()

    fsa = fsa_constructor(task_case)
    ts = ts_constructor()
    wfse = wfse_constructor(task_case)
    n_max = 1000
    para = dict()
    # lite version, excluding extending and rewiring
    para['is_lite'] = False
    # step_size used in function near
    para['step_size'] = np.inf  # 0.25 * buchi.number_of_robots
    # probability of choosing node q_p_closest
    para['p_closest'] = 0.9
    # probability used when deciding the target point
    para['y_rand'] = 0.99
    # minimum distance between any pair of robots
    # para['threshold'] = task.threshold
    para['weight'] = 0.2

    print('fsa:', fsa)
    print('wfse:',wfse)

    # product_model = ts_times_wfse_times_fsa(ts, wfse,fsa)
    product_fsa = wfse_times_fsa(wfse, fsa)
    # product_model = ts_times_fsa(ts, fsa)

    print("fsa_init:", fsa.init)
    print("-----------------")
    print("product_nodes:", product_fsa.g.nodes())
    print("product_edges:", product_fsa.g.edges(data=True))

    #@TODO: 1. get minimal length dict with the source and target as the keys (use single source dijkstra)
    # 2. Feasible accepting states - for now, use the condition : min_length[(a,b)] < np.inf.


    ts_init = ts.init[(0)]
    # print("ts_init", ts_init)
    #
    #
    fsa_init = fsa.init.keys()
    fsa_init= list(map(itemgetter(0), fsa.init.items()))
    # wfse_init = wfse.init.keys()
    wfse_init = next(iter(wfse.init))
    print("fsa_init", fsa_init)
    init_state = (ts_init, (wfse_init, fsa_init[0]))
    print("inits: ",init_state)



    # product_approx = product_tree.Biased_Product_Tree(ts, product_fsa, init_state, 'init', para )
    #
    product_approx = biased_tree.BiasedTree(ts, product_fsa, init_state, 'init', 'prefix', para )

    print('Product: Init:', product_fsa.init) # initial states
    print('Product: Final:', product_fsa.final) # final states
    print('product_model_edges:', product_fsa.g.edges(data=True))
    print('TS_edge_data:', ts.g.edges(data=True))
    # print('\n\n\n')


    # get initial state in product model -- should be only one
    # Convert the sets of initial and final states into lists
    init_states = list(product_approx.init)
    print("approx init:", init_states)
    finals = list(product_approx.final_states)
    print("approx final:", finals)
    tree_pre = product_approx
    print('------------------------------ prefix path --------------------------------')
    # construct the tree for the prefix part
    print("good ")
    cost_path_pre = construct_biased_tree.construction_biased_tree(product_approx, n_max)
    print("llen", len(tree_pre.goals))
    if len(tree_pre.goals):
        pre_time = (datetime.datetime.now() - start).total_seconds()
        print('Time for the prefix path: {0:.4f} s'.format(pre_time))
        print('{0} accepting goals found'.format(len(tree_pre.goals)))
    else:
        print('Couldn\'t find the path within predetermined number of iteration')

    dijkstra_length = []    # This list stores the Dijkstra path lengths for all final states


    # Iterate over all final states and find the correponding path lenths and paths
    for each_state in product_approx.final_states:
        print(each_state)
        length = nx.dijkstra_path_length(product_approx, init_states[0], each_state,weight='weight')
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


    pa_optimal_path = nx.dijkstra_path(product_approx.g, init_states[0],pa_optimal_final_state,weight='weight')
    pa_optimal_cost = nx.dijkstra_path_length(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')
    print("TOTAL COST:", pa_optimal_cost)
    # pa_optimal_path = nx.bidirectional_dijkstra(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')
    # pa_optimal_path = nx.astar_path(product_model.g, init_states[0],pa_optimal_final_state,weight='weight')

    print("Optimal_path", pa_optimal_path)

    # Obtain the individual optimal paths for each component
    ts_optimal_path, wfse_state_path, fsa_state_path = zip(*pa_optimal_path)

    print('TS: Optimal Trajectory:', ts_optimal_path)
    print('WFSE: Optimal Trajectory:', wfse_state_path)
    print('FSA: Optimal Trajectory:', fsa_state_path)

    print('Symbol translations:')
    for ts_state, state, next_state in zip(ts_optimal_path[1:], pa_optimal_path,
                                           pa_optimal_path[1:]):
        transition_data = product_model.g[state][next_state]
        original_symbol, transformed_symbol = transition_data['prop']
        print(ts_state, ':', original_symbol, '->', transformed_symbol)


if __name__ == '__main__':
    main()
