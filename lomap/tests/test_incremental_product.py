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
This is a simple test code for checking the incremental product
https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=8404066
https://journals.sagepub.com/doi/pdf/10.1177/0278364920913922
'''
# This code implements a simple case with relaxation
# The approximate product tree between the transition system (TS) and the Relaxed product automaton (WFSE X FSA).
from __future__ import print_function

import networkx as nx
from lomap import Fsa, Ts, Wfse, ts_times_wfse_times_fsa, wfse_times_fsa, ts_times_fsa
from lomap.algorithms import product, product_tree, biased_tree, incremental_product_tsxauto
import matplotlib.pyplot as plt
import numpy as np
import itertools as it
from operator import itemgetter
from lomap.algorithms import construct_biased_tree, biased_tree, uniform_geometry


def fsa_constructor():

    # Define the set of atomic propositions
    '''
    g - Goal region
    O - obstacle
    '''
    # ap = set(['g', 'O', 'g_rel'])
    # specs = ['(!O U g)'] #canonical case
    #
    # fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`
    # for spec in specs:
    #     fsa.from_formula(spec)
    #
    # # for edge in fsa.g.edges():
    # #     nx.set_edge_attributes(fsa.g, 'weight'=1)
    # fsa.g.edges_iter(data='weight', default=1)
    # print("fsa:", fsa)
    ## Visualize the FSA

    # nx.draw(fsa.g, with_labels=True)
    # plt.show()

    ap = set(['g', 'O', 'g_rel']) # set of atomic propositions
    fsa = Fsa(props=ap, multi=False)
    # fsa.init = set() # HACK
    # add states
    fsa.g.add_nodes_from(['s_init', 's_final'])

    # add transitions
    # pass_through transitions
    inputs = set(fsa.bitmap_of_props(value) for value in [set('!g')])
    fsa.g.add_edge('s_init', 's_init', attr_dict={'input': inputs}, weight = 1 )

    inputs = set(fsa.bitmap_of_props(value) for value in [set('g')])
    fsa.g.add_edge('s_init', 's_final', attr_dict={'input': inputs} , weight = 1 )

    fsa.g.add_edge('s_final', 's_final', attr_dict={'input': fsa.alphabet}, weight = 1 )

    # set the initial state
    fsa.init['s_init'] = 1

    # add `s3` to set of final/accepting states
    fsa.final.add('s_final')
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

def main():


    # print("Please enter case number:\n1. Canonical\n2. Deletion\n3. Substitution")

    fsa = fsa_constructor()
    ts = ts_constructor()
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

    # product_model = ts_times_fsa(ts, fsa)

    #@TODO: 1. get minimal length dict with the source and target as the keys (use single source dijkstra)
    # 2. Feasible accepting states - for now, use the condition : min_length[(a,b)] < np.inf.


    ts_init = ts.init[(0)]

    fsa_init = fsa.init.keys()
    fsa_init= list(map(itemgetter(0), fsa.init.items()))
    # wfse_init = wfse.init.keys()
    print("fsa_init", fsa_init)
    init_state = (ts_init,fsa_init)

    # product_approx = product_tree.Biased_Product_Tree(ts, product_fsa, init_state, 'init', para )
    #
    product_approx = incremental_product_tsxauto.incremental_tree(ts, fsa, init_state )




if __name__ == '__main__':
    main()
