# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
#               2016-2017  Cristian-Ioan Vasile (cvasile@mit.edu)
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

import itertools as it
import operator as op
import logging
from collections import deque

from classes import Fsa, Markov, Model, Ts


# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

#TODO: make independent of graph type
__all__ = ['ts_times_ts', 'ts_times_buchi', 'ts_times_fsa',
           'markov_times_markov', 'markov_times_fsa',
           'fsa_times_fsa', 'no_data']

def no_data(*args, **kwargs):
    '''Returns an empty dictionary.'''
    return dict()

def get_default_state_data(state, **kwargs):
    '''Returns the default data to store for a state of a product.

    Parameters
    ----------
    state: hashable
        A state.

    Returns
    -------
        dictionary containing the data to be stored.
    '''
    prop = kwargs.get('prop', None)
    return {'prop': prop, 'label':"%s\\n%s" % (state, list(prop))}

def get_default_transtion_data(current_state, next_state, **kwargs):
    '''Returns the default data to store for a transition of a product.

    Parameters
    ----------
    current_state, next_state: hashable
        The endpoint states of the transition.

    Returns
    -------
        Dictionary containing the data to be stored.
    '''
    return {'weight': kwargs.get('weight', None),
            'control': kwargs.get('control', None)}

def ts_times_fsa(ts, fsa, from_current=False,
                 get_state_data=get_default_state_data,
                 get_transition_data=get_default_transtion_data):
    '''Computes the product automaton between a transition system and an FSA.

    Parameters
    ----------
    ts: LOMAP transition system

    fsa: LOMAP deterministic finite state automaton

    from_current: bool, optional (default: False)
        Indicates whether the product automaton should be constructed starting
        from the current TS and FSA states. 

    get_state_data: function, optional (default: get_default_state_data)
        Returns the data to be saved for a state of the product. The function
        takes the state as a mandatory argument, and optional keyword arguments.

    get_transition_data : function, optional
        (default: get_default_transition_data)
        Returns the data to be saved for a transition of the product. The
        function takes the two endpoint states as mandatory arguments, and
        optional keyword arguments.

    Returns
    -------
    product_model : LOMAP Model

    Notes
    -----
    The procedure supports only a single current state for construction with
    the from_currrent option set. The current state is retrieved from the ts
    and fsa.

    TODO
    ----
    Add regression tests.
    Add debugging logging.
    '''

    # Create the product_model
    product_model = Model()
    if from_current:
        product_model.init[(ts.current, fsa.current)] = 1
    else:
        # Iterate over initial states of the TS
        for init_ts in ts.init:
            init_prop = ts.g.node[init_ts].get('prop',set())
            # Iterate over the initial states of the FSA
            for init_fsa in fsa.init:
                # Add the initial states to the graph and mark them as initial
                act_init_fsa = fsa.next_state_of_fsa(init_fsa, init_prop)
                if act_init_fsa is not None:
                    init_state = (init_ts, act_init_fsa)
                    product_model.init[init_state] = 1
                    init_state_data = get_state_data(init_state, prop=init_prop,
                                                     ts=ts, fsa=fsa)
                    product_model.g.add_node(init_state, **init_state_data)
                    if act_init_fsa in fsa.final:
                        product_model.final.add(init_state)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    while stack:
        cur_state = stack.pop()
        ts_state, fsa_state = cur_state

        for ts_next_state, weight, control in ts.next_states_of_wts(ts_state,
                                                     traveling_states=False):
            ts_next_prop = ts.g.node[ts_next_state].get('prop',set())
            fsa_next_state = fsa.next_state_of_fsa(fsa_state, ts_next_prop)
            if fsa_next_state is not None:
                next_state = (ts_next_state, fsa_next_state)
                if next_state not in product_model.g:
                    next_prop = ts.g.node[ts_next_state].get('prop',set())
                    # Add the new state
                    next_state_data = get_state_data(next_state, prop=next_prop,
                                                     ts=ts, fsa=fsa)
                    product_model.g.add_node(next_state, **next_state_data)
                    # Add transition w/ data
                    transition_data = get_transition_data(cur_state, next_state,
                                weight=weight, control=control, ts=ts, fsa=fsa)
                    product_model.g.add_edge(cur_state, next_state,
                                             **transition_data)
                    # Mark as final if final in fsa
                    if fsa_next_state in fsa.final:
                        product_model.final.add(next_state)
                    # Continue search from next state
                    stack.append(next_state)
                elif next_state not in product_model.g[cur_state]:
                    # Add transition w/ data
                    transition_data = get_transition_data(cur_state, next_state,
                                weight=weight, control=control, ts=ts, fsa=fsa)
                    product_model.g.add_edge(cur_state, next_state,
                                             **transition_data)

    return product_model

def ts_times_buchi(ts, buchi):
    '''TODO: trim to 80 characters per line
    add option to choose what to save on the automaton's
    add description
    add regression tests
    add option to create from current state 
    '''

    # Create the product_model
    product_model = Model()

    # Iterate over initial states of the TS
    init_states = []
    for init_ts in ts.init.keys():
        init_prop = ts.g.node[init_ts].get('prop',set())
        # Iterate over the initial states of the FSA
        for init_buchi in buchi.init.keys():
            # Add the initial states to the graph and mark them as initial
            for act_init_buchi in buchi.next_states(init_buchi, init_prop):
                init_state = (init_ts, act_init_buchi)
                init_states.append(init_state)
                product_model.init[init_state] = 1
                product_model.g.add_node(init_state, {'prop':init_prop, 'label':"%s\\n%s" % (init_state,list(init_prop))})
                if act_init_buchi in buchi.final:
                    product_model.final.add(init_state)

    # Add all initial states to the stack
    stack = []
    for init_state in init_states:
        stack.append(init_state)

    # Consume the stack
    while(stack):
        cur_state = stack.pop()
        ts_state = cur_state[0]
        buchi_state = cur_state[1]

        for ts_next in ts.next_states_of_wts(ts_state, traveling_states = False):
            ts_next_state = ts_next[0]
            ts_next_prop = ts.g.node[ts_next_state].get('prop',set())
            weight = ts_next[1]
            control = ts_next[2]
            for buchi_next_state in buchi.next_states(buchi_state, ts_next_prop):
                next_state = (ts_next_state, buchi_next_state)
                #print "%s -%d-> %s" % (cur_state, weight, next_state)

                if(next_state not in product_model.g):
                    next_prop = ts.g.node[ts_next_state].get('prop',set())

                    # Add the new state
                    product_model.g.add_node(next_state, {'prop': next_prop, 'label': "%s\\n%s" % (next_state, list(next_prop))})

                    # Add transition w/ weight
                    product_model.g.add_edge(cur_state, next_state, attr_dict = {'weight':weight, 'control':control})

                    # Mark as final if final in buchi
                    if buchi_next_state in buchi.final:
                        product_model.final.add(next_state)

                    # Continue search from next state
                    stack.append(next_state)

                elif(next_state not in product_model.g[cur_state]):
                    product_model.g.add_edge(cur_state, next_state, attr_dict = {'weight':weight, 'control':control})

    return product_model

def ts_times_ts(ts_tuple):
    '''TODO: trim to 80 characters per line
    add option to choose what to save on the automaton's
    add description
    add regression tests
    add option to create from current state
    '''

    # Initial state label is the tuple of initial states' labels
    # NOTE: We assume deterministic TS (that's why we pick [0])
    assert all(map(lambda ts: True if len(ts.init) == 1 else False, ts_tuple))
    init_state = tuple(map(lambda ts: ts.init.keys()[0], ts_tuple))
    product_ts = Ts()
    product_ts.init[init_state] = 1

    # Props satisfied at init_state is the union of props
    # For each ts, get the prop of init state or empty set
    init_prop = map(lambda ts: ts.g.node[ts.init.keys()[0]].get('prop',set()), ts_tuple)

    # This makes each set in the list a new argument and takes the union
    init_prop = set.union(*init_prop)

    # Finally, add the state
    product_ts.g.add_node(init_state, {'prop':init_prop, 'label':"%s\\n%s" % (init_state,list(init_prop))})

    # Start depth first search from the initial state
    stack=[]
    stack.append(init_state)

    while(stack):
        cur_state = stack.pop()
        # Actual source states of traveling states
        source_state = tuple(map(lambda q: q[0] if type(q) == tuple else q, cur_state))
        # Time spent since actual source states
        time_spent = tuple(map(lambda q: q[2] if type(q) == tuple else 0, cur_state))

        # Iterate over all possible transitions
        for tran_tuple in it.product(*map(lambda t,q: t.next_states_of_wts(q), ts_tuple, cur_state)):
            # tran_tuple is a tuple of m-tuples (m: size of ts_tuple)

            # First element of each tuple: next_state
            # Second element of each tuple: time_left
            next_state = tuple([t[0] for t in tran_tuple])
            time_left = tuple([t[1] for t in tran_tuple])
            control = tuple([t[2] for t in tran_tuple])

            # Min time until next transition
            w_min = min(time_left)

            # Next state label. Singleton if transition taken, tuple if traveling state
            next_state = tuple(map(lambda ss, ns, tl, ts: (ss,ns,w_min+ts) if w_min < tl else ns, source_state, next_state, time_left, time_spent))

            # Add node if new
            if(next_state not in product_ts.g):
                # Props satisfied at next_state is the union of props
                # For each ts, get the prop of next state or empty set
                # Note: we use .get(ns, {}) as this might be a travelling state
                next_prop = map(lambda ts,ns: ts.g.node.get(ns,{}).get('prop',set()), ts_tuple, next_state)
                next_prop = set.union(*next_prop)

                # Add the new state
                product_ts.g.add_node(next_state, {'prop': next_prop, 'label': "%s\\n%s" % (next_state, list(next_prop))})

                # Add transition w/ weight
                product_ts.g.add_edge(cur_state, next_state, attr_dict = {'weight':w_min, 'control':control})
                #print "%s -%d-> %s (%s)" % (cur_state,w_min,next_state,next_prop)
                # Continue dfs from ns
                stack.append(next_state)

            # Add tran w/ weight if new
            elif(next_state not in product_ts.g[cur_state]):
                product_ts.g.add_edge(cur_state, next_state, attr_dict = {'weight':w_min, 'control':control})
                #print "%s -%d-> %s" % (cur_state,w_min,next_state)

    # Return ts_1 x ts_2 x ...
    return product_ts

def pfsa_default_transition_data(current_state, next_state, guard, bitmaps,
                                 fsa_tuple):
    '''Returns the default data to store for a transition of a product FSA.'''
    return {'weight': 0, 'input': bitmaps, 'guard' : guard, 'label': guard}

def fsa_times_fsa(fsa_tuple, from_current=False,
                  get_state_data=no_data,
                  get_transition_data=pfsa_default_transition_data):
    '''Computes the product FSA between a multiple FSAs.

    Parameters
    ----------
    fsa_tuple: iterable of LOMAP deterministic finite state automata

    from_current: bool, optional (default: False)
        Indicates whether the product automaton should be constructed starting
        from the FSAs' states.

    get_state_data: function, optional (default: get_default_state_data)
        Returns the data to be saved for a state of the product. The function
        takes the state as a mandatory argument, and optional keyword arguments.

    get_transition_data : function, optional
        (default: get_default_transition_data)
        Returns the data to be saved for a transition of the product. The
        function takes the two endpoint states as mandatory arguments, and
        optional keyword arguments.

    Returns
    -------
    product_fsa : LOMAP Fsa

    Notes
    -----
    The procedure supports only a single current state for construction with
    the from_currrent option set. The current state is retrieved from the FSAs.

    TODO
    ----
    Add regression tests.
    Add debugging logging.
    Add option to choose what to save on the automaton's states and transitions.
    '''
    if from_current:
        init_state = tuple([fsa.current_state for fsa in fsa_tuple])
    else:
        # assume deterministic FSAs
        assert all([len(fsa.init) == 1 for fsa in fsa_tuple])
        init_state = tuple([next(iter(fsa.init)) for fsa in fsa_tuple])

    # union of all atomic proposition sets 
    product_props = set.union(*[set(fsa.props) for fsa in fsa_tuple])
    product_fsa = Fsa(product_props, multi=False)
    product_fsa.init[init_state] = 1

    # Start depth first search from the initial state
    stack = deque([(init_state, it.product(*[fsa.g[s]
                            for s, fsa in it.izip(init_state, fsa_tuple)]))])

    while stack:
        current_state, neighbors = stack.popleft()
        state_data = get_state_data(current_state, fsa_tuple=fsa_tuple)
        product_fsa.g.add_node(current_state, **state_data)
        if all([s in fsa.final for s, fsa in it.izip(current_state,
                                                     fsa_tuple)]):
            product_fsa.final.add(current_state)
        # Iterate over all possible transitions
        for next_state in neighbors:
            guard = [fsa.g[u][v]['guard']
                     for u, v, fsa in it.izip(current_state, next_state,
                                              fsa_tuple)]
            guard = '({})'.format(' ) & ( '.join(guard))
            bitmaps = product_fsa.get_guard_bitmap(guard)
            if bitmaps:
                if next_state not in product_fsa.g:
                    stack.append((next_state, it.product(*[fsa.g[s]
                               for s, fsa in it.izip(next_state, fsa_tuple)])))
                transition_data = get_transition_data(current_state, next_state,
                              guard=guard, bitmaps=bitmaps, fsa_tuple=fsa_tuple)
                product_fsa.g.add_edge(current_state, next_state,
                                       **transition_data)
    # Return fsa_1 x fsa_2 x ...
    return product_fsa

def flatten_tuple(t):
    '''TODO: add description
    add regression tests 
    '''
    flat_tuple = ()
    for item in t:
        if isinstance(item, tuple):
            flat_tuple += item
        else:
            flat_tuple += (item,)
    return flat_tuple

def markov_times_markov(markov_tuple):
    '''TODO: trim to 80 characters per line
    add option to choose what to save on the automaton's
    add description
    add regression tests
    change lambda function to functions in operator package
    add option to create from current state
    '''

    # This results in an Mdp
    mdp = Markov()
    mdp.init = dict()

    # Stack for depth first search
    stack=[]

    # Find the initial states of the MDP
    for init_state in it.product(*map(lambda m: m.init.keys(), markov_tuple)):
        
        # Find initial probability and propositions of this state
        init_prob = reduce(lambda x,y: x*y, map(lambda m, s: m.init[s], markov_tuple, init_state))
        init_prop = reduce(lambda x,y: x|y, map(lambda m, s: m.g.node[s].get('prop',set()), markov_tuple, init_state))

        flat_init_state = flatten_tuple(init_state)

        # Set the initial probability of this state
        mdp.init[flat_init_state] = init_prob
        # Add the state to the graph
        mdp.g.add_node(flat_init_state, {'prop':init_prop, 'label':r'%s\n%.2f\n%s' % (flat_init_state,init_prob,list(init_prop))})
        # Start depth first search from the initial states
        stack.append(init_state)

    while(stack):
        cur_state = stack.pop()

        # Actual source states of traveling states
        source_state = tuple(map(lambda q: q[0] if isinstance(q, tuple) and len(q)==3 and isinstance(q[2], (int, float, long)) else q, cur_state))
        # Time spent since actual source states
        time_spent = tuple(map(lambda q: q[2] if isinstance(q, tuple) and len(q)==3 and isinstance(q[2], (int, float, long)) else 0, cur_state))

        # Iterate over all possible transitions
        for tran_tuple in it.product(*map(lambda t,q: t.next_states_of_markov(q), markov_tuple, cur_state)):
            # tran_tuple is a tuple of m-tuples (m: size of ts_tuple)

            # First element of each tuple: next_state
            # Second element of each tuple: time_left
            # Third element of each tuple: control    
            # Forth element of each tuple: tran_prob
            next_state = tuple([t[0] for t in tran_tuple])
            time_left = tuple([t[1] for t in tran_tuple])
            control = tuple([t[2] for t in tran_tuple])
            prob = tuple([t[3] for t in tran_tuple])

            # Min time until next transition
            w_min = min(time_left)
            tran_prob = reduce(lambda x,y: x*y, prob)

            # Next state label. Singleton if transition taken, tuple if traveling state
            next_state = tuple(map(lambda ss, ns, tl, ts: (ss,ns,w_min+ts) if w_min < tl else ns, source_state, next_state, time_left, time_spent))

            # Compute flat labels
            flat_cur_state = flatten_tuple(cur_state)
            flat_next_state = flatten_tuple(next_state)
            flat_control = flatten_tuple(control)

            # Add node if new
            if(flat_next_state not in mdp.g):
                # Props satisfied at next_state is the union of props
                # For each ts, get the prop of next state or empty set
                # Note: we use .get(ns, {}) as this might be a travelling state
                next_prop = map(lambda m,ns: m.g.node.get(ns,{}).get('prop',set()), markov_tuple, next_state)
                next_prop = set.union(*next_prop)

                # Add the new state
                mdp.g.add_node(flat_next_state, {'prop': next_prop, 'label': "%s\\n%s" % (flat_next_state, list(next_prop))})

                # Add transition w/ weight
                mdp.g.add_edge(flat_cur_state, flat_next_state, attr_dict = {'weight':w_min, 'control':flat_control, 'prob':tran_prob})
                #print "%s -%d-> %s (%s)" % (cur_state,w_min,next_state,next_prop)
                # Continue dfs from ns
                stack.append(next_state)

            # Add tran w/ weight if new
            elif(flat_next_state not in mdp.g[flat_cur_state]):
                mdp.g.add_edge(flat_cur_state, flat_next_state, attr_dict = {'weight':w_min, 'control':flat_control, 'prob':tran_prob})
                #print "%s -%d-> %s" % (cur_state,w_min,next_state)

    # Return m1 x m2 x ...
    return mdp


def markov_times_fsa(markov, fsa):
    '''TODO: trim to 80 characters per line
    add option to choose what to save on the automaton's
    add description
    add regression tests
    add option to create from current state
    '''

    # Create the product_model
    p = Markov()
    p.name = 'Product of %s and %s' % (markov.name, fsa.name)
    p.init = {}
    p.final = set()

    # Stack for depth first search
    stack = []
    # Iterate over initial states of the markov model
    for init_markov in markov.init.keys():
        init_prop = markov.g.node[init_markov].get('prop',set())
        # Iterate over the initial states of the FSA
        for init_fsa in fsa.init.keys():
            # Add the initial states to the graph and mark them as initial
            for act_init_fsa in fsa.next_states_of_fsa(init_fsa, init_prop):
                init_state = (init_markov, act_init_fsa)
                # Flatten state label
                flat_init_state = flatten_tuple(init_state)
                # Probabilities come from the markov model as FSA is deterministic
                p.init[flat_init_state] = markov.init[init_markov]
                p.g.add_node(flat_init_state, {'prop':init_prop, 'label':r'%s\n%.2f\n%s' % (flat_init_state,p.init[flat_init_state],list(init_prop))})
                if act_init_fsa in fsa.final:
                    p.final.add(flat_init_state)
                # Add this initial state to stack
                stack.append(init_state)

    # Consume the stack
    while(stack):
        cur_state = stack.pop()
        flat_cur_state = flatten_tuple(cur_state)
        markov_state = cur_state[0]
        fsa_state = cur_state[1]
    
        for markov_next in markov.next_states_of_markov(markov_state, traveling_states = False):
            markov_next_state = markov_next[0]
            markov_next_prop = markov.g.node[markov_next_state]['prop']
            weight = markov_next[1]
            control = markov_next[2]
            prob = markov_next[3]
            for fsa_next_state in fsa.next_states_of_fsa(fsa_state, markov_next_prop):
                next_state = (markov_next_state, fsa_next_state)
                flat_next_state = flatten_tuple(next_state)
                #print "%s -%d-> %s" % (cur_state, weight, next_state)
    
                if(flat_next_state not in p.g):
                    next_prop = markov.g.node[markov_next_state].get('prop',set())
    
                    # Add the new state
                    p.g.add_node(flat_next_state, {'prop': next_prop, 'label': "%s\\n%s" % (flat_next_state, list(next_prop))})
    
                    # Add transition w/ weight and prob
                    p.g.add_edge(flat_cur_state, flat_next_state, attr_dict = {'weight':weight, 'control':control, 'prob':prob})
    
                    # Mark as final if final in fsa
                    if fsa_next_state in fsa.final:
                        p.final.add(flat_next_state)
    
                    # Continue search from next state
                    stack.append(next_state)
    
                elif(flat_next_state not in p.g[flat_cur_state]):
                    p.g.add_edge(flat_cur_state, flat_next_state, attr_dict = {'weight':weight, 'control':control, 'prob':prob})

    return p
