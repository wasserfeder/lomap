#! /usr/bin/env python

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
from matplotlib.path import Path
import lomap
from lomap.algorithms.dijkstra import dijkstra_to_all, source_to_target_dijkstra
from collections import defaultdict
from pprint import pprint as pp
import logging
from functools import reduce

# Logger configuration
logger = logging.getLogger(__name__)

class Planner(object):
	def __init__(self, env, quad, global_spec, local_spec, prio):
		# Initialize some fields
		self.env = env
		self.quad = quad
		self.global_spec = global_spec
		self.local_spec = local_spec
		self.prio = prio

		#
		# OFFLINE INITIALIZATION
		#

		# Construct the evnrionment TS
		self.global_ts = self.construct_global_ts()
		logger.debug('Global TS has %s states and %s edges.' % self.global_ts.size())
		#self.global_ts.visualize()

		# Construct the Buchi automaton for the global spec
		self.global_nba = lomap.Buchi()
		self.global_nba.from_formula(global_spec)
		logger.debug('Global NBA has %s states and %s edges.' % self.global_nba.size())
		#self.global_nba.visualize()

		# Take the product
		self.global_pa = lomap.ts_times_buchi(self.global_ts, self.global_nba)
		#self.global_pa.visualize()

		# Remove unreachable and unreaching final states
		self.clean_final_states()
		assert len(self.global_pa.final)>0, "Global spec '%s' is not satisfiable" % global_spec
		logger.debug('Global product automaton has %s states and %s edges.' % self.global_pa.size())
		#self.global_pa.visualize()

		# Compute the shortest distance of each node to final states
		self.dist_table, self.path_table = self.compute_dist_and_path_tables()
		logger.debug('Global product automaton distance table: %s' % self.dist_table)
		logger.debug('Global product automaton path table: %s' % self.path_table)

		# Set the current state (pick the initial state closest to finals)
		self.global_pa_state = self.compute_global_pa_init()
		logger.debug('Initial global product automaton state: %s' % (self.global_pa_state,))

		# Construct the FSA for the local spec
		self.local_fsa = self.construct_local_fsa()
		logger.debug('Local FSA has %s states and %s edges.' % self.local_fsa.size())
		self.local_fsa_state = next(iter(self.local_fsa.init.keys()))
		logger.debug('Initial local FSA state: %s.' % self.local_fsa_state)



	def compute_global_pa_init(self):
		dist_star, state_star = float('Inf'), None
		# Pick the state closest to final states
		for s in self.global_pa.init:
			dist = self.dist_table[s]
			if dist < dist_star:
				dist_star = dist
				state_star = s
		return state_star



	def construct_local_fsa(self):
		ts = lomap.Ts()
		edges = []
		init_state = None

		# Define the edges (hardcoded for now using dk.brics.automaton package
		# by Anders Moller, available at http://www.brics.dk/automaton/)
		if self.local_spec == '(assist|extinguish)*':
			edges += [('init', 'init', {'input': set(['assist'])})]
			edges += [('init', 'init', {'input': set(['extinguish'])})]
			init_state = 'init'
		elif self.local_spec == '(pickup.dropoff)*':
			edges += [('empty', 'cargo', {'input': set(['pickup'])})]
			edges += [('cargo', 'empty', {'input': set(['dropoff'])})]
			init_state = 'empty'
		elif self.local_spec == '(pickup1.dropoff1|pickup2.dropoff2)*':
			edges += [('empty', 'cargoa', {'input': set(['pickup1'])})]
			edges += [('cargoa', 'empty', {'input': set(['dropoff1'])})]
			edges += [('empty', 'cargob', {'input': set(['pickup2'])})]
			edges += [('cargob', 'empty', {'input': set(['dropoff2'])})]
			init_state = 'empty'
		else:
			assert False, 'Local spec %s is not implemented' % self.local_spec

		# Construct the ts
		for s, v, d in edges:
			ts.g.add_edge(s, v, None, d)
		# Set the initial state
		ts.init[init_state] = 1

		return ts



	def construct_local_ts(self):
		ts =  lomap.Ts()
		# ts.name: str - name of the model
		# ts.init: dict - initial distribution of the model
		# ts.final: set - accepting states
		# ts.g: a NetworkX multidigraph
		#       state property 'prop' gives the propositions satisfied at that state.
		#       edge properties 'weight' and 'control' give the weight of the edge and the corresponding control.
		ts.name = 'Local TS'

		# Find the current cell of the quad (center cell of the sensing range)
		# with integer division
		center_cell = (self.quad.x, self.quad.y)
		ts.init[center_cell] = 1

		# Define the vertices of the local TS (the sensing cells)
		for cx, cy in it.product(range(0, self.quad.sensing_range), repeat=2):
			cell = self.quad.get_sensing_cell_global_coords((cx, cy))
			props = self.quad.sensed[cx][cy]['local_reqs']
			# Add this cell with sensed local requests
			ts.g.add_node(cell, prop=props)
		assert len(ts.g) == self.quad.sensing_range**2

		# Define edges between the states of the local ts
		for cell in ts.g:
			# east, north, west, south, hold controls and corresponding neighbors
			x, y = cell
			controls = {'e':(x+1, y), 'n':(x, y+1), 'w':(x-1, y), 's':(x, y-1), 'h':(x,y)}
			for ctrl in controls:
				neigh = controls[ctrl]
				# Skip this neighbor if it is not in the local TS
				if neigh not in ts.g:
					continue
				# Add the edge
				ts.g.add_edge(cell, neigh, weight=1, control=ctrl)
		return ts



	#
	# ONLINE RECEDING HORIZON CONTROL
	#
	def next_command(self):

		# Construct the local TS
		local_ts = self.construct_local_ts()
		local_ts_state = next(iter(local_ts.init.keys()))
		# Initialize vars to hold optimal vals
		# (path_star is for debugging purposes)
		d_star, cell_next_star, target_cell_star, g_next_star, path_star = float('inf'), None, None, None, None

		# Get the set of sensed local requests
		local_reqs = reduce(lambda a,b: a|b, [local_ts.g.node[cell]['prop'] for cell in local_ts.g], set([]))
		logger.debug('Sensed local requests: %s' % local_reqs)

		# Find the set of requests that can be serviced
		# (D_service in alg.)
		enabled_reqs = set([])
		for _, _, d in self.local_fsa.g.out_edges_iter((self.local_fsa_state,), data=True):
			enabled_reqs = enabled_reqs | d['input']
		serviceable_reqs = local_reqs & enabled_reqs

		# Find the cells with static and dynamic requests
		global_req_cells = reduce(lambda a,b: a|b, [set([q]) for q in local_ts.g if q in self.env.global_reqs], set([]))
		local_req_cells = reduce(lambda a,b: a|b, [set([q]) for q in local_ts.g if local_ts.g.node[q]['prop']], set([]))

		if not serviceable_reqs:
			# Consider all neighbors of our current state in the global product automaton
			for cur, neigh in self.global_pa.g.out_edges_iter(self.global_pa_state):

				if neigh[0] in local_ts.g:
					# Avoid all cells with global and local requests
					# except the cell corresponding to neigh
					avoid_cells = (global_req_cells | local_req_cells) - {neigh[0]}
					# If neigh[0] is in local_ts, it is our target
					target_cells = {neigh[0]}
				else:
					# Avoid all cells with global and local requests
					avoid_cells = global_req_cells | local_req_cells

					# Reach boundary cells
					target_cells = set([])
					x_min, y_min = self.quad.get_sensing_cell_global_coords((0,0))
					x_max, y_max = self.quad.get_sensing_cell_global_coords((self.quad.sensing_range-1,self.quad.sensing_range-1))
					for local_cell in local_ts.g.nodes_iter():
						x, y = local_cell
						if (x == x_min or x == x_max or y == y_min or y == y_max):
							target_cells.add(local_cell)
					# Remove those cells that we have to avoid
					target_cells = target_cells - avoid_cells

				# Set incoming edge weights of avoid_cells to inf
				for u, v, k in local_ts.g.in_edges_iter(avoid_cells, keys=True):
					local_ts.g[u][v][k]['weight'] = float('inf')
				# Find shortest paths
				dists, paths = dijkstra_to_all(local_ts.g, local_ts_state)
				# Restore incoming edge weights of avoided cells
				for u, v, k in local_ts.g.in_edges_iter(avoid_cells, keys=True):
					local_ts.g[u][v][k]['weight'] = 1

				# Plan for each cell in target_cells while avoiding the cells in avoid_cells
				for target_cell in target_cells:
					# We also consider the length of the local path
					d_plan = abs(target_cell[0]-neigh[0][0]) + abs(target_cell[1]-neigh[0][1])
					d_plan += self.dist_table[neigh]
					d_plan += dists[target_cell]
					if d_plan < d_star or (d_plan == d_star and target_cell_star and (target_cell[0] < target_cell_star[0] or (target_cell[0] == target_cell_star[0] and target_cell[1] > target_cell_star[1]))):
						d_star = d_plan
						g_next_star = neigh
						cell_next_star = paths[target_cell][1]
						path_star = paths[target_cell]
						target_cell_star = target_cell

		else:
			# Drive the vehicle to the closest local request with the highest
			# priority while avoiding all other sensed local requests and
			# global requests within the sensing range

			# Find the maximum priority request (min prio number)
			max_prio = min([self.prio[req] for req in serviceable_reqs])

			# Find the set of target requests
			target_reqs = set([req for req in serviceable_reqs if self.prio[req] == max_prio])
			target_cells = set([cell for cell in local_ts.g if local_ts.g.node[cell]['prop'] & target_reqs])
			logger.debug('Will service local requests: %s at cells %s' % (target_reqs, target_cells))

			# Avoid all cells with global and local requests
			# except those in target_cells
			avoid_cells = (global_req_cells | local_req_cells) - target_cells
			logger.debug('Cells to avoid: %s' % avoid_cells)

			# Set incoming edge weights of avoid_cells to inf
			for u, v, k in local_ts.g.in_edges_iter(avoid_cells, keys=True):
				local_ts.g[u][v][k]['weight'] = float('inf')
			# Find shortest paths
			dists, paths = dijkstra_to_all(local_ts.g, local_ts_state)
			# Restore incoming edge weights of avoided cells
			for u, v, k in local_ts.g.in_edges_iter(avoid_cells, keys=True):
				local_ts.g[u][v][k]['weight'] = 1

			# Plan for each cell in target_cells while avoiding the cells in avoid_cells
			for target_cell in target_cells:
				if dists[target_cell] == float('inf'):
					# No path to this target_cell
					continue
				d_plan = dists[target_cell]
				if d_plan < d_star:
					d_star = d_plan
					g_next_star = None
					cell_next_star = paths[target_cell][1]
					path_star = paths[target_cell]

		assert d_star != float('inf'), 'Could not find a feasible local plan'
		logger.debug('Path to target: %s, cell_next_star: %s' % (path_star, cell_next_star))

		# Find the command to reach cell_next_star
		assert len(local_ts.g[local_ts_state][cell_next_star]) == 1, 'Local TS cannot have parallel edges'
		control_star = local_ts.g[local_ts_state][cell_next_star][0]['control']

		# Update global NBA state as necessary
		if g_next_star and g_next_star[0] == cell_next_star:
			self.global_pa_state = g_next_star
			logger.debug('Updated global product automaton state to: %s' % (g_next_star,))

		# Update local FSA state as necessary
		found_next_local_fsa_state = False
		next_local_req = local_ts.g.node[cell_next_star]['prop']
		if next_local_req:
			for _, next_local_fsa_state, d in self.local_fsa.g.out_edges_iter((self.local_fsa_state,), data=True):
				if d['input'] == next_local_req:
					self.local_fsa_state = next_local_fsa_state
					found_next_local_fsa_state = True
					break
			assert found_next_local_fsa_state, 'Local FSA does not have a transition for %s from its current state %s' % (next_local_req, self.local_fsa_state)

		# Turn off the serviced request as necessary
		if next_local_req:
			self.env.local_reqs[cell_next_star]['on'] = False

		return (control_star, path_star)



	def clean_final_states(self):
		# By construction all final states are reachable from
		# the initial states of global_pa

		# Find and remove the final states that cannot reach themselves
		unreaching_finals = set()
		unreaching_finals.update(self.global_pa.final)
		for final in self.global_pa.final:
			dist, _ = source_to_target_dijkstra(self.global_pa.g, final, final, degen_paths=False, weight_key='weight')
			if dist == float('inf'):
				# final cannot reach itself
				continue
			# final can reach itself
			unreaching_finals -= set([final])
		self.global_pa.final -= unreaching_finals
		# Remove unreaching finals from the set of initial states
		for state in unreaching_finals:
			if state in self.global_pa.init:
				del self.global_pa.init[state]
		# Finally, actually remove these states from the graph
		# (Can also remove states w/ fd(q) = \infty)
		self.global_pa.g.remove_nodes_from(unreaching_finals)




	def compute_dist_and_path_tables(self):
		# Find the shortest distance of each state in the product to the final states
		dist_table = dict()
		path_table = dict()
		for node in self.global_pa.g.nodes():
			dist_table[node] = float('inf') # initialize to inf
			path_table[node] = None
			dists, paths = dijkstra_to_all(self.global_pa.g, node, degen_paths=True, weight_key='weight') # returns 0 for node=final
			for final in self.global_pa.final:
				if final in dists and dists[final] < dist_table[node]:
					dist_table[node] = dists[final]
					path_table[node] = paths[final]
		return (dist_table, path_table)



	def construct_global_ts(self):
		logger.debug('Constructing the global TS')
		ts = lomap.Ts()
		# ts.name: str - name of the model
		# ts.init: dict - initial distribution of the model
		# ts.final: set - accepting states
		# ts.g: a NetworkX multidigraph
		#       state property 'prop' gives the propositions satisfied at that state.
		#       edge properties 'weight' and 'control' give the weight of the edge and the corresponding control.
		ts.name = 'Global TS'

		# Initial state of the global transition system
		init_state = (self.quad.x, self.quad.y)
		ts.init[init_state] = 1

		# Add the cells with global requests
		for cell in self.env.global_reqs:
			ts.g.add_node(cell, prop=self.env.global_reqs[cell]['reqs'])

		# Add edges between each global request cell
		for u, v in it.product(self.env.global_reqs, repeat=2):
			# Compute manhattan distance
			dist = abs(u[0]-v[0]) + abs(u[1]-v[1])
			assert (u == v) != (dist > 0), 'Global requests cannot be co-located.'
			# Change self-loop weights to 1 to prevent infinite loops during planning
			dist = 1 if dist == 0 else dist
			logger.debug('%s -> %s (dist: %s)' % (u, v, dist))
			ts.g.add_edge(u, v, weight=dist, control='N/A', label=dist)

		# If the init_state is not a global request,
		# add it to the global TS but define outgoing edges only
		if init_state not in self.env.global_reqs:
			ts.g.add_node(init_state, prop=set([]))
			for v in self.env.global_reqs:
				# Compute manhattan distance
				dist = abs(init_state[0]-v[0]) + abs(init_state[1]-v[1])
				logger.debug('%s -> %s (dist: %s)' % (init_state, v, dist))
				ts.g.add_edge(init_state, v, weight=dist, control='N/A', label=dist)

		return ts
