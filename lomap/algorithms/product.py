#! /usr/bin/python

# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
#               2016-2024  Cristian-Ioan Vasile (cvasile@lehigh.edu)
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

from six.moves import zip

from lomap.classes import Fsa, Markov, Model, Ts, Timer
from functools import reduce


# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

#TODO: make independent of graph type
__all__ = ['ts_times_ts', 'ts_times_buchi', 'ts_times_fsa', 'ts_times_fsas',
           'markov_times_markov', 'markov_times_fsa', 'fsa_times_fsa',
           'no_data', 'get_default_state_data', 'get_default_transition_data',
           'pfsa_default_transition_data']

def powerset(iterable):
    '''powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    Note: from https://docs.python.org/2.7/library/itertools.html#recipes
    '''
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r)
                                                      for r in range(len(s)+1))

def no_data(*args, **kwargs):
    '''Returns an empty dictionary.'''
    return dict()

def get_default_state_data(state, c, aut):
    '''Returns the default data to store for a state of a product.

    Parameters
    ----------
    state: hashable
        A state.

    Returns
    -------
        dictionary containing the data to be stored.
    '''
    return {'prop': sys.g.nodes[state].get('prop', None)}

def get_default_transition_data(current_state, next_state, sys, aut):
    '''Returns the default data to store for a transition of a product.

    Parameters
    ----------
    current_state, next_state: hashable
        The endpoint states of the transition.

    Returns
    -------
        Dictionary containing the data to be stored.
    '''
    return {'weight': sys.g[cur_state, next_state].get('weight', None)}


def process_product_initial_states(product_model, ts, aut, get_state_data):
    '''Process the initial states of a product model.
    
    Parameters
    ----------
    product_model: LOMAP model
        The product LOMAP model the initial states are added to.
    
    ts: LOMAP transition system

    aut: LOMAP automaton

    get_state_data: function
        Returns the data to be saved for a state of the product. The function
        takes the state as a mandatory argument, and no other arguments.
    '''
    # Iterate over initial states of the TS
    for init_ts in ts.init:
        init_prop = ts.g.nodes[init_ts].get('prop', set())
        # Iterate over the initial states of the automaton
        for init_aut in aut.init:
            # Add the initial states to the product and mark them as initial
            for act_init_aut in aut.next_states(init_aut, init_prop):
                init_state = (init_ts, act_init_aut)
                product_model.init.add(init_state)
                init_state_data = get_state_data(init_state)
                product_model.g.add_node(init_state, **init_state_data)
                if act_init_aut in fsa.final:
                    product_model.final.add(init_state)


def process_product_transition(product_model, stack, current_state, next_state,
                               is_final, get_state_data, get_transition_data):
    '''Process a transition of a product model.

    Parameters
    ----------
    product_model: LOMAP model
        The product LOMAP model the transition is added to.

    stack: list or deque
        The stack used for process the states of the product LOMAP model.

    current_state: hashable
        The origin endpoint state of the transition.

    next_state: hashable
        The destination endpoint state of the transition.

    is_final: Boolean
        Indicates whether next_state is an accepting state.

    get_state_data: function
        Returns the data to be saved for a state of the product. The function
        takes the state as a mandatory argument, and no other arguments.

    get_transition_data : function
        Returns the data to be saved for a transition of the product. The
        function takes the two endpoint states as mandatory arguments, and
        no other arguments.
    '''
    # form new product automaton state
    if next_state not in product_model.g:
        # Add new state with data
        next_state_data = get_state_data(next_state)
        product_model.g.add_node(next_state, **next_state_data)
        # Mark as final if it is final for all FSAs
        if is_final:
            product_model.final.add(next_state)
        # Continue search from next state
        stack.append(next_state)
    if next_state not in product_model.g[current_state]:
        # Add transition with data
        transition_data = get_transition_data(current_state, next_state)
        product_model.g.add_edge(current_state, next_state,
                                 attr_dict=transition_data)


def system_times_automaton(sys, aut, from_current=False, expand_finals=True,
                           product_type=Model,
                           get_state_data=get_default_state_data,
                           get_transition_data=get_default_transition_data):
    '''Computes the product automaton between a transition system and an
    automaton.

    Parameters
    ----------
    sys: LOMAP system model

    aut: LOMAP automaton

    from_current: bool, optional (default: False)
        Indicates whether the product automaton should be constructed starting
        from the current TS and Automaton states.

    expand_finals: bool, optional (default: True)
        Indicates whether the product automaton construction should proceed
        beyond reaching final states.

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
    the from_current option set. The current state is retrieved from the system
    model and automaton.

    TODO
    ----
    Add regression tests.
    Add debugging logging.
    '''

    get_state_data_ = lambda state: get_state_data(state, sys, aut)
    get_transition_data_ = lambda current_state, next_state: \
        get_transition_data(current_state, next_state, sys, aut)

    # Create product model
    multi = sys.multi or aut.multi
    assert aut.directed
    product_model = product_type(directed=True, multi=multi,
                                 init_factory=set, final_factory=set)

    # Process initial states
    if from_current:
        product_model.init.add((sys.current, fsa.current))
    else:
        process_product_initial_states()

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    while stack:
        current_state = stack.pop()
        sys_state, aut_state = current_state

        # skip processing final beyond final states
        if not expand_finals and aut_state in aut.final:
            continue

        for sys_next_state, sys_next_prop in sys.g[ts_state].data('prop', set()):
            for aut_next_state in aut.next_states(aut_state, sys_next_prop)
                process_product_transition(
                    product_model,
                    stack,
                    current_state=current_state,
                    next_state=(sys_next_state, aut_next_state),
                    is_final=aut_next_state in aut.final,
                    get_state_data=get_state_data_,
                    get_transition_data=get_transition_data_
                )
    return product_model

ts_times_fsa = ts_times_automaton
ts_times_buchi = ts_times_automaton

def ts_times_ts(ts_tuple):
    '''TODO:
    add option to choose what to save on the automaton's
    add description
    add regression tests
    add option to create from current state
    '''
    # NOTE: We assume deterministic TS
    assert all((len(ts.init) == 1 for ts in ts_tuple))

    multi = any(ts.multi for ts in ts_tuple)
    directed = any(ts.directed for ts in ts_tuple)
    product_ts = Ts(directed=directed, multi=multi,
                    init_factory=set)

    # Initial state label is the tuple of initial states' labels
    init_state = tuple((next(iter(ts.init)) for ts in ts_tuple))
    product_ts.init.add(init_state)

    # Props satisfied at init_state is the union of props
    # For each ts, get the prop of init state or empty set
    init_prop = set.union(*[ts.g.node[ts_init].get('prop', set())
                            for ts, ts_init in zip(ts_tuple, init_state)])

    # Finally, add the state
    product_ts.g.add_node(init_state, {'prop': init_prop,
                        'label': "{}\\n{}".format(init_state, list(init_prop))})

    # Start depth first search from the initial state
    stack=[]
    stack.append(init_state)
    while stack:
        cur_state = stack.pop()
        # Actual source states of traveling states
        source_state = tuple((q[0] if type(q) == tuple else q
                              for q in cur_state))
        # Time spent since actual source states
        time_spent = tuple((q[2] if type(q) == tuple else 0 for q in cur_state))

        # Iterate over all possible transitions
        for tran_tuple in it.product(*[t.next_states_of_wts(q)
                                       for t, q in zip(ts_tuple, cur_state)]):
            # tran_tuple is a tuple of m-tuples (m: size of ts_tuple)

            # First element of each tuple: next_state
            # Second element of each tuple: time_left
            next_state = tuple([t[0] for t in tran_tuple])
            time_left = tuple([t[1] for t in tran_tuple])
            control = tuple([t[2] for t in tran_tuple])

            # Min time until next transition
            w_min = min(time_left)

            # Next state label. Singleton if transition taken, tuple if
            # traveling state
            next_state = tuple(((ss, ns, w_min+ts) if w_min < tl else ns
                        for ss, ns, tl, ts in zip(
                            source_state, next_state, time_left, time_spent)))

            # Add node if new
            if next_state not in product_ts.g:
                # Props satisfied at next_state is the union of props
                # For each ts, get the prop of next state or empty set
                # Note: we use .get(ns, {}) as this might be a travelling state
                next_prop = set.union(*[ts.g.node.get(ns, {}).get('prop', set())
                                       for ts, ns in zip(ts_tuple, next_state)])

                # Add the new state
                product_ts.g.add_node(next_state, {'prop': next_prop,
                        'label': "{}\\n{}".format(next_state, list(next_prop))})

                # Add transition w/ weight
                product_ts.g.add_edge(cur_state, next_state,
                                attr_dict={'weight': w_min, 'control': control})
                # Continue dfs from ns
                stack.append(next_state)

            # Add tran w/ weight if new
            elif next_state not in product_ts.g[cur_state]:
                product_ts.g.add_edge(cur_state, next_state,
                                attr_dict={'weight': w_min, 'control': control})

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
    the from_current option set. The current state is retrieved from the FSAs.

    TODO
    ----
    Add regression tests.
    Add debugging logging.
    Add option to choose what to save on the automaton's states and transitions.
    '''
    if from_current:
        init_state = tuple([fsa.current for fsa in fsa_tuple])
    else:
        # assume deterministic FSAs
        assert all([len(fsa.init) == 1 for fsa in fsa_tuple])
        init_state = tuple([next(iter(fsa.init)) for fsa in fsa_tuple])

    # union of all atomic proposition sets
    product_props = set.union(*[set(fsa.props) for fsa in fsa_tuple])
    product_fsa = Fsa(product_props, multi=False)
    product_fsa.init.add(init_state)

    symbol_tables = []
    for fsa in fsa_tuple:
        translation_table = dict()
        for fsa_props in powerset(fsa.props):
            fsa_symbol = fsa.bitmap_of_props(fsa_props)
            product_fsa_symbol = product_fsa.bitmap_of_props(fsa_props)
            other_props = set(product_fsa.props) - set(fsa.props)

            product_fsa_symbols = set()
            for pfsa_props in powerset(other_props):
                other_pfsa_symbol = product_fsa.bitmap_of_props(pfsa_props)
                assert not (product_fsa_symbol & other_pfsa_symbol)
                product_fsa_symbols.add(product_fsa_symbol | other_pfsa_symbol)
            translation_table[fsa_symbol] = product_fsa_symbols
        symbol_tables.append(translation_table)

    # Start depth first search from the initial state
    stack = deque([(init_state, it.product(*[fsa.g[s]
                                   for s, fsa in zip(init_state, fsa_tuple)]))])

    while stack:
        current_state, neighbors = stack.popleft()
        state_data = get_state_data(current_state, fsa_tuple=fsa_tuple)
        product_fsa.g.add_node(current_state, **state_data)
        if all([s in fsa.final for s, fsa in zip(current_state, fsa_tuple)]):
            product_fsa.final.add(current_state)
        # Iterate over all possible transitions
        for next_state in neighbors:
            guard = [fsa.g[u][v]['guard']
                            for u, v, fsa in zip(current_state, next_state,
                                                     fsa_tuple)]
            guard = '({})'.format(' ) & ( '.join(guard))
#             bitmaps = product_fsa.get_guard_bitmap(guard)

            aux = [set(it.chain.from_iterable(
                                         [tr[s] for s in fsa.g[u][v]['input']]))
                        for u, v, fsa, tr in zip(current_state,
                                      next_state, fsa_tuple, symbol_tables)]
            bitmaps = set.intersection(*aux)

            if bitmaps:
                if next_state not in product_fsa.g:
                    stack.append((next_state, it.product(*[fsa.g[s]
                               for s, fsa in zip(next_state, fsa_tuple)])))
                transition_data = get_transition_data(current_state, next_state,
                              guard=guard, bitmaps=bitmaps, fsa_tuple=fsa_tuple)
                product_fsa.g.add_edge(current_state, next_state,
                                       attr_dict=transition_data)
    # Return fsa_1 x fsa_2 x ...
    return product_fsa

def ts_times_fsas(ts, fsa_tuple, from_current=None, expand_finals=True,
                  get_state_data=no_data,
                  get_transition_data=get_default_transition_data):
    '''Computes the product automaton between a transition system and an FSA.

    Parameters
    ----------
    ts: LOMAP transition system

    fsa_tuple: a tuple of LOMAP deterministic finite state automata

    get_state_data: function, optional (default: no _data)
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
    and fsa_tuple.

    TODO:
    ----
    Add regression tests.
    Add debugging logging.
    '''

    # Create the product_model
    product_model = Model(multi=False, directed=True)
    # Simplify state and transition data functions
    get_state_data_ = lambda state: get_state_data(state, ts=ts,
                                                  fsa_tuple=fsa_tuple)
    get_transition_data_ = lambda current_state, next_state: \
                                get_transition_data(current_state, next_state,
                                                    ts=ts, fsa_tuple=fsa_tuple)

    if from_current is not None:
        # NOTE: this option assumes that the TS and FSAs are deterministic
        assert len(from_current) == len(fsa_tuple)+1
        # Get current TS state
        if from_current[0]:
            ts_current = ts.current
        else:
            ts_current = next(iter(ts.init))
        # Get the APs at the current TS state
        prop_current = ts.g.node[ts_current].get('prop', set())
        # Get current product FSA state
        pfsa_current = []
        for is_current, fsa in zip(from_current[1:], fsa_tuple):
            if is_current:
                pfsa_current.append(fsa.current)
            else:
                fsa_init = next(iter(fsa.init))
                pfsa_current.append(fsa.next_state(fsa_init, prop_current))
        if any(s is None for s in pfsa_current): # if an FSA gets blocked
            return product_model
        pfsa_current = tuple(pfsa_current)
        # Process initial product model state
        init_state = (ts_current, pfsa_current)
        # Add to initial state
        product_model.init[init_state] = 1
        # Add to product graph with data
        init_state_data = get_state_data_(init_state)
        product_model.g.add_node(init_state, **init_state_data)
        # Check if final
        if all(s in fsa.final for s, fsa in zip(pfsa_current, fsa_tuple)):
            product_model.final.add(init_state)
    else:
        # Iterate over initial states of the TS
        for init_ts in ts.init:
            init_prop = ts.g.node[init_ts].get('prop', set())
            # Iterate over the initial states of the FSA
            for init_pfsa in it.product(*[fsa.init for fsa in fsa_tuple]):
                # Add the initial states to the graph and mark them as initial
                act_init_pfsa = tuple(fsa.next_state(init_fsa, init_prop)
                             for init_fsa, fsa in zip(init_pfsa, fsa_tuple))
                if all(fsa_state is not None for fsa_state in act_init_pfsa):
                    init_state = (init_ts, act_init_pfsa)
                    product_model.init[init_state] = 1
                    init_state_data = get_state_data_(init_state)
                    product_model.g.add_node(init_state, **init_state_data)
                    if all(fsa_state in fsa.final
                       for fsa_state, fsa in zip(act_init_pfsa, fsa_tuple)):
                        product_model.final.add(init_state)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    while stack:
        current_state = stack.popleft()
        ts_state, pfsa_state = current_state
        # Skip propagation of beyond final states
        if not expand_finals and current_state in product_model.final:
            continue
        # Loop over next states of transition system
        for ts_next_state, _, _ in ts.next_states_of_wts(ts_state,
                                                     traveling_states=False):
            # Get the propositions satisfied at the next state
            ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
            # Get next product FSA state using the TS prop
            pfsa_next_state = tuple(fsa.next_state(fsa_state, ts_next_prop)
                        for fsa, fsa_state in zip(fsa_tuple, pfsa_state))

            if all(s is not None for s in pfsa_next_state):
                process_product_transition(product_model, stack,
                    current_state=current_state,
                    next_state=(ts_next_state, pfsa_next_state),
                    is_final=all(s in fsa.final for s, fsa in
                                              zip(pfsa_next_state, fsa_tuple)),
                    get_state_data=get_state_data_,
                    get_transition_data=get_transition_data_)

    return product_model


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
    '''TODO:
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
        init_prob = reduce(lambda x, y: x * y,
                   (m.init[s] for m, s in zip(markov_tuple, init_state)))
        init_prop = reduce(lambda x, y: x | y,
                   (m.g.node[s].get('prop', set())
                    for m, s in zip(markov_tuple, init_state)))

        flat_init_state = flatten_tuple(init_state)

        # Set the initial probability of this state
        mdp.init[flat_init_state] = init_prob
        # Add the state to the graph
        mdp.g.add_node(flat_init_state,
                       {'prop': init_prop,
                        'label': r'{}\n{:.2f}\n{}'.format(flat_init_state,
                                                init_prob, list(init_prop))})

        # Start depth first search from the initial states
        stack.append(init_state)

    while stack:
        cur_state = stack.pop()

        # Actual source states of traveling states
        source_state = tuple([q[0] if isinstance(q, tuple)
                                        and len(q)==3
                                        and isinstance(q[2], (int, float))
                                        else q for q in cur_state])
        # Time spent since actual source states
        time_spent = tuple([q[2] if isinstance(q, tuple)
                                        and len(q)==3
                                        and isinstance(q[2], (int, float))
                                        else 0 for q in cur_state])

        # Iterate over all possible transitions
        for tran_tuple in it.product(*[t.next_states_of_markov(q)
                               for t, q in zip(markov_tuple, cur_state)]):
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

            # Next state label. Singleton if transition taken, tuple if
            # traveling state
            next_state = tuple(map(lambda ss, ns, tl, ts: (ss,ns,w_min+ts)
                                                         if w_min < tl else ns,
                                   source_state, next_state, time_left,
                                   time_spent))

            # Compute flat labels
            flat_cur_state = flatten_tuple(cur_state)
            flat_next_state = flatten_tuple(next_state)
            flat_control = flatten_tuple(control)

            # Add node if new
            if(flat_next_state not in mdp.g):
                # Props satisfied at next_state is the union of props
                # For each ts, get the prop of next state or empty set
                # Note: we use .get(ns, {}) as this might be a travelling state
                next_prop = [m.g.node.get(ns,{}).get('prop', set())
             for m, ns in zip(markov_tuple, next_state)]
                next_prop = set.union(*next_prop)

                # Add the new state
                mdp.g.add_node(flat_next_state,
                    {'prop': next_prop,
                     'label': "{}\\n{}".format(flat_next_state,
                                               list(next_prop))})

                # Add transition w/ weight
                mdp.g.add_edge(flat_cur_state, flat_next_state,
                               attr_dict={'weight': w_min,
                                          'control': flat_control,
                                          'prob': tran_prob})
                # Continue dfs from ns
                stack.append(next_state)

            # Add tran w/ weight if new
            elif(flat_next_state not in mdp.g[flat_cur_state]):
                mdp.g.add_edge(flat_cur_state, flat_next_state,
                               attr_dict={'weight': w_min,
                                          'control':flat_control,
                                          'prob':tran_prob})
                #print "%s -%d-> %s" % (cur_state,w_min,next_state)

    # Return m1 x m2 x ...
    return mdp


def markov_times_fsa(markov, fsa, from_current=False, expand_finals=True):
    '''TODO:
    add option to choose what to save on the automaton's
    add description
    add regression tests
    add option to create from current state
    '''

    def get_transition_data_(current_state, next_state): 
        d = markov.g[current_state, next_state]
        return {'weight': d.get('weight', 0),
                'control': d.get('control', 0),
                'prob': d.get(prob, 0)}

    # Create the product Markov model
    pmdp = system_times_automaton(markov, aut,
                                  from_current=from_current,
                                  expand_finals=expand_finals,
                                  product_type=Markov,
                                  get_state_data=get_default_state_data,
                                  get_transition_data=get_transition_data_)
    init_dist = dict(((state, markov.init[state[0]]) for state in pmdp.init))
    pmdp.init = init_dist
    return pmdp
