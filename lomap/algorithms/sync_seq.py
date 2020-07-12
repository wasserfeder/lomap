#! /usr/bin/python

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

"""
Compute a synchronization sequence for a given run of a team of agents that
guarantees correctness in the field.
"""

__author__ = 'Alphan Ulusoy'

import logging

from lomap.algorithms.product import ts_times_buchi
from lomap.algorithms.field_event_ts import construct_field_event_ts
from lomap.algorithms.dijkstra import source_to_target_dijkstra

# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

def empty_language(p):
	# Not checking reachability from initial states
	# as such finals are not included by construction
	for final in p.final:
		dist, _ = source_to_target_dijkstra(p.g, final, final, degen_paths=False, weight_key='weight')
		if dist != float('inf'):
				# final can reach itself
				return False
	return True

def compute_sync_seqs(ts_tuple, rhos, tts, b, prefix, suffix):
	"""
	Compute synchronization sequences for each, i.e. wait sets,
	for each agent so that correctness in the field is guaranteed.

	Parameters
	----------
	ts_tuple: Tuple of transition system objects
		ts_tuple[i] is the transition that models agent i.

	tts: A transition system object
		tts is the team transition system that models the asynchronous
		behavior of the team of agents who are individually modeled as
		the transition systems in ts_tuple.

	b: A buchi object
		This is the buchi automaton that corresponds to the negation of
		the mission specification.

	prefix: A list of tuples
		This is the prefix of the run on the team transition system tts.

	suffix: A list of tuples
		This is the suffix of the run on the team transition system tts.

	Results
	-------
	wait_sets: A 2-D list of sets
		wait_sets[i][j] gives the list of agents that agent i must wait at
		position j of the run before satisfying any propositions at that
		state and proceeding with the next position in its run.
	"""

	# Indeces of the agents
	agents = list(range(0, len(ts_tuple)))

	# Run is prefix + suffix after removing duplicate states
	run = prefix[0:-1] + suffix[0:-1]
	suffix_start = len(prefix)-1
	logger.debug('suffix start:%d, run:%s', suffix_start, run)

	# Everyone goes in lock-step by default
	wait_sets = [[set(agents)-{ii} for jj in run] for ii in agents]

	for pos in range(0,len(run)):
		logger.info("Considering position %d" % pos)
		if pos == 0:
			logger.info("Skipping initial position")
			continue
		if pos == suffix_start:
			logger.info("Skipping suffix start")
			continue

		# Heuristic, check no sync before considering
		# agents individually
		for this_agent in agents:
			wait_sets[this_agent][pos] = set()
		field_ts = construct_field_event_ts(agents, rhos, ts_tuple, tts, run, wait_sets, suffix_start)
		p = ts_times_buchi(field_ts, b)
		if empty_language(p):
			logger.info('Heuristic succeeded!')
			continue

		# Revert wait sets for this position to their default values
		logger.info('Heuristic did not help...')
		for this_agent in agents:
			wait_sets[this_agent][pos] = set(agents)-{this_agent}

		for this_agent in agents:
			for that_agent in set(agents)-{this_agent}:
				logger.info("Removing %s from %s's wait set", that_agent, this_agent)
				wait_sets[this_agent][pos].remove(that_agent)
				# Generate the field TS
				field_ts = construct_field_event_ts(agents, rhos, ts_tuple, tts, run, wait_sets, suffix_start)
				# Take the product
				p = ts_times_buchi(field_ts, b)
				# Check if the language of inverted formula is empty
				if empty_language(p):
					logger.info('Empty Language')
				else:
					logger.info('Non-empty language')
					# Revert change made to wait set of this_agent
					wait_sets[this_agent][pos].add(that_agent)

	return wait_sets
