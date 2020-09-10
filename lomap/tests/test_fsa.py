#! /usr/bin/python

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

from lomap import Fsa, Ts, ts_times_fsa, ts_times_ts


def construct_fsa():
    ap = set(['a', 'b']) # set of atomic propositions
    fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`

    # add states
    fsa.g.add_nodes_from(['s0', 's1', 's2', 's3'])

    # add transitions
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

def construct_ts():
    ts = Ts(directed=True, multi=False)
    ts.g = nx.grid_2d_graph(4, 3)

    ts.init[(1, 1)] = 1

    ts.g.add_node((0, 0), attr_dict={'prop': set(['a'])})
    ts.g.add_node((3, 2), attr_dict={'prop': set(['b'])})

    ts.g.add_edges_from(ts.g.edges(), weight=1)

    return ts

def is_word_accepted_verbose(fsa, word):
    s_current = next(iter(fsa.init))
    for symbol in word:
        s_next = fsa.next_state(s_current, symbol)
        print('state:', s_current, 'symbol:', symbol, 'next_state:', s_next)
        if s_next is None:
            print('blocked on (state, symbol):', (s_current, symbol))
            return
        s_current = s_next
    print('terminal state', s_current, 'Accept word:', s_current in fsa.final)

def main():
    fsa = construct_fsa()
    print(fsa)

    print('Is FSA deterministic:', fsa.is_deterministic())

    words = [
        [set(['a']), set(), set(['b'])],
        [set(), set(['b']), set(), set(['a'])],
        [set(['a', 'b']), set(), set()],
        [set(['b']), set(), set()],
        [set(), set(), set(['a']), set()],
    ]

    for k, word in enumerate(words):
        print('Input word', k, ':', word)
        is_word_accepted_verbose(fsa, word)
        print('Word accepted (Method):', fsa.is_word_accepted(word))

    print('Language empty?:', fsa.is_language_empty())

    fsa2 = fsa.clone()
    fsa2.g.remove_edges_from([('s0', 's1'), ('s0', 's3'), ('s2', 's3')])
    print(fsa2)
    print('Language empty?:', fsa2.is_language_empty())

    init_state = next(iter(fsa.init))
    final_state = next(iter(fsa.final))
    trajectory = nx.shortest_path(fsa.g, source=init_state, target=final_state)
    print('Accepted word:', fsa.word_from_trajectory(trajectory))

    trajectory = ['s0', 's0', 's1', 's1', 's3']
    word = fsa.word_from_trajectory(trajectory)
    print('Trajectory:', trajectory, 'Word:', word)

    ts = construct_ts()
    print(ts)
    # compute product model that captures motion and mission satisfaction at the
    # same time
    product_model = ts_times_fsa(ts, fsa)
    print(product_model)
    print('Product initial states:', product_model.init) # initial states
    print('Product accepting states:', product_model.final) # final states
    # get initial state in product model -- should be only one
    pa_initial_state = next(iter(product_model.init))
    # compute shortest path lengths from initial state to all other states
    lengths = nx.shortest_path_length(product_model.g, source=pa_initial_state)
    # keep path lenghts only for final states in the product model
    lengths = {final_state: lengths[final_state]
               for final_state in product_model.final}
    # find the final state with minimum length
    pa_optimal_final_state = min(lengths, key=lengths.get)
    print('Product optimal accepting state:', pa_optimal_final_state)
    # get optimal solution path in product model from initial state to optimal
    # final state
    pa_optimal_path = nx.shortest_path(product_model.g, source=pa_initial_state,
                                       target=pa_optimal_final_state)
    print('Product optimal accepting trajectory:', pa_optimal_path)
    # get optimal solution path in the transition system (robot motion model)
    ts_optimal_path, fsa_state_trajectory = zip(*pa_optimal_path)
    print('TS optimal accepting trajectory:', ts_optimal_path)
    print('FSA optimal accepting trajectory:', fsa_state_trajectory)

if __name__ == '__main__':
    main()
