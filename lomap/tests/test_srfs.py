# Copyright (C) 2015-2017, Cristian-Ioan Vasile (cvasile@bu.edu)
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

import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from random import randint, seed

from lomap import Ts, Buchi
from lomap import ts_times_buchi
from lomap.algorithms.srfs import compute_potentials


def draw_grid(ts, edgelabel='control', prop_colors=None, current_node=None):
    assert edgelabel is None or nx.is_weighted(ts.g, weight=edgelabel)
    pos = nx.get_node_attributes(ts.g, 'location')
    if current_node == 'init':
        current_node = next(ts.init.iterkeys())
    colors = dict([(v, 'w') for v in ts.g])
    if current_node:
        colors[current_node] = 'b'
    for v, d in ts.g.nodes_iter(data=True):
        if d['prop']:
            colors[v] = prop_colors[tuple(d['prop'])]
    colors = colors.values()
    labels = nx.get_node_attributes(ts.g, 'label')
    nx.draw(ts.g, pos=pos, node_color=colors)
    nx.draw_networkx_labels(ts.g, pos=pos, labels=labels)
    edge_labels = nx.get_edge_attributes(ts.g, edgelabel)
    nx.draw_networkx_edge_labels(ts.g, pos=pos,
                                 edge_labels=edge_labels)

def generate_rewards(ts, current_ts_state):
    ci, cj = current_ts_state
    rewards = defaultdict(int)
    for i in [ci-1, ci, ci+1]:
        for j in [cj-1, cj, cj+1]:
            if (i, j) in ts.g:
                rewards[(i, j)] = randint(5, 10)
    return rewards

def compute_receding_horizon_policy(pa, current_pa_state, neighborhood_rewards,
                                    horizon, prev_policy):
    '''TODO:
    '''
    index, end_potential = None, pa.max_potential
    if prev_policy is not None:
        assert current_pa_state == prev_policy[0]

        if pa.g.node[current_pa_state]['potential'] > 0:
            potentials = [pa.g.node[q]['potential'] for q in prev_policy]
            if 0 in potentials:
                index = potentials.index(0)
            else:
                end_potential = potentials[-1]

#     print 'end_potential:', end_potential
#     print 'index:', index
    stack = [(current_pa_state, pa.g[current_pa_state].iterkeys(),
              neighborhood_rewards[current_pa_state[0]])]
    optimum_reward = 0
    policy = None
    while stack:
        q, neighbors, cr = stack[-1]
        level = len(stack)-1
#         print q, cr, pa.g.node[q]['potential'], stack
        if level == horizon:
            if pa.g.node[q]['potential'] < end_potential:
                if cr > optimum_reward:
                    optimum_reward = cr
                    policy = [e[0] for e in stack]
#                     print 'optimum reward', cr, policy
            stack.pop()
        elif index != level or pa.g.node[q]['potential'] == 0:
            try:
                nq = next(neighbors)
                ncr = cr + neighborhood_rewards[nq[0]]
                stack.append((nq, pa.g[nq].iterkeys(), ncr))
            except StopIteration:
                stack.pop()
        else:
            stack.pop()
#         print stack
#         print
    assert policy is not None
    assert len(policy) == horizon+1
    return policy[1:]

def test_srfs():
    ts = Ts(directed=False, multi=False)

    M, N = 10, 10

    ts.g.add_nodes_from([((i, j),
                          {'location': (i, j), 'prop': set(), 'label': ''})
                                          for i in range(M) for j in range(N)])

    for i in range(M):
        for j in range(N):
            if i > 0:
                ts.g.add_edge((i, j), (i-1, j), weight=1)
                if j > 0:
                    ts.g.add_edge((i, j), (i-1, j-1), weight=1)
                if j < N-1:
                    ts.g.add_edge((i, j), (i-1, j+1), weight=1)
            if i < N-1:
                ts.g.add_edge((i, j), (i+1, j), weight=1)
                if j > 0:
                    ts.g.add_edge((i, j), (i+1, j-1), weight=1)
                if j < N-1:
                    ts.g.add_edge((i, j), (i+1, j+1), weight=1)
            if j > 0:
                ts.g.add_edge((i, j), (i, j-1), weight=1)
            if j < N-1:
                ts.g.add_edge((i, j), (i, j+1), weight=1)

    ts.init[(9, 9)] = 1

    ts.g.node[(1, 1)]['prop'] = {'a'}
    ts.g.node[(1, 1)]['label'] = 'a'
    ts.g.node[(3, 8)]['prop'] = {'b'}
    ts.g.node[(3, 8)]['label'] = 'b'
    ts.g.node[(7, 2)]['prop'] = {'b'}
    ts.g.node[(7, 2)]['label'] = 'b'

    ts.g.node[(5, 5)]['prop'] = {'o'}
    ts.g.node[(5, 4)]['prop'] = {'o'}
    ts.g.node[(5, 3)]['prop'] = {'o'}
    ts.g.node[(5, 2)]['prop'] = {'o'}
    ts.g.node[(5, 6)]['prop'] = {'o'}
    ts.g.node[(5, 7)]['prop'] = {'o'}
    ts.g.node[(6, 6)]['prop'] = {'o'}
    ts.g.node[(7, 6)]['prop'] = {'o'}
    ts.g.node[(4, 4)]['prop'] = {'o'}
    ts.g.node[(3, 4)]['prop'] = {'o'}
    ts.g.node[(2, 4)]['prop'] = {'o'}

    prop_colors = {('a',):  'y', ('b',): 'g', ('o',): 'k'}

    draw_grid(ts, edgelabel='weight', prop_colors=prop_colors,
              current_node='init')
    plt.xlim(-1, M)
    plt.ylim(-1, N)
    plt.show()

    spec = 'G (F a && F b && !o)'
    buchi = Buchi()
    buchi.from_formula(spec)
    print('Created Buchi automaton of size', buchi.size())
#     buchi.visualize(draw='matplotlib')
#     plt.show()

    print
    for u, d in buchi.g.nodes_iter(data=True):
        print u, d
    print
    for u, v, d in buchi.g.edges_iter(data=True):
        print u, v, d

    pa = ts_times_buchi(ts, buchi)
    print('Created product automaton of size', pa.size())
#     pa.visualize(draw='matplotlib')
#     plt.show()

    compute_potentials(pa)
#     print
#     for u, d in pa.g.nodes_iter(data=True):
#         print u, d
    pa.max_potential = 1 + max([d['potential'] for _, d in pa.g.nodes_iter(data=True)])

    seed(1)

    horizon=2
    current_pa_state = next(pa.init.iterkeys())
    policy = None
    while True:
        current_ts_state, _ = current_pa_state

        neighborhood_rewards = generate_rewards(ts, current_ts_state)
        print 'rewards', neighborhood_rewards

        policy =  compute_receding_horizon_policy(pa, current_pa_state,
                                         neighborhood_rewards, horizon, policy)

        draw_grid(ts, edgelabel='weight', prop_colors=prop_colors,
                  current_node=current_ts_state)
        plt.xlim(-1, M)
        plt.ylim(-1, N)

        for v, r in neighborhood_rewards.iteritems():
            c = plt.Circle(v, radius=0.05*r, color=(.8, .8, .8, .7))
            plt.gcf().gca().add_artist(c)

        plt.show()

        current_pa_state = policy[0]


if __name__ == '__main__':
    test_srfs()
