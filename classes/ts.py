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
import re
import itertools
from model import Model

class FileError(Exception):
	pass

class Ts(Model):
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
			raise FileError('Problem opening file %s for reading.' % path)
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
			raise FileError("Line 1 must be of the form: 'name name_of_the_transition_system', read: '%s'." % lines[line_cnt])
		
		# Initial distribution of the model
		# A dictionary of the form {'state_label': probability}
		try:
			m = re.match(r'init (.*$)', lines[line_cnt])
			self.init = eval(m.group(1))
			line_cnt += 1
		except:
			raise FileError("Line 2 must give the initial distribution of the form {'state_label': 1}, read: '%s'." % lines[line_cnt])
		
		# Single state for det-ts, multiple states w/ prob. 1 for nondet-ts
		for init in self.init:
			if self.init[init] != 1:
				raise FileError('Initial probability of state %s cannot be %f in a transition system.' % (init, self.init[init]))
	
		##
		# End of part-1
		##

		if(lines[line_cnt] != ';'):
			raise FileError("Expected ';' after model attributes, read: '%s'." % (line_cnt, lines[line_cnt]))
		line_cnt += 1
		
		##
		# Part-2: State attributes
		##

		# We store state attributes in a dict keyed by states as
		# we haven't defined them yet
		state_attr = dict();
		try:
			while(line_cnt < len(lines) and lines[line_cnt] != ';'):
				m = re.search('(\S*) (.*)$', lines[line_cnt]);
				exec("state_attr['%s'] = %s" % (m.group(1),m.group(2)));
				line_cnt += 1
			line_cnt+=1
		except:
			raise FileError('Problem parsing state attributes.')
		
		##
		# Part-3: Edge list with attributes
		##
		try:
			self.g = nx.parse_edgelist(lines[line_cnt:], comments='#', create_using=nx.MultiDiGraph())
		except:
			raise FileError('Problem parsing definitions of the transitions.') 
		
		# Add state attributes to nodes of the graph
		try:
			for node in state_attr.keys():
				# Reset label of the node
				self.g.node[node]['label'] = node
				for key in state_attr[node].keys():
					# Copy defined attributes to the node in the graph
					# This is a shallow copy, we don't touch state_attr[node][key] afterwards
					self.g.node[node][key] = state_attr[node][key]
					# Define custom node label
					self.g.node[node]['label'] = r'%s\n%s: %s' % (self.g.node[node]['label'], key, state_attr[node][key])
		except:
			raise FileError('Problem setting state attributes.')
	
	def controls_from_run(self, run):
		"""
		Returns controls corresponding to a run.
		If there are multiple controls for an edge, returns the first one.
		"""
		controls = [];
		for s, t in zip(run[0:-1], run[1:]):
			# The the third zero index for choosing the first parallel
			# edge in the multidigraph
			controls.append(self.g[s][t][0].get('control',None))
		return controls
	
	def next_states_of_wts(self, q, traveling_states = True):
		"""
		Returns a tuple (next_state, remaining_time, control) for each outgoing transition from q in a tuple.
		
		Parameters:
		-----------
		q : Node label or a tuple
		    A tuple stands for traveling states of the form (q,q',x), i.e. robot left q x time units
		    ago and going towards q'.
		
		Notes:
		------
		Only works for a regular weighted deterministic transition system (not a nondet or team ts).
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
			for source, target, data in self.g.out_edges_iter((q,), data=True):
				r.append((target, data['weight'], data.get('control', None)))
			return tuple(r)

	def visualize(self):
		"""
		Visualizes a LOMAP system model
		"""
		nx.view_pygraphviz(self.g, 'control')
