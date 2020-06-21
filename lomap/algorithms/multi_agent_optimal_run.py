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

import logging

from lomap.algorithms.product import ts_times_ts
from lomap.algorithms.optimal_run import optimal_run

# Logger configuration
logger = logging.getLogger(__name__)


def pretty_print(agent_cnt, prefix, suffix):
	import string
	# Pretty print the prefix and suffix_cycle on team_ts
	hdr_line_1 = ''
	hdr_line_2 = ''
	for i in range(0,agent_cnt):
		hdr_line_1 += string.ljust('Robot-%d' % (i+1), 20)
		hdr_line_2 += string.ljust('-------', 20)
	logger.info(hdr_line_1)
	logger.info(hdr_line_2)

	logger.info('*** Prefix: ***')
	for s in prefix:
		line = ''
		for ss in s:
			line += string.ljust('%s' % (ss,), 20)
		logger.info(line)

	logger.info('*** Suffix: ***')
	for s in suffix:
		line = ''
		for ss in s:
			line += string.ljust('%s' % (ss,), 20)
		logger.info(line)

def multi_agent_optimal_run(ts_tuple, formula, opt_prop):
	# Construct the team_ts
	team_ts = ts_times_ts(ts_tuple)
	# Find the optimal run and shortest prefix on team_ts
	prefix_length, prefix_on_team_ts, suffix_cycle_cost, suffix_cycle_on_team_ts = optimal_run(team_ts, formula, opt_prop)
	# Pretty print the run
	pretty_print(len(ts_tuple), prefix_on_team_ts, suffix_cycle_on_team_ts)
	# Project the run on team_ts down to individual agents
	prefixes = []
	suffix_cycles = []
	for i in range(0, len(ts_tuple)):
		ts = ts_tuple[i]
		prefixes.append([x for x in [x[i] if x[i] in ts.g.node else None for x in prefix_on_team_ts] if x != None])
		suffix_cycles.append([x for x in [x[i] if x[i] in ts.g.node else None for x in suffix_cycle_on_team_ts] if x!= None])

	return (prefix_length, prefixes, suffix_cycle_cost, suffix_cycles)
