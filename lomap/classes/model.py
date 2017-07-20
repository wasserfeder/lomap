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

import networkx as nx

# TODO: always use safe load
from yaml import load, dump #, safe_load as load
try: # try using the libyaml if installed
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError: # else use default PyYAML loader and dumper
    from yaml import Loader, Dumper


def graph_constructor(directed, multi):
    '''Returns the class to construct the appropriate graph type.'''
    if directed:
        if multi:
            constructor = nx.MultiDiGraph
        else:
            constructor = nx.DiGraph
    else:
        if multi:
            constructor = nx.MultiGraph
        else:
            constructor = nx.Graph
    return constructor


class Model(object):
    """
    Base class for various system models.
    """

    yaml_tag = u'!Model'

    def __init__(self, directed=True, multi=True):
        """
        Empty LOMAP Model object constructor.
        """
        self.name = 'Unnamed system model'
        self.init = dict()
        self.current = None
        self.final = set()
        graph_type = graph_constructor(directed, multi)
        self.g = graph_type()
        self.directed = directed
        self.multi = multi

    def nodes_w_prop(self, propset):
        """
        Returns the set of nodes with given properties.
        """
        nodes_w_prop = set()
        for node, data in self.g.nodes(data=True):
            if propset <= data.get('prop',set()):
                nodes_w_prop.add(node)
        return nodes_w_prop

    def size(self):
        return (self.g.number_of_nodes(), self.g.number_of_edges())

    def visualize(self, edgelabel=None, draw='pygraphviz'):
        """
        Visualizes a LOMAP system model
        """
        if draw == 'pygraphviz':
            nx.view_pygraphviz(self.g, edgelabel)
        elif draw == 'matplotlib':
            pos = nx.spring_layout(self.g)
            nx.draw(self.g, pos=pos)
            nx.draw_networkx_labels(self.g, pos=pos)
        else:
            raise ValueError('Expected parameter draw to be either:'
                             + '"pygraphviz" or "matplotlib"!')

    @classmethod
    def load(cls, filename):
        '''Load model from file in YAML format.'''
        with open(filename, 'r') as fin:
            return load(fin, Loader=Loader)

    def save(self, filename):
        '''Save the model to file in YAML format.'''
        with open(filename, 'w') as fout:
            dump(self, fout, Dumper=Dumper)
