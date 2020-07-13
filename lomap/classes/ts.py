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
#from builtins import next
import itertools as it

import networkx as nx

from lomap.classes.model import Model


class Ts(Model): #TODO: make independent of graph type
    """
    Base class for (weighted) transition systems.
    """

    yaml_tag = u'!Ts'

    def controls_from_run(self, run):
        """
        Returns controls corresponding to a run.
        If there are multiple controls for an edge, returns the first one.
        """
        controls = [];
        for s, t in it.izip(run[:-1], run[1:]):
            # The the third zero index for choosing the first parallel
            # edge in the multidigraph
            controls.append(self.g[s][t][0].get('control', None))
        return controls

    def next_states_of_wts(self, q, traveling_states = True):
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
        if(traveling_states and isinstance(q, tuple)):
            # q is a tuple of the form (source, target, elapsed_time)
            source, target, elapsed_time = q
            # the last [0] is required because MultiDiGraph edges have keys
            rem_time = self.g[source][target][0]['weight'] - elapsed_time
            control = self.g[source][target][0].get('control', None)
            # Return a tuple of tuples
            return ((target, rem_time, control),)
        else:
            # q is a normal state of the transition system
            r = []
            for source, target, data in self.g.edges_iter((q,), data=True):
                r.append((target, data['weight'], data.get('control', None)))
            return tuple(r)

    def visualize(self, edgelabel='control', current_node=None,
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
