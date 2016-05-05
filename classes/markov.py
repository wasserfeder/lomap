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
import copy

class FileError(Exception):
	pass

class Markov(Model):
	"""
	Base class for Markov models (MCs, MDPs, etc.)
	MCs are MDPs with a single default action.
	"""
	
	def mdp_from_det_ts(self, ts):
		self.name = copy.deepcopy(ts.name)
		self.init = copy.deepcopy(ts.init)
		self.g = copy.deepcopy(ts.g)

		if len(ts.init) != 1:
			raise Exception()
		if ts.init[ts.init.keys()[0]] != 1:
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
			raise FileError('Problem opening file %s for reading.' % path)
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
			raise FileError("Line 1 must be of the form: 'name name_of_the_transition_system', read: '%s'." % lines[line_cnt])
		
		# Initial distribution of the model
		# A dictionary of the form {'state_label': probability}
		try:
			m = re.match(r'init (.*$)', lines[line_cnt])
			self.init = eval(m.group(1))
			line_cnt += 1
		except:
			raise FileError("Line 2 must give the initial distribution of the form {'state_label': 1}, read: '%s'." % lines[line_cnt])
		
		# Initial distribution sum must be equal to 1
		init_prob_sum = 0
		for init in self.init:
			init_prob_sum += self.init[init]

		if init_prob_sum != 1:
			raise FileError('Initial distribution of a Markov model must sum to 1, you have %f.' % (init_prob_sum))
	
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
					self.g.node[node]['label'] = r'%s\n%s: %s' % (self.g[node]['label'], key, state_attr[node][key])
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
	
	def next_states_of_markov(self, q, traveling_states = True):
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
		if(traveling_states and isinstance(q, tuple) and len(q)==3 and isinstance(q[2], (int, float, long))):
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
		for _,t,key,d in self.g.out_edges_iter((s,), data=True, keys=True):
			if d['control'] == a:
				if keys:
					yield(t,key,d)
				else:
					yield (t,d)
	
	def available_controls(self, s):
		ctrls = set()
		for _,_,d in self.g.out_edges_iter((s,), data=True):
			ctrls.add(d['control'])
		return ctrls

	def mc_from_mdp_policy(self, mdp, policy):

		self.name = 'MC induced on %s by policy' % mdp.name
		self.init = dict()
		self.final = set()
		# Set the initial distribution
		for s in mdp.init:
			self.init[s] = mdp.init[s]

		assert len(policy) == len(mdp.g.node), 'Policy state count (%d) and MDP state count (%d) differ!' % (len(policy), len(mdp.g.node))

		# Add edges
		for s in policy:
			for t,d in mdp.iter_action_edges(s, policy[s]):
				self.g.add_edge(s, t, attr_dict = copy.deepcopy(d))

		# Copy attributes of states from MDP
		for s in self.g:
			self.g.node[s] = copy.deepcopy(mdp.g.node[s])

	def visualize(self):
		"""
		Visualizes a LOMAP system model
		"""
		nx.view_pygraphviz(self.g, 'prob')
