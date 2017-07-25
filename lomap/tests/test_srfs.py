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
                                    horizon, index, end_potential):
    current_ts_state, _ = current_pa_state
    prev_cummulative_rewards = {current_pa_state: neighborhood_rewards[current_ts_state]}
    prev_paths = {current_pa_state: []}

    for h in range(horizon):
        cummulative_rewards = defaultdict(int)
        paths = dict()
        for pa_state in prev_cummulative_rewards:
            for next_pa_state in pa.g[pa_state]:
                next_ts_state, _ = next_pa_state
                reward = (prev_cummulative_rewards[pa_state]
                          + neighborhood_rewards[next_ts_state])
                if cummulative_rewards[next_pa_state] < reward:
                    cummulative_rewards[next_pa_state] = reward
                    paths[next_pa_state] = prev_paths[pa_state] + [next_pa_state]

        prev_cummulative_rewards = cummulative_rewards
        prev_paths = paths

    if end_potential > 0 and False: # FIXME: HACK to make it run, needs to handle case thou
        path = None
        maxr = 0
        for pa_state, pa_path in paths.iteritems():
            if (maxr < cummulative_rewards[pa_state] and
                pa.g.node[pa_state]['potential'] < end_potential):
                maxr = cummulative_rewards[pa_state]
                path = pa_path
    else:
        _, path = max(paths.iteritems(),
                  key=lambda (pa_state, pa_path): cummulative_rewards[pa_state])

    return path, None, None

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

    seed(1)

    horizon=2
    current_pa_state = next(pa.init.iterkeys())
    index = None
    potential = pa.g.node[current_pa_state]['potential']
    while True:
        current_ts_state, _ = current_pa_state

        neighborhood_rewards = generate_rewards(ts, current_ts_state)
        print 'rewards', neighborhood_rewards

        policy, index, potential = \
            compute_receding_horizon_policy(pa, current_pa_state,
                                            neighborhood_rewards, horizon,
                                            index, potential)

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
