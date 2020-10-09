#! /usr/bin/python

# Test case for using Weighted Finite State Error Systems.
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
import matplotlib.pyplot as plt


def fsa_constructor():
    ap = set(['a', 'b']) # set of atomic propositions
    fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`
    # add states
    fsa.g.add_nodes_from(['s0', 's1', 's2', 's3'])

    #add transitions
    inputs = set(fsa.bitmap_of_props(value) for value in [set()])
    fsa.g.add_edge('s0', 's0', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['a'])])
    fsa.g.add_edge('s0', 's1', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['b'])])
    fsa.g.add_edge('s0', 's2', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['a', 'b'])])
    fsa.g.add_edge('s0', 's3', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['a'])])
    fsa.g.add_edge('s1', 's1', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['b']), set(['a', 'b'])])
    fsa.g.add_edge('s1', 's3', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['b'])])
    fsa.g.add_edge('s2', 's2', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['a']), set(['a', 'b'])])
    fsa.g.add_edge('s2', 's3', attr_dict={'input': inputs})
    fsa.g.add_edge('s3', 's3', attr_dict={'input': fsa.alphabet})
    # set the initial state
    fsa.init['s0'] = 1
    # add `s3` to set of final/accepting states
    fsa.final.add('s3')

    return fsa


def ts_constructor():
    ts = Ts(directed=True, multi=False)
    ts.g = nx.grid_2d_graph(4, 3)
    ts.g.add_edges_from((u, u) for u in ts.g)

    ts.init[(2, 2)] = 1

    # ts.g.add_node((0, 0), attr_dict={'prop': set(['a'])})
    ts.g.add_node((0, 0), attr_dict={'prop': set(['d'])})
    # ts.g.add_node((3, 2), attr_dict={'prop': set(['b'])})
    ts.g.add_node((3, 2), attr_dict={'prop': set(['c'])})

    ts.g.add_edges_from(ts.g.edges(), weight=1)

    nx.draw(ts.g , show_labels=True)
    plt.show()

    return ts


def wfse_constructor():
    ap = set(['a', 'b', 'c', 'd']) # set of atomic propositions
    wfse = Wfse(props=ap, multi=False)
    wfse.init = set() # HACK

    # add states
    wfse.g.add_nodes_from(['q0', 'q1', 'q2', 'q3'])

    # add transitions
    pass_through_symbols = [(symbol, symbol, 1) for symbol in wfse.prop_bitmaps
                            if symbol >= 0]
    print('pass through symbols:', pass_through_symbols)
    wfse.g.add_edge('q0', 'q0', attr_dict={'symbols': pass_through_symbols})

    in_symbol = wfse.bitmap_of_props(set(['c']))
    out_symbol = wfse.bitmap_of_props(set(['b']))
    weighted_symbols = [(in_symbol, out_symbol, 2)]
    wfse.g.add_edge('q0', 'q1', attr_dict={'symbols': weighted_symbols})
    wfse.g.add_edge('q1', 'q2', attr_dict={'symbols': weighted_symbols})
    weighted_symbols = [(in_symbol, -1, 2)]
    wfse.g.add_edge('q2', 'q0', attr_dict={'symbols': weighted_symbols})

    in_symbol = wfse.bitmap_of_props(set(['d']))
    out_symbol = wfse.bitmap_of_props(set(['a']))
    weighted_symbols = [(in_symbol, out_symbol, 2)]
    wfse.g.add_edge('q0', 'q3', attr_dict={'symbols': weighted_symbols})
    weighted_symbols = [(-1, out_symbol, 2)]
    wfse.g.add_edge('q3', 'q0', attr_dict={'symbols': weighted_symbols})

    # set the initial state
    wfse.init.add('q0')

    # set the final state
    wfse.final.add('q0')

    return wfse


def main():
    fsa = fsa_constructor()
    print(fsa)
    ts = ts_constructor()
    print(ts)
    wfse = wfse_constructor()
    print(wfse)

    product_model = ts_times_wfse_times_fsa(ts, wfse, fsa)
    print(product_model)

    print('Product: Init:', product_model.init) # initial states
    print('Product: Final:', product_model.final) # final states

    # get initial state in product model -- should be only one
    pa_initial_state = next(iter(product_model.init))
    # compute shortest path lengths from initial state to all other states
    lengths = nx.shortest_path_length(product_model.g, source=pa_initial_state)
    # keep path lenghts only for final states in the product model
    lengths = {final_state: lengths[final_state]
               for final_state in product_model.final}
    # find the final state with minimum length
    pa_optimal_final_state = min(lengths, key=lengths.get)
    print('Product: Optimal Final State:', pa_optimal_final_state)
    # get optimal solution path in product model from initial state to optimal
    # final state
    pa_optimal_path = nx.shortest_path(product_model.g, source=pa_initial_state,
                                       target=pa_optimal_final_state)
    print('Product: Optimal trajectory:', pa_optimal_path)
    # get optimal solution path in the transition system (robot motion model)
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
