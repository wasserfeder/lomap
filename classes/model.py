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

import networkx as nx
import itertools as it
from ..algorithms.graph_search import dfs_successors
from ..algorithms.graph_search import is_reachable_dfs

class Model(object):
	"""
	Base class for various system models.
	"""

	def __init__(self, directed=True, multi=True):
		"""
		Empty LOMAP Model object constructor.
		"""
		self.init = dict()
		self.name = 'Unnamed system model'
		self.final = set()
		if directed:
			if multi:
				self.g = nx.MultiDiGraph()
			else:
				self.g = nx.DiGraph()
		else:
			if multi:
				self.g = nx.MultiGraph()
			else:
				self.g = nx.Graph()
		self.directed = directed
		self.multi = multi

	def nodes_w_prop(self, propset):
		"""
		Returns the set of nodes with given properties.
		"""
		nodes_w_prop = set()
		for node,data in self.g.nodes(data=True):
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
