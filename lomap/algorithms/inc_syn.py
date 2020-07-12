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

from ..classes import Markov
from ..classes import Timer
from .product import markov_times_markov
from .product import markov_times_fsa
from .value_iteration import policy_synthesis
from .value_iteration import compute_mrp

# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

__all__ = ['minimize_mdp', 'incremental_synthesis', 'classical_synthesis']

def minimize_mdp(mdp, exp_rwd, exp_rwd_ver):
	# mdp is the mdp to be minimized
	# exp_rwd is the expected rwd of taking action at a state of mdp x fsa
	# exp_rwd_ver is the expected rwd from verification

	state_cnt = len(next(iter(mdp.g.node.keys())))
	min_exp_rwd_ver = dict()
	for s in exp_rwd_ver:
		mdp_state = s[:state_cnt]
		min_exp_rwd_ver[mdp_state] = min(min_exp_rwd_ver.get(mdp_state,float('inf')), exp_rwd_ver[s])

	# Find out which controls must be kept
	# at each state of the mdp
	ctrls_to_keep = coll.defaultdict(set)
	for s in exp_rwd:
		for ctrl in exp_rwd[s]:
			if (exp_rwd[s][ctrl] > 0) and ((exp_rwd[s][ctrl]+1e-3) >= min_exp_rwd_ver.get(s[:-1], 0)):
				ctrls_to_keep[s[0:-1]].add(ctrl)

	# Remove edges corresponding to
	# the controls to be removed
	cnt = 0
	for s in mdp.g:
		edges = [(s, t, key)
			for _,t,key,d in mdp.g.out_edges_iter((s,), data=True, keys=True)
				if d['control'] not in ctrls_to_keep[s]]
		mdp.g.remove_edges_from(edges)
		#logger.info('Removed %s -%s-> %s' % (s, d['control'][0], t))
		cnt += len(edges)
	logger.info('Removed %d edges' % cnt)


def incremental_synthesis(vehicle_mdp, fsa, targets, prop_set_fn, assumed_props=None):

	mdp = vehicle_mdp
	i = 0
	max_prod_mdp = (0,0)
	max_prod_mc = (0,0)

	while targets:
		iter_name = 'Iteration %d - ' % (i+1)
		with Timer('Iteration %d' % (i+1)):
			new_target = targets.pop(0)
			logger.info(iter_name + 'Considering target %s' % new_target.name)

			# Take the product with the previous mdp
			mdp = markov_times_markov((mdp, new_target))
			#logger.info(iter_name + 'Size of the partial model: %d nodes, %d edges' % mdp.size())
			if assumed_props:
				prop_set_fn(mdp, assumed_props[i])
			else:
				prop_set_fn(mdp)

			# Compute the product MDP
			p = markov_times_fsa(mdp, fsa)
			logger.info(iter_name + 'Size of the partial product MDP: %d nodes, %d edges' % p.size())
			if p.size() > max_prod_mdp:
				max_prod_mdp = p.size()

			# Find the optimal policy
			prob, exp_rwd, policy = policy_synthesis(p)
			logger.info(iter_name + 'Synthesis probability: %.6f' % prob)
			#pp.pprint(policy)

			if prob < 1e-6:
				logger.warn('Specification is not satisfiable! Synthesis probability: %f' % prob)
				break

			if targets:
				# Verification
				mc = Markov()
				# Compute the MC induced by policy
				mc.mc_from_mdp_policy(p, policy)
				mc = markov_times_markov(tuple([mc]+targets))
				prop_set_fn(mc)
				# MC times FSA
				p_verify = markov_times_fsa(mc, fsa)
				logger.info(iter_name + 'Size of Product MC: %d nodes, %d edges' % p_verify.size())
				if p_verify.size() > max_prod_mc:
					max_prod_mc = p_verify.size()
				prob_ver, exp_rwd_ver = compute_mrp(p_verify)
				logger.info(iter_name + 'Verification probability: %.6f' % prob_ver)
				if abs(prob_ver - prob) <= 1e-6:
					logger.info('Optimal policy w/ prob %f found before considering all agents', prob)
					break
				# Minimization
				minimize_mdp(mdp, exp_rwd, exp_rwd_ver)
			# Increment counter
			i+=1

	logger.info('Largest product MDP: %d nodes, %d edges' % max_prod_mdp)
	logger.info('Largest product MC: %d nodes, %d edges' % max_prod_mc)

def classical_synthesis(vehicle_mdp, fsa, targets, prop_set_fn):

	# Take the product of the vehicle mdp and MCs of the targets
	mdp = markov_times_markov(tuple([vehicle_mdp]+targets))
	# Print info
	#logger.info('Size of the complete system model: %d nodes, %d edges' % mdp.size())

	# Define properties at the relevant states
	prop_set_fn(mdp)

	# Construct the full-state fsa using scheck
	# (full-state ensures proper MDP after product)
	logger.info('Size of the FSA: %d nodes, %d edges' % fsa.size())

	# Compute the product MDP
	p = markov_times_fsa(mdp, fsa)
	logger.info('Size of the product MDP: %d nodes, %d edges' % p.size())

	# Find the optimal policy
	prob, exp_rwd, policy = policy_synthesis(p)
	logger.info('Maximum Probability of Satisfaction: %.6f' % prob)
