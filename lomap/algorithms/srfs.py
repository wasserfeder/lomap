from __future__ import print_function
'''
.. module:: algorithms
   :synopsis: Module implements algorithms used for planning.

.. moduleauthor:: Cristian Ioan Vasile <cvasile@bu.edu>
'''
'''
    Module implements algorithms used for planning.
    Copyright (C) 2014-2016  Cristian Ioan Vasile <cvasile@bu.edu>
    Hybrid and Networked Systems (HyNeSs) Group, BU Robotics Laboratory,
    Boston University

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from builtins import map
from collections import deque

import networkx as nx


__all__ = ['self_reachable_final_states', 'self_reachable_final_states_dag',
           'compute_potentials', 'has_empty_language']


def self_reachable_final_states(model, trivial=False):
    '''Returns the list of self-reachable final states of the given model. The
    algorithms only considers those final states which are reachable from some
    initial state of the model. 
    
    Adapted from networkx.networkx.algorithms.components.strongly_connected.strongly_connected_components.

    Parameters
    ----------
    model : Model
       A finite system model.
    trivial: boolean
       Specify if self-loops are allowed in the definition of self-reachability.
    By default, self-loops are not allowed.

    Returns
    -------
    self_reachable_final_states : list
       The list of self-reachable final states.
    
    See Also
    --------
    networkx.networkx.algorithms.components.strongly_connected.strongly_connected_components
    has_empty_language

    Notes
    -----
    Uses Tarjan's algorithm with Nuutila's modifications.
    Nonrecursive version of algorithm.

    References
    ----------
    .. [1] Depth-first search and linear graph algorithms, R. Tarjan
       SIAM Journal of Computing 1(2):146-160, (1972).

    .. [2] On finding the strongly connected components in a directed graph.
       E. Nuutila and E. Soisalon-Soinen
       Information Processing Letters 49(1): 9-14, (1994).
    '''
    # TODO: check this function
    preorder = {}
    lowlink = {}
    scc_found = {}
    scc_queue = []
    self_reachable_final_states = set()
    i = 0 # Preorder counter
    for source in model.init: # only use nodes reachable from some initial state
        if source not in scc_found:
            queue = [source]
            while queue:
                v = queue[-1]
                if v not in preorder:
                    i += 1
                    preorder[v] = i
                done = True
                v_nbrs = model.g[v]
                for w in v_nbrs:
                    if w not in preorder:
                        queue.append(w)
                        done = False
                        break
                if done:
                    lowlink[v] = preorder[v]
                    for w in v_nbrs:
                        if w not in scc_found:
                            if preorder[w] > preorder[v]:
                                lowlink[v] = min([lowlink[v], lowlink[w]])
                            else:
                                lowlink[v] = min([lowlink[v], preorder[w]])
                    queue.pop()
                    if lowlink[v] == preorder[v]:
                        scc_found[v] = True
                        scc_trivial = True
                        scc_final = [v] if v in model.final else []
                        while scc_queue and preorder[scc_queue[-1]] > preorder[v]:
                            k = scc_queue.pop()
                            scc_found[k] = True
                            scc_trivial = False
                            if k in model.final:
                                scc_final.append(k)
                        if trivial or (not trivial and not scc_trivial):
                            # if self-loops are allowed or the scc is not
                            # trivial (i.e. its length is greater than 1)
                            self_reachable_final_states.extend(scc_final)
                    else:
                        scc_queue.append(v)
    return self_reachable_final_states


def self_reachable_final_states_dag(pa, dag, scc, start):
    '''The set of final self reachable states may be computed by traversing
    the SCC graph of the product automaton. For each strongly connected
    component scc it is checked if |scc| > 1 or scc reaches another strongly
    connected component which contains self-reachable final states. In both
    cases the set of self reachable states in scc can be computed as the
    intersection between the states in scc and the set of final states.
    Note: Since the scc is a partition of the states of the product automaton
    (graph), the complexity of the algorithm is linear in the number of
    transitions (edges) of the product automaton.
    '''
    visited = set()
    for cc in dag:
        dag.node[cc]['srfs'] = set()
    
    visited.add(start)
    stack = deque([start])
    while stack:
        cc = stack[-1]
        done = True
        for next_cc in dag[cc]:
            if next_cc not in visited:
                stack.append(next_cc)
                visited.add(next_cc)
                done = False
        if done:
            ccp = stack.pop()
            assert ccp == cc, (ccp, cc)
            if dag[cc]:
                srfs = set.union(*[dag.node[next_cc]['srfs']
                                                        for next_cc in dag[cc]])
            else:
                srfs = set()
            if srfs or len(scc[cc]) > 1:
                srfs |=  pa.final & set(scc[cc])
            else:
                assert scc[cc] == 1 and not srfs
                state = scc[cc][0]
                if pa.g.has_edge(state, state) and state in pa.final:
                    srfs.add(state)
            dag.node[cc]['srfs'] |= srfs
    return dag.node[start]['srfs']


def compute_potentials(pa):
    '''Computes the potential function for each state of the product automaton.
    The potential function represents the minimum distance to a self-reachable
    final state in the product automaton.
    '''
    assert 'v' not in pa.g
    # add virtual node which connects to all initial states in the product
    pa.g.add_node('v')
    pa.g.add_edges_from([('v', p) for p in pa.init])
    # create strongly connected components of the product automaton w/ 'v'
    scc = list(nx.strongly_connected_components(pa.g))
    dag = nx.condensation(pa.g, scc)
    # get strongly connected component which contains 'v'
    for k, sc in enumerate(scc[::-1]):
        if 'v' in sc:
            start = len(scc) - k - 1
            break
    assert 'v' in scc[start]
    assert list(map(lambda sc: 'v' in sc, scc)).count(True) == 1
    # get self-reachable final states
    pa.srfs = self_reachable_final_states_dag(pa, dag, scc, start)
    # remove virtual node from product automaton
    pa.g.remove_node('v')
    assert 'v' not in pa.g
    if not pa.srfs:
        return False
    # add artificial node 'v' and edges from the set of self reachable
    # states (pa.srfs) to 'v'
    pa.g.add_node('v')
    for p in pa.srfs:
        pa.g.add_edge(p, 'v', **{'weight': 0})
    # compute the potentials for each state of the product automaton
    lengths = nx.shortest_path_length(pa.g, target='v', weight='weight')
    for p in pa.g:
        pa.g.node[p]['potential'] = lengths[p]
    # remove virtual state 'v'
    pa.g.remove_node('v')
    return True

def has_empty_language(model, trivial=False):
    '''
    Checks if the language associated with the model is empty. It verifies if
    there are any self-reachable final states of the model which are also
    reachable from some initial state.
    
    Parameters
    ----------
    model : Model
       A finite system model.
    trivial: boolean
       Specify if self-loops are allowed in the definition of self-reachability.
    By default, self-loops are not allowed.

    Returns
    -------
    empty : boolean
       True if the language is empty.
    
    See Also
    --------
    networkx.networkx.algorithms.components.strongly_connected.strongly_connected_components
    self_reachable_final_states
    product
    
    Note
    ----
    This function is intended to be used on product automata.
    '''
    return len(self_reachable_final_states(model, trivial)) == 0
