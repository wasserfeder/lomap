# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
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

import re
import itertools as it

import networkx as nx

from model import Model, graph_constructor


class FileError(Exception):
    pass


class Ts(Model): #TODO: make independent of graph type
    """
    Base class for (weighted) transition systems.
    """

    def read_from_file(self, path): 
        """
        Reads a LOMAP Ts object from a given file
        """

        ##
        # Open and read the file
        ##
        try:
            with open(path, 'r') as f:
                lines = f.read().splitlines()
        except:
            raise FileError('Problem opening file {} for reading.'.format(path))
        line_cnt = 0;

        ##
        # Part-1: Model attributes
        ##

        # Name of the model
        try:
            m = re.match(r'name (.*$)', lines[line_cnt])
            self.name = m.group(1)
            line_cnt += 1
        except:
            raise FileError("Line 1 must be of the form:"
                            + " 'name name_of_the_transition_system',"
                            + " read: '{}'.".format(lines[line_cnt]))

        # Initial distribution of the model
        # A dictionary of the form {'state_label': probability}
        try:
            m = re.match(r'init (.*$)', lines[line_cnt])
            self.init = eval(m.group(1))
            line_cnt += 1
        except:
            raise FileError("Line 2 must give the initial distribution of"
                            + " the form {'state_label': 1}, read:"
                            + " '{}'.".format(lines[line_cnt]))

        # Single state for det-ts, multiple states w/ prob. 1 for nondet-ts
        for init in self.init:
            if self.init[init] != 1:
                raise FileError('Initial probability of state {} cannot be {}'
                                + ' in a transition system.'.format(
                                 init, self.init[init]))

        ##
        # End of part-1
        ##

        if(lines[line_cnt] != ';'):
            raise FileError("Expected ';' after model attributes, read: '{}'.".
                            format(line_cnt, lines[line_cnt]))
        line_cnt += 1
        
        ##
        # Part-2: State attributes
        ##

        # We store state attributes in a dict keyed by states as
        # we haven't defined them yet
        state_attr = dict();
        try:
            while(line_cnt < len(lines) and lines[line_cnt] != ';'):
                m = re.search('(\S*) (.*)$', lines[line_cnt])
                state_attr[m.group(1)] = eval(m.group(2))
#                 exec("state_attr['%s'] = %s" % (m.group(1), m.group(2)))
                line_cnt += 1
            line_cnt+=1
        except:
            raise FileError('Problem parsing state attributes.')
        
        ##
        # Part-3: Edge list with attributes
        ##
        try:
            graph_type = graph_constructor(self.directed, self.multi)
            self.g = nx.parse_edgelist(lines[line_cnt:], comments='#',
                                       create_using=graph_type())
        except:
            raise FileError('Problem parsing definitions of the transitions.') 
        
        # Add state attributes to nodes of the graph
        try:
            for node in state_attr.keys():
                # Reset label of the node
                self.g.node[node]['label'] = node
                for key in state_attr[node].keys():
                    # Copy defined attributes to the node in the graph
                    # This is a shallow copy, we don't touch
                    # state_attr[node][key] afterwards
                    self.g.node[node][key] = state_attr[node][key]
                    # Define custom node label
                    self.g.node[node]['label'] = r'{}\n{}: {}'.format(
                         self.g.node[node]['label'], key, state_attr[node][key])
        except:
            raise FileError('Problem setting state attributes.')
    
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
        Visualizes a LOMAP system model
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
                    current_node = next(self.init.iterkeys())
                colors = dict([(v, 'r') for v in self.g])
                colors[current_node] = 'b'
                colors = colors.values()
            nx.draw(self.g, pos=pos, node_color=colors)
            nx.draw_networkx_labels(self.g, pos=pos)
            edge_labels = nx.get_edge_attributes(self.g, edgelabel)
            nx.draw_networkx_edge_labels(self.g, pos=pos,
                                         edge_labels=edge_labels)
        else:
            raise ValueError('Expected parameter draw to be either:'
                             + '"pygraphviz" or "matplotlib"!')
