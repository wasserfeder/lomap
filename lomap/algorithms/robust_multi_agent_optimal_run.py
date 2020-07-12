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

#from builtins import range
import sys
import traceback
import logging

from lomap.algorithms.product import ts_times_ts
from lomap.algorithms.optimal_run import optimal_run
from lomap.algorithms.sync_seq import compute_sync_seqs
from lomap.classes import Buchi
from lomap.classes import Timer

# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())


def pretty_print(agent_cnt, prefix, suffix):
    '''Pretty print the prefix and suffix_cycle on team_ts'''
    hdr_line_1 = ''
    hdr_line_2 = ''
    for i in range(0,agent_cnt):
        hdr_line_1 += 'Robot-{}'.format(i+1).ljust(20)
        hdr_line_2 += '-------'.ljust(20)
    logger.info(hdr_line_1)
    logger.info(hdr_line_2)

    logger.info('*** Prefix: ***')
    for s in prefix:
        line = ''
        for ss in s:
            line += '{}'.format(ss).ljust(20)
        logger.info(line)

    logger.info('*** Suffix: ***')
    for s in suffix:
        line = ''
        for ss in s:
            line += '{}'.format(ss).ljust(20)
        logger.info(line)

def robust_multi_agent_optimal_run(ts_tuple, rhos, formula, opt_prop):
    '''TODO:
    '''
    with Timer('Path Planning'):
        # Construct the team_ts
        team_ts = ts_times_ts(ts_tuple)
        # Find the optimal run and shortest prefix on team_ts
        try:
            prefix_length, prefix_on_team_ts, suffix_cycle_cost, \
               suffix_cycle_on_team_ts = optimal_run(team_ts, formula, opt_prop)
        except: # FIXME: seems like a hack
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            exit(1)
        # Pretty print the run
        pretty_print(len(ts_tuple), prefix_on_team_ts, suffix_cycle_on_team_ts)
        # Project the run on team_ts down to individual agents
        prefixes = []
        suffix_cycles = []
        for i in range(0, len(ts_tuple)):
            ts = ts_tuple[i]
            prefixes.append([x[i] for x in prefix_on_team_ts])
            suffix_cycles.append([x[i] for x in suffix_cycle_on_team_ts])
            complement_ts_and_run(ts, prefixes[i], suffix_cycles[i])
        logger.info('Prefixes: %s', prefixes)
        logger.info('Suffix Cycles: %s', suffix_cycles)

        # Construct the buchi for the negation of the formula
        b = Buchi()
        neg_formula = '! ({})'.format(formula)
        b.from_formula(neg_formula)
        #b.visualize()

    # Compute synchronization sequences
    with Timer('Sync Seq computation'):
        sync_seqs = compute_sync_seqs(ts_tuple, rhos, team_ts, b,
                                    prefix_on_team_ts, suffix_cycle_on_team_ts)
        logger.info('%s', sync_seqs)

    return (prefix_length, prefixes, suffix_cycle_cost, suffix_cycles)

def complement_ts_and_run(ts, prefix, suffix_cycle):
    '''TODO:
    '''

    traveling_states = [x for x in prefix + suffix_cycle if type(x)==tuple]

    if not traveling_states:
        return
    else:
        # sort the tuples in the list
        traveling_states.sort()
        done = set()
        for s in traveling_states:
            # src, dest of this traveling state
            src = s[0]
            dest = s[1]

            # Skip if we already covered src->dest
            if (src, dest) in done:
                continue

            # list of traveling states between src -> dest
            s_list = [x for x in traveling_states if x[0] == s[0] and x[1] == s[1]]

            # keep orig weight and control
            orig_weight = ts.g[src][dest][0]['weight']
            orig_control = ts.g[src][dest][0]['control']

            # remove the src->dest edge
            ts.g.remove_edge(src,dest)

            # add edges and traveling states as required
            prev = src
            prev_time = 0
            for t in s_list:
                weight = t[2] - prev_time
                ts.g.add_edge(prev, t, 0, {'weight': weight, 'control': orig_control})
                prev = t
                prev_time = t[2]
            weight = orig_weight - prev_time
            ts.g.add_edge(prev, dest, 0, {'weight': weight, 'control': orig_control})

            # Complement prefix and suffix by inserting s_list between any src, dest sequence
            #logger.debug("src: %s, dest: %s" % (src, dest))
            #logger.debug("s-list: %s" % s_list)
            #logger.debug("p_before: %s" % prefix)
            for i in range(0,len(prefix)-1):
                if (prefix[i] == src and prefix[i+1] == dest):
                    prefix[i+1:i+1] = s_list
            #logger.debug("p_after: %s" % prefix)

            #logger.debug("s_before: %s" % suffix_cycle)
            for i in range(0,len(suffix_cycle)-1):
                if (suffix_cycle[i] == src and suffix_cycle[i+1] == dest):
                    suffix_cycle[i+1:i+1] = s_list
            #logger.debug("s_after: %s" % suffix_cycle)

            # mark this transition as done
            done.add((src,dest))

# Notes
# -----
# import pickle
# # Pickle to save time
# f = open('state.pickle', 'w')
# pickle.dump((ts_tuple, team_ts, b, prefix_on_team_ts, suffix_cycle_on_team_ts, prefix_length, prefixes, suffix_cycle_cost, suffix_cycles), f)
# exit(0)
# # Load the pickle
#    f = open('state.pickle', 'r')
#    ts_tuple, team_ts, b, prefix_on_team_ts, suffix_cycle_on_team_ts = pickle.load(f)
