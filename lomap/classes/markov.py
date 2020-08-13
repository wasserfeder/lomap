# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
#               2015-2017, Cristian-Ioan Vasile (cvasile@mit.edu)
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

import itertools as it
import copy

import networkx as nx

from lomap.classes.model import Model


class Markov(Model):
    """
    Base class for Markov models (MCs, MDPs, etc.)
    MCs are MDPs with a single default action.
    """

    yaml_tag = u'!Markov'

    def mdp_from_det_ts(self, ts):
        self.name = copy.deepcopy(ts.name)
        self.init = {u: 1 for u in ts.init}
        self.g = copy.deepcopy(ts.g)

        if len(ts.init) != 1:
            raise Exception()
        nx.set_edge_attributes(self.g, name='prob', values=1.0)

    def controls_from_run(self, run):
        """
        Returns controls corresponding to a run.
        If there are multiple controls for an edge, returns the first one.
        """
        controls = [];
        for s, t in it.izip(run[:-1], run[1:]):
            # The the third zero index for choosing the first parallel
            # edge in the multidigraph
            controls.append(self.g[s][t][0].get('control',None))
        return controls

    def next_states_of_markov(self, q, traveling_states = True):
        """
        Returns a tuple (next_state, remaining_time, control) for each outgoing
        transition from q in a tuple.

        Parameters:
        -----------
        q : Node label or a tuple
            A tuple stands for traveling states of the form (q,q',x), i.e.
            robot left q x time units ago and going towards q'.

        Notes:
        ------
        Only works for a regular weighted deterministic transition system
        (not a nondet or team ts).
        """
        if(traveling_states and isinstance(q, tuple) and len(q)==3 and isinstance(q[2], (int, float))):
            # q is a tuple of the form (source, target, elapsed_time)
            source, target, elapsed_time = q
            # the last [0] is required because MultiDiGraph edges have keys
            rem_time = self.g[source][target][0]['weight'] - elapsed_time
            control = self.g[source][target][0].get('control', None)
            prob = self.g[source][target][0]['prob']
            # Return a tuple of tuples
            return ((target, rem_time, control, prob),)
        else:
            # q is a normal state of the markov model
            r = []
            for source, target, data in self.g.out_edges_iter((q,), data=True):
                r.append((target, data['weight'], data.get('control', None), data['prob']))
            return tuple(r)

    def iter_action_edges(self, s, a, keys=False):
        '''Iterate over the next states of an (state, action) pair.

        #FIXME: assumes MultiDiGraph
        '''
        for _,t,key,d in self.g.out_edges_iter((s,), data=True, keys=True):
            if d['control'] == a:
                if keys:
                    yield(t,key,d)
                else:
                    yield (t,d)

    def available_controls(self, s):
        '''
        Returns all available actions (controls) at the state.
        '''
        ctrls = set()
        for _,_,d in self.g.out_edges_iter((s,), data=True):
            ctrls.add(d['control'])
        return ctrls

    def mc_from_mdp_policy(self, mdp, policy):
        '''
        Returns the MC induced by the given policy.
        '''

        self.name = 'MC induced on {} by policy'.format(mdp.name)
        self.init = dict()
        self.final = set()
        # Set the initial distribution
        self.init = dict(mdp.init)

        assert len(policy) == len(mdp.g.node), \
            'Policy state count ({}) and MDP state count ({}) differ!' \
            .format(len(policy), len(mdp.g.node))

        # Add edges
        for s in policy:
            for t, d in mdp.iter_action_edges(s, policy[s]):
                self.g.add_edge(s, t, attr_dict = copy.deepcopy(d))

        # Copy attributes of states from MDP
        for s in self.g:
            self.g.node[s] = copy.deepcopy(mdp.g.node[s])

    def visualize(self, edgelabel='prob', current_node=None,
                  draw='pygraphviz'):
        """
        Visualizes a LOMAP system model.
        """
        assert edgelabel is None or nx.is_weighted(self.g, weight=edgelabel)
        if draw == 'pygraphviz':
            nx.view_pygraphviz(self.g, edgelabel)
        elif draw == 'matplotlib':
            pos = nx.get_node_attributes(self.g, 'location')
            if len(pos) != self.g.number_of_nodes():
                pos = nx.spring_layout(self.g)
            if current_node is None:
                colors = 'r'
            else:
                if current_node == 'init':
                    current_node = next(iter(self.init.keys()))
                colors = dict([(v, 'r') for v in self.g])
                colors[current_node] = 'b'
                colors = list(colors.values())
            nx.draw(self.g, pos=pos, node_color=colors)
            nx.draw_networkx_labels(self.g, pos=pos)
            edge_labels = nx.get_edge_attributes(self.g, edgelabel)
            nx.draw_networkx_edge_labels(self.g, pos=pos,
                                         edge_labels=edge_labels)
        else:
            raise ValueError('Expected parameter draw to be either:'
                             + '"pygraphviz" or "matplotlib"!')
