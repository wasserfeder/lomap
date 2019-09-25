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
Construct the field event transition system for a given run of a team of agents.

Given a team transition system modeling a team of agents, a run on this team
transition system, wait sets of the agents and lower and upper deviation values
of the agents, this module constructs the field event transition system that 
captures all possible executions of the run by the agents in the field.
"""
from __future__ import print_function
from builtins import range
import itertools as it
from collections import namedtuple
import logging

from ..classes import Interval
from ..classes import Ts

# Logger configuration
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Classes derived from namedtuple
Event = namedtuple('Event', ['agent', 'pos'])
Realization = namedtuple('Realization', ['actual', 'assumed', 'postponed'])

def compute_agent_pos_dep_iv(wait_sets, rhos, dep_ivs, time_to_go, run_pos, agent_no):
	"""
	Compute the departure interval for an agent for a given position of a run.

	Parameters
	----------
	wait_sets: 2-D array of sets.
		wait_sets[i][j] gives the agents that agent i waits at the j^th position of 
		the run.

	rhos: 2-D array of floats.
		rhos[i].upper and rhos[i].lower are the upper and lower lower deviation values of
		agent i, respectively.

	dep_ivs: 2-D array of interval objects.
		dep_ivs[i][j] is the interval that agent i can depart from the j^th position
		of the run. 

	time_to_go: list of floats.
		time_to_go[i] gives the nominal time it takes to reach from i-1 to i
		position of the run. Times are given for the run on the team transition system,
		thus we have a single time_to_go list.

	run_pos: Integer
		Position of the run to consider.

	agent_no: Integer
		Agent to consider.

	Returns
	-------
	agent_pos_dep_iv: Interval object
		Interval that gives the earliest and latest times that agent agent_no can
		depart position run_pos of the run given its wait sets.
	"""

	if run_pos == 0:
		# Time is 0 at the beginning of the run (robots start sync'ed)
		return Interval(0, 0, True, True)

	# Agents that this agent has to wait for (this includes itself)
	agents_to_wait = wait_sets[agent_no][run_pos] | {agent_no}

	# Earliest and latest departure times
	earliest_dep = 0
	latest_dep = 0
	for i in agents_to_wait:
		prev_earliest_dep = dep_ivs[i][run_pos-1].start
		prev_latest_dep = dep_ivs[i][run_pos-1].end
		min_time_to_go = time_to_go[run_pos] * rhos[i].lower
		max_time_to_go = time_to_go[run_pos] * rhos[i].upper
		this_earliest_dep = prev_earliest_dep + min_time_to_go
		this_latest_dep = prev_latest_dep + max_time_to_go
		earliest_dep = max(earliest_dep, this_earliest_dep)
		latest_dep = max(latest_dep, this_latest_dep)

	# Construct the departure interval of this agent for this position
	agent_pos_dep_iv = Interval(earliest_dep, latest_dep, True, True)

	return agent_pos_dep_iv

def compute_departure_ivs(agents, run, tts, wait_sets, rhos):
	"""
	Compute the departure intervals for all agents for all positions of the run.

	Parameters
	----------
	agents: A list of integers.

	run: A list of tuples.
		Length of the list is the length of the run, and the i^th tuple run[i]
		gives the state of the team at the i^th position of the run. Length of
		this tuple is equal to the number of the agents and the j^th element
		run[i][j] of this tuple gives the state of the j^th agent at the i^th
		position of the run.

	tts: A transition system object.
		The team transition system that captures the joint asynchronous behavior
		of the agents.

	wait_sets: 2-D array of sets.
		wait_sets[i][j] gives the agents that agent i waits at the j^th position of 
		the run.

	rhos: Array of Rho objects.
		rhos[i].lower and rhos[i].upper are lower and upper deviation values of
		agent i, respectively.

	Returns
	-------
	dep_ivs: 2-D array of intervals.
		dep_ivs[i][j] gives the interval that agent i can depart from the j^th
		position of the run.
	"""

	# Time to reach each pos in the run from the prev pos
	time_to_go = [0] + [tts.g[run[ii-1]][run[ii]][0]['weight'] for ii in range(1,len(run))]
	# Planned times to reach each pos in the run
	planned_times = [0]
	for i in time_to_go[1:]:
		planned_times.append(planned_times[-1]+i)

	# Departure intervals for each position of each agent given rhos and wait-sets
	# These are actually intervals of satisfactions of propositions
	dep_ivs = [[None]*len(run) for ii in agents]
	for pos in range(0,len(run)):
		for agent_no in agents:
			dep_ivs[agent_no][pos] = compute_agent_pos_dep_iv(wait_sets, rhos, dep_ivs, time_to_go, pos, agent_no)
			#logger.debug('agent %d, pos %d: %s' % (agent_no, pos, dep_ivs[agent_no][pos]))

	return dep_ivs

def compute_timeline(agents, ts_tuple, dep_ivs):
	"""
	Compute the timeline of events that can occur in the field.

	Given the departure intervals of the agents, this function 
	computes a common timeline of events that captures all possible 
	occurances of events in the field.

	Parameters
	----------
	agents: A list of integers.

	ts_tuple: Tuple of transition system objects.
		ts_tuple[i] corresponds to the transition system of agent i.

	dep_ivs: 2-D array of interval objects.
		dep_ivs[i][j] gives the earliest lates departure times of agent
		i from position j of the run.

	Returns
	-------
	timeline: A dictionary of sets of tuples keyed by interval objects.
		An event is a tuple of the form (agent_no, run_pos).
		timeline is a dictionary of sets of events keyed by intervals
		such that timeline[Interval(0,1)] gives the set of events that
		can occur in Interval(0,1), if such an interval is defined.
	"""

	# Construct a dictionary of sets of events keyed by intervals.
	timeline = dict()

	# An event is a tuple of the form (agent_no, run_pos).
	# timeline[Interval(...)] gives the set of events that can occur
	# in Interval(...), if such an interval is defined.

	# Consider all agents
	for agent_no in agents:

		# Consider all positions
		for run_pos in range(0, len(dep_ivs[agent_no])):

			# The queue of intervals to be projected
			# We use a queue as we may break down old intervals
			# if they intersect with the new ones partially.
			projection_queue = [dep_ivs[agent_no][run_pos]]

			for new_iv in projection_queue:

				# Flag to remember if we intersect with anything
				intersected = False
				new_iv_events = {Event(agent=agent_no, pos=run_pos)}

				# Consider all previously discovered intervals
				for old_iv in list(timeline.keys()):
					# See if new_iv intersects with any old_iv
					old_iv_events = timeline[old_iv]
					int_iv = old_iv & new_iv

					if int_iv: 
						# We have a valid intersection
						intersected = True
						# Create a new iv for intersection (or update)
						timeline[int_iv] = old_iv_events | new_iv_events
						# Find non-intersecting parts of old_iv and new_iv
						old_diff = old_iv.difference(int_iv)
						new_diff = new_iv.difference(int_iv)
						if old_diff:
							# Break old_iv as needed
							for old_iv_frag in old_diff:
								timeline[old_iv_frag] = set([ii for ii in old_iv_events])
							# Remove previous old_iv entry
							del timeline[old_iv]
						# Break new_iv as needed
						for new_iv_frag in new_diff:
							# add to queue, as this fragment may intersect with others
							projection_queue.append(new_iv_frag)

						# Finished processing this part of new_iv.
						# As intervals in the timeline are disjoint no need 
						# to consider further entries.
						break

				if not intersected:
					# new_iv did not intersect w/ any of the old_ivs
					timeline[new_iv] = new_iv_events

	return timeline

def generate_event_seq(agents, cur_events, prev_events, next_events, iv_len):
	"""
	Generate all possible sequences of events that can occur in this interval.

	Parameters
	----------
	agents: List of integers
		This list must start from 0 and monotonically increase to n-1 for n agents.

	cur_events: Set of tuples
		Elements of the set events_this are tuples of the form (i,j). Each (i,j) is an
		event that captures the departure of agent i from the j^th position of the run.

	prev_events: Set of tuples
		Subset of events that can occur both in this interval and the previous one.

	next_events: Set of tuples
		Subset of events that can occur both in this interval and the next one.

	Returns
	-------
	A tuple (postponed_events, assumed_events, event_seq) that gives postponed and assumed
	events for a given event sequence.
	"""

	done = set()

	# Extract agent specific and sorted past, current, and future event lists
	agents_prev_events = [sorted([ee.pos for ee in prev_events if ee.agent==aa]) for aa in agents]
	agents_cur_events = [sorted([ee.pos for ee in cur_events if ee.agent==aa]) for aa in agents]
	agents_next_events = [sorted([ee.pos for ee in next_events if ee.agent==aa]) for aa in agents]

	# Compute which events can be assumed or postponed for each agent
	# e.g. if agents_past = [[20,21],[20,21]], agents_assumed = [[[],[20],[20,21]],[[],[20],[20,21]]]
	# ii is in [0, 1, ..., len(agents_prev_events[aa])]
	assumable_events = [[agents_prev_events[aa][:ii] for ii in range(0,len(agents_prev_events[aa])+1)] for aa in agents]
	# e.g. if agents_future = [[20,21],[20,21]], agents_postponed = [[[],[21],[20,21]],[[],[21],[20,21]]]
	# ii is in [len(agents_next_events[aa]), ... , 1, 0] 
	postponable_events = [[agents_next_events[aa][ii:] for ii in range(len(agents_next_events[aa]),-1,-1)] for aa in agents]

	# Compute all possible realizations for all agents
	realizations = [[] for aa in agents]
	for a in agents:
		# Consider all possible combinations of assumed and postponed events
		for assumed_events, postponed_events in it.product(assumable_events[a], postponable_events[a]):
			# Consider only disjoint combinations of assumed/postponed events
			if any([assumed_events[ii] == postponed_events[jj] for ii in range(0,len(assumed_events)) for jj in range(0,len(postponed_events))]):
				continue
			# Obtain actual list of events of this realization after filtering out
			# assumed and postponed events.
			actual_events = [ee for ee in agents_cur_events[a] if (ee not in assumed_events and ee not in postponed_events)]
			# Skip empty event_lists
			if not actual_events:
				continue
			realizations[a].append(Realization(tuple(actual_events), tuple(assumed_events), tuple(postponed_events)))

	# Consider all possible combinations of realizations
	for real_tuple in it.product(*realizations):
		# Number of events of each agent and total number of events
		agent_event_cnts = [len(real_tuple[aa].actual) for aa in agents]
		total_event_cnt = sum(agent_event_cnts)

		if iv_len > 0:
			# Get the place at which each event of each agent occurs
			# agent_pos_lists[0]=[1,3,4] means events of agent 0 occur as the 
			# first, third, and fourth event of the interval
			agent_pos_lists = [it.combinations(list(range(0,total_event_cnt)),agent_event_cnts[aa]) for aa in agents]
		else:
			# Get the pos lists for point interval -- all events occur simultaneously
			agent_pos_lists = [[[0] * agent_event_cnts[aa]] for aa in agents]

		for pos_tuple in it.product(*agent_pos_lists):
			# pos_tuple is a tuple of positions such that
			# pos_tuple[a] gives the positions at which events
			# of the a^th agent occurs

			# Initialize the template event_seq, we'll filter out Nones later
			event_seq = [tuple() for ii in range(0,total_event_cnt)]
			for a in agents:
				for i in range(0,agent_event_cnts[a]):
					# i^th actual event of agent a that occurs in this interval
					event = Event(a, real_tuple[a].actual[i])
					# The position at which this event occurs in this interval
					pos = pos_tuple[a][i]
					# Update the tuple of events that occur at this pos
					event_seq[pos] = event_seq[pos] + (event,)

			# Filter out empty tuples to obtain the final event_seq
			event_seq = [tt for tt in event_seq if tt]
			if tuple(event_seq) not in done:
				done.add(tuple(event_seq))
				#print "Possible event seq: %s" % event_seq
				assumed_seq = [Event(aa,ee) for aa in agents for ee in real_tuple[aa].assumed]
				postponed_seq = [Event(aa,ee) for aa in agents for ee in real_tuple[aa].postponed]
				#logger.debug('Yielding assumed:%s, event_seq:%s, postponed:%s', assumed_seq, event_seq, postponed_seq)
				yield (tuple(assumed_seq), tuple(event_seq), tuple(postponed_seq))

def wait_set_checks_fail(agents, wait_sets, assumed, event_seq, latest_events):
	"""
	Check if whether a given event_seq violates the wait sets of the agents.

	Parameters
	----------
	agents: List of integers.
		This list gives the index of each agent. agents=range(0,3) if we have
		3 agents, i.e. agent 0...2.

	wait_sets: 2-D array of sets.
		wait_sets[i][j] gives the agents that agent i waits at the j^th position of 
		the run.

	assumed: List of tuples.
		An event is a tuple of the form (agent_no, run_pos). Elements of the assumed
		list gives the sequence of events that are assumed to occur before the 
		events in event_seq.

	event_seq: List of tuples.
		The sequence of events that occur in this interval.

	latest_events: List of integers.
		The last events of the agents that have occured for sure. latest_events[i] gives
		the latest event of agent i.

	Returns
	-------
	True if event_seq violates the constraints of the wait_sets. False, otherwise.

	"""

	# Update the latest events of each agent according to assumed events
	latest_events_actual = [event for event in latest_events]
	for agent,event in assumed:
		assert(event > latest_events_actual[agent])
		latest_events_actual[agent] = event

	# Preserve the order imposed by the wait-sets
	# Consider all pairs of agents
	for agent_1, agent_2 in [tt for tt in it.product(agents, repeat=2) if tt[0] != tt[1]]:
		# Start from last reached positions
		agent_1_pos, agent_2_pos = latest_events_actual[agent_1], latest_events_actual[agent_2]
		# Process the events in the event sequence
		for event_tuple in event_seq:
			# Update positions of the agents
			for ee in event_tuple:
				if ee.agent == agent_1:
					agent_1_pos = ee.pos
				if ee.agent == agent_2:
					agent_2_pos = ee.pos

			# Check if this instant in the event_seq violates any of the wait sets
			if agent_2 in wait_sets[agent_1][agent_1_pos] and agent_1_pos > agent_2_pos:
				#logger.debug('Invalid event seq1 %s: %s waits for %s at pos %s [%s-%s]' % (event_seq, agent_1, agent_2, agent_1_pos, event, agent_2_pos))
				return True
			if agent_1 in wait_sets[agent_2][agent_2_pos] and agent_2_pos > agent_1_pos:
				#logger.debug('Invalid event seq2 %s: %s waits for %s at pos %s [%s-%s]' % (event_seq, agent_2, agent_1, agent_2_pos, event, agent_1_pos))
				return True

	return False

def start_states_of_event_seq(agents, event_seq, assumed_events, latest_events, field_ts):
	"""
	Figure out the states at which some given event sequence can occur.

	Parameters
	----------
	agents: List of integers
		This list must start from 0 and monotonically increase to n-1 for n agents.

	event_seq: List of tuples.
		An event is a tuple of the form (agent_no, run_pos). This list gives the
		sequence of events that occur in this interval.

	assumed_events: List of tuples.
		The sequence of events that are assumed to occur before the events in event_seq.

	latest_events: List of integers.
		The last events of the agents that have occured for sure. latest_events[i] gives
		the latest event of agent i.

	field_ts: A transition system object.
		The field event transition system of the team.

	Returns
	-------
	start_states: A list of tuple of tuples.
		This list gives all possible states from which this event sequence can start.

	"""

	# Update the latest events of each agent according to assumed events
	latest_events_actual = [ee for ee in latest_events]
	for agent,event in assumed_events:
		assert(event > latest_events_actual[agent])
		latest_events_actual[agent] = event

	# Consider every 0,...,n combinations of n agents to cover cases where
	# some of them may be in traveling while others are at a state
	start_states = []
	for traveling_agents in it.chain(*[it.combinations(agents,n) for n in range(0, len(agents)+1)]):
		new_start_state = [ee for ee in latest_events_actual]
		for agent in traveling_agents:
			# Find out what the state would be if the agents in traveling_agents were traveling
			new_start_state[agent] = (new_start_state[agent],new_start_state[agent]+1)
		# Add this candidate to our list
		start_states.append(tuple(new_start_state))

	# Remove those states that are not in field event transition system
	# E.g. Event (1,1) might occur at [(0, 0), ((0, 1), 0), (0, (0, 1)), ((0, 1), (0, 1))]
	# But, since we only have (0,0), we ignore other possibilities
	start_states = [ss for ss in start_states if ss in field_ts.g]

	return start_states

def valid_event_seqs(agents, timeline, wait_sets, field_ts):
	"""
	Generates all possible event sequences that are valid in the sense that
		1- Events that belong to an agent monotonically increase
		2- No two different events that belong to a single agent occur simultaneously
		3- Wait sets of the agents are honored

	Parameters
	----------
	agents: List of integers
		This list must start from 0 and monotonically increase to n-1 for n agents.

	timeline: A dictionary of sets of tuples keyed by interval objects.
		An event is a tuple of the form (agent_no, run_pos).
		timeline is a dictionary of sets of events keyed by intervals
		such that timeline[Interval(0,1)] gives the set of events that
		can occur in Interval(0,1), if such an interval is defined.

	wait_sets: 2-D array of sets.
		wait_sets[i][j] gives the agents that agent i waits at the j^th position of 
		the run.

	field_ts: A transition system object.
		The field event transition system of the team.

	Returns
	-------
	A tuple (start_states, event_seq) where event_seq is a list of tuples and each
		tuple is either a single event or a tuple of events, and start_states is the
		states of field_ts at which this event_seq can start occuring.

	"""

	# Process the intervals in the timeline
	ivs = sorted(timeline.keys())
	latest_events = [0 for aa in agents]
	for ii in range(0, len(ivs)):
		# Events of this, prev and next intervals
		events_cur = timeline[ivs[ii]]
		events_prev = timeline[ivs[ii-1]] if ii > 0 else set()
		# Since everything restarts at the next suffix cycle,
		# no events are shared if the next iv is in the next suffix cycle
		# generate_field_ts ties up remaining states to suffix_start state
		events_next = timeline[ivs[ii+1]] if (ii+1) < len(ivs) else set()

		# Shared past and future events
		events_cur_and_prev = (events_cur & events_prev)
		events_cur_and_next = (events_cur & events_next)

		# Consider all event sequences that can occur in this interval
		for (assumed_seq, cur_seq, postponed_seq) in generate_event_seq(agents, events_cur, events_cur_and_prev, events_cur_and_next, ivs[ii].length()):
			# Filter out those that violate the constraints of the wait sets
			if wait_set_checks_fail(agents, wait_sets, assumed_seq, cur_seq, latest_events):
				continue
			# Compute possible start states of this event sequence
			start_states = start_states_of_event_seq(agents, cur_seq, assumed_seq, latest_events, field_ts)
			yield (start_states, cur_seq)
		
		# Update the most recent event of each agent that has occured for sure
		for event in (events_cur - events_next):
			if(event.pos > latest_events[event.agent]):
				latest_events[event.agent] = event.pos


def props_of_this_event(event, ts_tuple, run):
	"""
	Find the set of propositions that correspond to an event.

	Parameters
	-----------
	event: A tuple
		An event is a tuple of the form (agent_no, run_pos). This argument
		can either be a tuple of events (simultaneous events) or a tuple of
		integers (single event).

	ts_tuple: A tuple of transition system objects
		In this tuple ts_tuple[i] corresponds to the transition system that
		models agent i.

	run: A list of tuples.
		A run on the team transition system. Length of the list is the length
		of the run, and the i^th tuple run[i] gives the state of the team at
		the i^th position of the run. Length of this tuple is equal to the number 
		of the agents and the j^th element run[i][j] of this tuple gives the
		state of the j^th agent at the i^th position of the run.

	Returns
	-------
	props: The set of propositions.

	"""

	# Construct a serialized list of events
	events_ser = [ee for ee in event]

	# Construct the set of propositions of the states of the agents
	props = set()
	for e in events_ser:
		# NOTE: run[pos][agent] = state_label
		state = run[e.pos][e.agent]
		props |= ts_tuple[e.agent].g.node[state].get('prop',set())

	return props

def next_state_after_event(agents, event, prev_state, max_pos, suffix_start):
	"""
	Get the next state in the field event transition system after event
	occurs at prev_state.

	Parameters
	----------
	event: A tuple
		An event is a tuple of the form (agent_no, run_pos). This argument
		can either be a tuple of events (simultaneous events) or a tuple of
		integers (single event).

	prev_state: A tuple
		Previous state of the field event transition system. Elements can be
		integers for events that have just occured or tuples for traveling
		states.

	Returns
	-------
	next_state: A tuple giving the next state of field_ts

	"""

	next_state = [ss for ss in prev_state]
	changed_agents = set()

	# Register new positions of all agents
	for e in event:
		changed_agents.add(e.agent)
		next_state[e.agent] = e.pos

	# Agents can't just wait at some state
	# change states of remaining agents to appropriate traveling states
	for agent in agents:
		if agent not in changed_agents and type(next_state[agent]) != tuple:
			if (next_state[agent]+1) <= max_pos:
				next_state[agent] = (next_state[agent],next_state[agent]+1)
			else:
				# Handle the case we wrap to suffix start
				next_state[agent] = (next_state[agent],suffix_start)

	return tuple(next_state)


def construct_field_event_ts(agents, rhos, ts_tuple, tts, run, wait_sets, suffix_start):
	"""
	Construct the field event transition system for a given run of a team of agents.

	The resulting field event transition system meets the following criteria:
	1. Propositions that belong to the same agent occur one by one sequentially
		and are not repeated.
	2. Order of propositions obey given wait_sets.
	
	Parameters
	----------
	timeline: A dictionary of sets of tuples keyed by interval objects.
		An event is a tuple of the form (agent_no, run_pos).
		timeline is a dictionary of sets of events keyed by intervals
		such that timeline[Interval(0,1)] gives the set of events that
		can occur in Interval(0,1), if such an interval is defined.

	ts_tuple: Tuple of transition system objects.
		ts_tuple[i] corresponds to the transition system of agent i.

	wait_sets: 2-D array of sets.
		wait_sets[i][j] gives the agents that agent i waits at the j^th position of 
		the run.

	run: A list of tuples.
		Length of the list is the length of the run, and the i^th tuple run[i]
		gives the state of the team at the i^th position of the run. Length of
		this tuple is equal to the number of the agents and the j^th element
		run[i][j] of this tuple gives the state of the j^th agent at the i^th
		position of the run. For an actual run in prefix-suffix form,
		run = prefix[0:-1] + suffix[0:-1].

	suffix_start: Integer
		run[suffix_start] is start of the suffix cycle.

	Returns
	-------
	field_ts: A transition system object
		This transition system captures all possible executions of the run by
		the agents in the field and has corresponding propositions defined at
		its states.
	"""

	# Compute the departure intervals for each agent for each position
	# of the run for the given rho values
	dep_ivs = compute_departure_ivs(agents, run, tts, wait_sets, rhos)
	# Compute the timeline of events corresponding to these departure 
	# intervals

	assert len(ts_tuple) == len(dep_ivs) == len(agents)

	timeline = compute_timeline(agents, ts_tuple, dep_ivs)

	# Create the ts
	field_ts = Ts()
	field_ts.name = 'Field event TS of ' + ', '.join([ts.name for ts in ts_tuple])

	# Create the generator object
	valid_sequences = valid_event_seqs(agents, timeline, wait_sets, field_ts)

	# First event we get is the initial state of field_ts
	_,event_seq = next(valid_sequences)
	assert(len(event_seq) == 1 and len(event_seq[0]) == len(agents))
	init_state = tuple([ee.pos for ee in event_seq[0]])
	assert init_state == tuple([0 for ii in agents])
	field_ts.g.add_node(init_state)
	field_ts.g.node[init_state]['prop'] = props_of_this_event(event_seq[0], ts_tuple, run)
	field_ts.init[init_state] = 1

	# Consider all valid event sequences
	for start_states,event_seq in valid_sequences:
		# Consider all possible starting states
		for state in start_states:
			prev_state = state
			# Create states and transitions for each event in the sequence
			for event in event_seq:
				next_state = next_state_after_event(agents, event, prev_state, len(run)-1, suffix_start)
				if next_state not in field_ts.g:
					props = props_of_this_event(event, ts_tuple, run)
					field_ts.g.add_node(next_state)
					field_ts.g.node[next_state]['prop'] = props
				if next_state not in field_ts.g[prev_state]:
					field_ts.g.add_edge(prev_state, next_state, control = event, weight = 0)
				prev_state = next_state

	# Tie the remaining states to the start of the suffix
	for state in field_ts.g.nodes_iter():
		if not field_ts.g[state]:
			logger.debug('%s left alone', state)
			suffix_start_state = tuple([suffix_start for ii in agents])
			assert(suffix_start_state in field_ts.g)
			return_control = tuple([(ii,suffix_start) for ii in agents])
			field_ts.g.add_edge(state, suffix_start_state, control = return_control, weight = 0)

	#logger.debug('Nodes: %d, edges: %d', len(field_ts.g.nodes()), len(field_ts.g.edges()))

	return field_ts

def _clean_timeline(timeline):

	# TODO: Do we need/want to clean-up of intervals?
        # Resulting field_ts's should be the same if we don't need to.
	ivs = sorted(timeline.keys())
	ivs_to_delete = []

	for ii in range(0, len(ivs)):
		this_events = timeline[ivs[ii]]
		if ii == 0:
			prev_events = set()
			next_events = timeline[ivs[ii+1]]
		elif ii == len(ivs)-1:
			prev_events = timeline[ivs[ii-1]]
			next_events = set()
		else:
			prev_events = timeline[ivs[ii-1]]
			next_events = timeline[ivs[ii+1]]
		if this_events.issubset(prev_events) or this_events.issubset(next_events):
			ivs_to_delete.append(ivs[ii])

	for iv in ivs_to_delete:
		del timeline[iv]

#
# Notes
# -----
# - Can change all dijkstra's to bidirectional dijkstra for better performance.
# - remove planned times from field_event_ts
#
# Useful code snippets
# --------------------
#field_ts.visualize()
#queue = []
#queue.append((0,0))
#done = set()
#while queue:
#	# Append children to the queue
#	parent = queue[0]
#	queue = queue + sorted(set(field_ts.g[parent].keys())-done)
#	if parent not in done:
#		for child in sorted(field_ts.g[parent].keys()):
#			logger.debug('%s -%s-> %s', parent, field_ts.g[parent][child][0]['action'],child)
#	queue.remove(parent)
#	done.add(parent)
#
#for parent, child in nx.bfs_edges(field_ts.g, (0,0)):
#	logger.debug('%s -%s-> %s', parent, field_ts.g[parent][child][0]['action'],child)
#
#print nx.info(field_ts.g)
