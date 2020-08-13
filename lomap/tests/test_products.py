#! /usr/bin/python

# Copyright (C) 2017, Cristian-Ioan Vasile (cvasile@mit.edu)
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
from networkx.utils import generate_unique_node
import matplotlib.pyplot as plt

from lomap.classes import Buchi, Ts
from lomap.algorithms.product import ts_times_buchi
from lomap.algorithms.dijkstra import source_to_target_dijkstra


def policy_buchi_pa(pa, weight_label='weight'):
    '''Computes the policy.'''
    if not pa.final:
        return float('Inf'), None

    vinit = generate_unique_node()
    pa.g.add_node(vinit)
    pa.g.add_edges_from([(vinit, init, {weight_label: 0}) for init in pa.init])

    prefix_costs, prefix_paths = nx.single_source_dijkstra(pa.g, source=vinit,
                                                           weight=weight_label)
    pa.g.remove_node(vinit)

    opt_cost, opt_suffix_path = float('Inf'), None
    for final in pa.final:
        if final in prefix_costs:
            suffix_cost, suffix_path = source_to_target_dijkstra(pa.g,
                    source=final, target=final, degen_paths=False,
                    weight_key=weight_label)
            if prefix_costs[final] + suffix_cost < opt_cost:
                opt_cost = prefix_costs[final] + suffix_cost
                opt_suffix_path = suffix_path

    if opt_suffix_path is None:
        return float('Inf'), None

    opt_final = opt_suffix_path[0]
    return (opt_cost, [u[0] for u in prefix_paths[opt_final][1:]],
            [u[0] for u in opt_suffix_path])

def test_ts_times_ts():
    '''TODO:'''

def test_fsa_times_fsa():
    '''TODO:'''

def test_markov_times_markov():
    '''TODO:'''

def test_ts_times_fsa():
    '''TODO:'''

def test_ts_times_buchi():
    ts = Ts.load('./simple_network.yaml')

    print('Loaded transition system of size', ts.size())
    ts.visualize(edgelabel='weight', draw='matplotlib')
    plt.show()

    for u, d in ts.g.nodes_iter(data=True):
        print(u, d)
    print()
    for u, v, d in ts.g.edges_iter(data=True):
        print(u, v, d)

    spec = 'G (F a && F g && !e)'
    buchi = Buchi()
    buchi.from_formula(spec)
    print('Created Buchi automaton of size', buchi.size())
    buchi.visualize(draw='matplotlib')
    plt.show()

    print()
    for u, d in buchi.g.nodes_iter(data=True):
        print(u, d)
    print()
    for u, v, d in buchi.g.edges_iter(data=True):
        print(u, v, d)

    pa = ts_times_buchi(ts, buchi)
    print('Created product automaton of size', pa.size())
    pa.visualize(draw='matplotlib')
    plt.show()

    print()
    for u, d in pa.g.nodes_iter(data=True):
        print(u, d)
    print()
    for u, v, d in pa.g.edges_iter(data=True):
        print(u, v, d)

    cost, prefix, suffix = policy_buchi_pa(pa)

    print('cost:', cost)
    print('prefix:', prefix)
    print('suffix:', suffix)

def test_ts_times_rabin():
    '''TODO:'''
    raise NotImplementedError

def test_mdp_times_fsa():
    '''TODO:'''

def test_mdp_times_rabin():
    '''TODO:'''
    raise NotImplementedError

if __name__ == '__main__':

    test_ts_times_buchi()
