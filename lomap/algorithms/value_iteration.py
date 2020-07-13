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
import logging
import collections as coll

# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

__all__ = ['policy_synthesis', 'compute_mrp']

def compute_mrp(p, backward=False):

	# Initialize exp_rwd dict
	exp_rwd = coll.defaultdict(float)

	# Update exp_rwd for final states
	for s in p.final:
		exp_rwd[s] = 1

	if not backward:
		# Asynchronous value iteration
		# states to consider during verification
		states = set(p.g)-p.final
		done = False
		while not done:
			max_change = 0
			for s in states:
				# Calculate new expected reward
				new_rwd = 0
				for _,t,d in p.g.out_edges((s,), data=True):
					new_rwd += exp_rwd[t]*d['prob']
				# Update exp_rwd
				if new_rwd > exp_rwd[s]:
					change = abs(new_rwd-exp_rwd[s])
					max_change = max(max_change, change)
					exp_rwd[s] = new_rwd
			if max_change < 1e-9:
				done = True
	else:
		# Asynchronous backward value iteration
		states_to_consider = set()
		for s,_ in p.g.in_edges_iter(p.final):
			states_to_consider.add(s)
		states_to_consider -= p.final

		while states_to_consider:
			new_states_to_consider = set()
			for s in states_to_consider:
				# Calculate new expected reward
				new_rwd = 0
				for _,t,d in p.g.out_edges((s,), data=True):
					new_rwd += exp_rwd[t]*d['prob']
				# Update exp_rwd as necessary
				if new_rwd > exp_rwd[s]:
					exp_rwd[s] = new_rwd
					for r,_ in p.g.in_edges((s,)):
						new_states_to_consider.add(r)
			states_to_consider = new_states_to_consider

	prob = 0
	for s in p.init:
		prob += exp_rwd[s]*p.init[s]

	return (prob, exp_rwd)


def policy_synthesis(p, backward=False):

	# states to be considered during synthesis
	# (Used in classic value iteration and policy extraction)
	states = set(p.g) - p.final

	# Initialize dicts
	# Value function
	val = dict()
	# Reward for taking an action at a state
	act_val = dict()
	# Best actions for a state
	act_max = dict()
	for s in p.g.nodes_iter():
		val[s] = 0
		act_max[s] = p.available_controls(s)
		act_val[s] = dict()
	for s,_,d in p.g.out_edges_iter(data=True):
		act_val[s][d['control']] = 0

	# Update val and act_val for final states
	for s in p.final:
		val[s] = 1
		for _,_,d in p.g.out_edges((s,), data=True):
			act_val[s][d['control']] = 1

	if not backward:
		# Asynchronous value iteration
		done = False
		while not done:
			max_change = 0
			# Consider states not in final set
			for s in states:
				# Calculate reward for each control
				ctrl_rwds = coll.defaultdict(float)
				for _,t,d in p.g.out_edges((s,), data=True):
					ctrl_rwds[d['control']] += val[t]*d['prob']

				# Update act_val and act_max for this state as required
				for this_ctrl, this_rwd in ctrl_rwds.items():
					diff = abs(this_rwd - val[s])
					act_val[s][this_ctrl] = this_rwd
					if diff <= 1e-9:
						act_max[s].add(this_ctrl)
					elif this_rwd > val[s]:
						max_change = max(max_change, diff)
						val[s] = this_rwd
						act_max[s] = set([this_ctrl])

			if max_change < 1e-9:
				done = True
	else:
		# Asynchronous backward value iteration
		states_to_consider = set()
		for s,_ in p.g.in_edges_iter(p.final):
			states_to_consider.add(s)
		states_to_consider -= p.final

		while states_to_consider:
			new_states_to_consider = set()
			for s in states_to_consider:
				# Calculate reward for each control
				ctrl_rwds = coll.defaultdict(float)
				for _,t,d in p.g.out_edges((s,), data=True):
					ctrl_rwds[d['control']] += val[t]*d['prob']

				# Update act_val and act_max for this state as required
				for this_ctrl, this_rwd in ctrl_rwds.items():
					diff = abs(this_rwd - val[s])
					act_val[s][this_ctrl] = this_rwd
					if diff <= 1e-9:
						act_max[s].add(this_ctrl)
					elif this_rwd > val[s]:
						val[s] = this_rwd
						act_max[s] = set([this_ctrl])
						for r,_ in p.g.in_edges((s,)):
							new_states_to_consider.add(r)

			states_to_consider = new_states_to_consider

	# Extract optimal policy
	# For details: "Control of Probabilistic Systems under Dynamic,
	# Partially Known Environments with Temporal Logic Specifications"

	# Compute graph dist of each node to set of final states
	# Only considering actions in act_max
	# Distances of regular states set to inf
	dist = coll.defaultdict(lambda:float('inf'))
	# Distances of final states set to 0
	for s in p.final:
		dist[s] = 0

	edges_to_process = p.g.in_edges_iter(p.final, data=True)
	while edges_to_process:
		new_edges_to_process = []
		for s,t,d in edges_to_process:
			# Only consider actions in act_max[s]
			if d['control'] not in act_max[s] or d['prob'] < 1e-9:
				continue
			new_dist = dist[t] + 1
			if new_dist < dist[s]:
				dist[s] = new_dist
				new_edges_to_process += p.g.in_edges([s], data=True)
		edges_to_process = new_edges_to_process

	for s in p.final:
		# We don't care about what we do once we reach the final states
		act_max[s] = act_max[s].pop()
	for s in states:
		if abs(val[s]) < 1e-9:
			# We choose action arbitrarily for val[s] == 0
			if act_max[s]:
				act_max[s] = act_max[s].pop()
			else:
				# maybe removed in reduction step
				act_max[s] = None
		else:
			if len(act_max[s]) == 1:
				act_max[s] = act_max[s].pop()
			else:
				# Choose the action that takes us closer to satisfaction
				best_act = None
				best_dist = float('inf')
				for a in act_max[s]:
					this_dist = float('inf')
					for t,_ in p.iter_action_edges(s,a):
						this_dist = min(this_dist, dist[t])
					if this_dist < best_dist:
						best_dist = this_dist
						best_act = a
				act_max[s] = best_act

	# Maximal reachability probability from initial states
	prob = 0
	for s in p.init:
		prob += val[s] * p.init[s]

	return (prob, act_val, act_max)
