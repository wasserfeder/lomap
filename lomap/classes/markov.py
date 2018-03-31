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

import re
import itertools as it
import copy

import networkx as nx

from .model import Model, graph_constructor
from networkx.drawing.nx_agraph import graphviz_layout
import pdb


class FileError(Exception):
    pass


class Markov(Model):
    """
    Base class for Markov models (MCs, MDPs, etc.)
    MCs are MDPs with a single default action.
    """

    yaml_tag = '!Markov'

    def mdp_from_det_ts(self, ts):
        self.name = copy.deepcopy(ts.name)
        self.init = copy.deepcopy(ts.init)
        self.g = copy.deepcopy(ts.g)

        if len(ts.init) != 1:
            raise Exception()
        if ts.init[list(ts.init.keys())[0]] != 1:
            raise Exception()
        for u,v,key in self.g.edges_iter(keys=True):
            self.g.edge[u][v][key]['prob'] = 1.0

    def read_from_file(self, path): 
        """
        Reads a LOMAP Markov object from a given file
        """

        ##
        # Open and read the file
        ##
        try:
            with open(path, 'r') as f:
                lines = f.read().splitlines()
        except:
            raise FileError('Problem opening file {} for reading.'.format(path))
        line_cnt = 0

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
        
        # Initial distribution sum must be equal to 1
        init_prob_sum = 0
        for init in self.init:
            init_prob_sum += self.init[init]

        if init_prob_sum != 1:
            raise FileError('Initial distribution of a Markov model must'
                            + 'sum to 1, you have {}.'.format(init_prob_sum))

        ##
        # End of part-1
        ##

        if(lines[line_cnt] != ';'):
            raise FileError("Expected ';' after model attributes, read: '{}'."
                            .format(line_cnt, lines[line_cnt]))
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
            for node in list(state_attr.keys()):
                # Reset label of the node
                self.g.node[node]['label'] = node
                for key in list(state_attr[node].keys()):
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
            nx.draw_networkx(self.g,pos=nx.get_node_attributes(self.g, 'location'), prog='dot')
        elif draw == 'matplotlib':
            pos = nx.get_node_attributes(self.g, 'location')
            if len(pos) != self.g.number_of_nodes():
                pos = nx.spring_layout(self.g)
            if current_node is None:
                colors = 'r'
            else:
                if current_node == 'init':
                    current_node = next(iter(list(self.init.keys())))
                colors = dict([(v, 'r') for v in self.g])
                colors[current_node] = 'b'
                colors = list(colors.values())
            nx.draw(self.g, pos=pos, node_color=colors)
            nx.draw_networkx_labels(self.g, pos=pos)
            edge_labels = nx.get_edge_attributes(self.g, edgelabel)
            
            if type(self.g).__name__ == 'MultiDiGraph':
                new_edge_labels = {}
                for key in edge_labels:
                    key1 = key[0]
                    key2 = key[1]
                    new_edge_labels[(key1, key2)] = self.g.edge[key[0]][key[1]][key[2]][edgelabel]
                edge_labels = new_edge_labels

            # if type(self.g).__name__ == 'MultiDiGraph':
            #     new_edge_labels = {}
            #     for key in edge_labels:
            #         value = edge_labels[key]
            #         pdb.set_trace()
            #         direction = key[2]
            #         direc = direction[0]
            #         new_string = direc + ": " + str(value)
            #         if key[0:2] in new_edge_labels:
            #             new_edge_labels[key[0:2]] += ", " + new_string
            #         elif key[1::-1] not in new_edge_labels:
            #             new_edge_labels[key[0:2]] = new_string
            #         if key[1::-1] in new_edge_labels and key[0] != key[1]:
            #             # pdb.set_trace()
            #             for nkey in self.g[key[0]][key[1]]:
            #                 ndirec = nkey[0]
            #                 new_string = ndirec + ": " + str(self.g[key[0]][key[1]][nkey][edgelabel])
            #                 new_edge_labels[key[1::-1]] += ", " + new_string
            #     edge_labels = new_edge_labels
            nx.draw_networkx_edge_labels(self.g, pos=pos,
                                         edge_labels=edge_labels)
        else:
            raise ValueError('Expected parameter draw to be either:'
                             + '"pygraphviz" or "matplotlib"!')
