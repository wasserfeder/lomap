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

from ..classes import Fsa, Markov, Model, Ts, Timer


# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

#TODO: make independent of graph type
__all__ = ['ts_times_ts', 'ts_times_buchi', 'ts_times_fsa', 'ts_times_fsas',
           'markov_times_markov', 'markov_times_fsa', 'fsa_times_fsa',
           'no_data', 'get_default_state_data', 'get_default_transition_data',
           'pfsa_default_transition_data', 'pts_default_state_data']

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
    ts = kwargs.get('ts')
    ts_state, _ = state
    prop = ts.g.node[ts_state]['prop']
    return {'prop': prop, 'label': "{}\\n{}".format(state, list(prop))}

def get_default_transition_data(current_state, next_state, **kwargs):
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

def process_product_initial_states(product_model, ts, automaton, from_current,
                                   get_state_data):
    '''Generates the initial states of the product model.

    Parameters
    ----------
    product_model: LOMAP model
        The product LOMAP model the transition is added to.

    ts: LOMAP transition system

    automaton: LOMAP automaton

    from_current: bool, optional (default: False)
        Indicates whether the product automaton should be constructed starting
        from the current TS and FSA states.

    get_state_data: function
        Returns the data to be saved for a state of the product. The function
        takes the state as a mandatory argument, and no other arguments.
    '''
    if from_current:
        product_model.init = {(ts.current, automaton.current)}
    else:
        # Iterate over initial states of the TS
        for init_ts in ts.init:
            init_prop = ts.g.node[init_ts].get('prop', set())
            # Iterate over the initial states of the automaton
            for init_aut in automaton.init:
                # Add the initial states to the graph and mark them as initial
                for act_init_aut in automaton.next_states(init_aut, init_prop):
                    init_state = (init_ts, act_init_aut)
                    product_model.init.add(init_state)
                    init_state_data = get_state_data(init_state)
                    product_model.g.add_node(init_state, **init_state_data)
                    if act_init_aut in automaton.final:
                        product_model.final.add(init_state)

def process_product_transition(product_model, stack, current_state, next_state,
                               blocking, is_final, get_state_data,
                               get_transition_data):
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

    blocking: Boolean
        Indicates whether the transition is blocking.

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
    # If transition is not blocking
    if not blocking:
        # Form new product automaton state
        if next_state not in product_model.g:
            # Add new state with data
            next_state_data = get_state_data(next_state)
            product_model.g.add_node(next_state, **next_state_data)
            # Mark as final if it is final for all FSAs
            if is_final:
                product_model.final.add(next_state)
            # Continue search from next state
            if stack is not None:
                stack.append(next_state)
        if next_state not in product_model.g[current_state]:
            # Add transition with data
            transition_data = get_transition_data(current_state, next_state)
            product_model.g.add_edge(current_state, next_state,
                                     attr_dict=transition_data)

def ts_times_fsa(ts, fsa, from_current=False, expand_finals=True,
                 get_state_data=get_default_state_data,
                 get_transition_data=get_default_transition_data):
    '''Computes the product automaton between a transition system and an FSA.

    Parameters
    ----------
    ts: LOMAP transition system

    fsa: LOMAP deterministic finite state automaton

    from_current: bool, optional (default: False)
        Indicates whether the product automaton should be constructed starting
        from the current TS and FSA states.

    expand_finals: bool, optional (default: True)
        Indicates whether the product automaton should be extended beyond
        reachable final states.

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
    the from_current option set. The current state is retrieved from the ts
    and fsa.

    TODO
    ----
    Add regression tests.
    Add debugging logging.
    '''

    # Create the product_model
    product_model = Model()
    # Simplify state and transition data functions
    get_state_data_ = lambda state: get_state_data(state, ts=ts, fsa=fsa)
    get_transition_data_ = lambda current_state, next_state: \
                                get_transition_data(current_state, next_state,
                                                    ts=ts, fsa=fsa)
    # Generate the initial states of the product model
    process_product_initial_states(
        product_model=product_model,
        ts=ts,
        automaton=fsa,
        from_current=from_current,
        get_state_data=get_state_data_)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    while stack:
        current_state = stack.popleft()
        ts_state, fsa_state = current_state
        # Skip propagation beyond final states
        if not expand_finals and fsa_state in fsa.final:
            continue
        # Loop over next_states of transition system
        for ts_next_state, _, _ in ts.next_states_of_wts(ts_state,
                                                        traveling_states=False):
            # Get the propositions satisfied at the next state
            ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
            # Get next FSA state using the TS prop
            fsa_next_state = fsa.next_state(fsa_state, ts_next_prop)

            process_product_transition(product_model, stack,
                current_state=current_state,
                next_state=(ts_next_state, fsa_next_state),
                blocking=fsa_next_state is None,
                is_final=fsa_next_state in fsa.final,
                get_state_data=get_state_data_,
                get_transition_data=get_transition_data_)

    return product_model

def ts_times_buchi(ts, buchi, from_current=False,
                 get_state_data=get_default_state_data,
                 get_transition_data=get_default_transition_data):
    '''Computes the product automaton between a transition system and a Buchi
    automaton.

    Parameters
    ----------
    ts: LOMAP transition system

    buchi: LOMAP Buchi automaton

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
    the from_current option set. The current state is retrieved from the ts
    and buchi.

    TODO
    ----
    Add regression tests.
    Add debugging logging.
    '''

    # Create the product_model
    product_model = Model()
    # Simplify state and transition data functions
    get_state_data_ = lambda state: get_state_data(state, ts=ts, buchi=buchi)
    get_transition_data_ = lambda current_state, next_state: \
                                get_transition_data(current_state, next_state,
                                                    ts=ts, buchi=buchi)
    # Generate the initial states of the product model
    process_product_initial_states(
        product_model=product_model,
        ts=ts,
        automaton=buchi,
        from_current=from_current,
        get_state_data=get_state_data_)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    while stack:
        current_state = stack.popleft()
        ts_state, buchi_state = current_state
        # Loop over next_states of transition system
        for ts_next_state, _, _ in ts.next_states_of_wts(ts_state,
                                                        traveling_states=False):
            # Get the propositions satisfied at the next state
            ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
            # Loop over next Buchi states using the TS prop
            for buchi_next_state in buchi.next_states(buchi_state,
                                                      ts_next_prop):
                process_product_transition(product_model, stack,
                    current_state=current_state,
                    next_state=(ts_next_state, buchi_next_state),
                    blocking=False,
                    is_final=buchi_next_state in buchi.final,
                    get_state_data=get_state_data_,
                    get_transition_data=get_transition_data_)

    return product_model

def pts_default_state_data(state, ts_tuple):
    '''TODO:
    '''
    # Props satisfied at init_state is the union of props
    # For each ts, get the prop of init state or empty set
    prop = set.union(*[ts.g.node[x].get('prop', set())
                                        for ts, x in it.izip(ts_tuple, state)])
    return {'prop': prop, 'label': "{}\\n{}".format(state, list(prop))}

def ts_times_ts(ts_tuple, asynchronous=True, from_current=False,
                get_state_data=pts_default_state_data,
                get_transition_data=no_data):
    '''TODO:

    Parameters
    ----------
    '''
    if asynchronous:
        return ts_times_ts_asynchronous(ts_tuple)
    else:
        return ts_times_ts_synchronous(ts_tuple, from_current, get_state_data,
                                       get_transition_data)

def ts_times_ts_synchronous(ts_tuple, from_current=False,
                            get_state_data=pts_default_state_data,
                            get_transition_data=no_data):
    '''Computes the product TS between a multiple TSs.

    Parameters
    ----------
    ts_tuple: iterable of LOMAP transition systems

    from_current: bool, optional (default: False)
        Indicates whether the product transition system should be constructed
        starting from the current TSs' states.

    get_state_data: function, optional (default: pts_default_state_data)
        Returns the data to be saved for a state of the product. The function
        takes the state as a mandatory argument, and optional keyword arguments.

    get_transition_data : function, optional (default: no_data)
        Returns the data to be saved for a transition of the product. The
        function takes the two endpoint states as mandatory arguments, and
        optional keyword arguments.

    Returns
    -------
    product_ts : LOMAP Ts

    Notes
    -----
    The procedure supports only a single current state for construction with
    the from_current option set. The current state is retrieved from the TSs.
    '''
    # NOTE: We assume deterministic TS
    assert all((len(ts.init) == 1 for ts in ts_tuple))

    # Initial state label is the tuple of initial states' labels
    multi = any(ts.multi for ts in ts_tuple)
    directed = any(ts.directed for ts in ts_tuple)
    product_ts = Ts(multi=multi, directed=directed)

    if from_current:
        init_state = tuple(ts.current for ts in ts_tuple)
    else:
        init_state = tuple(next(iter(ts.init)) for ts in ts_tuple)
    product_ts.init = {init_state}

    def get_neighbors(state):
        return it.product(*[ts.g[x] for x, ts in it.izip(state, ts_tuple)])

    # Start depth first search from the initial state
    stack=deque([(init_state, get_neighbors(init_state))])
    while stack:
        current_state, neighbors = stack.popleft()
        state_data = get_state_data(current_state, ts_tuple=ts_tuple)
        product_ts.g.add_node(current_state, **state_data)
        for next_state in neighbors:
            if next_state not in product_ts.g:
                stack.append((next_state, get_neighbors(next_state)))
            transition_data = get_transition_data(current_state, next_state,
                                                  ts_tuple=ts_tuple)
            product_ts.g.add_edge(current_state, next_state, **transition_data)
    return product_ts

def ts_times_ts_asynchronous(ts_tuple):
    '''TODO:
    add option to choose what to save on the automaton's
    add description
    add regression tests
    add option to create from current state
    '''
    # NOTE: We assume deterministic TS
    assert all((len(ts.init) == 1 for ts in ts_tuple))

    # Initial state label is the tuple of initial states' labels
    product_ts = Ts()

    init_state = tuple((next(iter(ts.init)) for ts in ts_tuple))
    product_ts.init[init_state] = 1

    # Props satisfied at init_state is the union of props
    # For each ts, get the prop of init state or empty set
    init_prop = set.union(*[ts.g.node[ts_init].get('prop', set())
                              for ts, ts_init in it.izip(ts_tuple, init_state)])

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
                                     for t, q in it.izip(ts_tuple, cur_state)]):
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
                        for ss, ns, tl, ts in it.izip(
                            source_state, next_state, time_left, time_spent)))

            # Add node if new
            if next_state not in product_ts.g:
                # Props satisfied at next_state is the union of props
                # For each ts, get the prop of next state or empty set
                # Note: we use .get(ns, {}) as this might be a travelling state
                next_prop = set.union(*[ts.g.node.get(ns, {}).get('prop', set())
                                   for ts, ns in it.izip(ts_tuple, next_state)])

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
        from the current FSAs' states.

    get_state_data: function, optional (default: no_data)
        Returns the data to be saved for a state of the product. The function
        takes the state as a mandatory argument, and optional keyword arguments.

    get_transition_data : function, optional
        (default: pfsa_default_transition_data)
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
    assert not any(fsa.multi for fsa in fsa_tuple), \
                                        'Multi-graph FSAs are not supported!'

    if from_current:
        init_state = tuple([fsa.current for fsa in fsa_tuple])
    else:
        # assume deterministic FSAs
        assert all([len(fsa.init) == 1 for fsa in fsa_tuple])
        init_state = tuple([next(iter(fsa.init)) for fsa in fsa_tuple])

    # union of all atomic proposition sets
    product_props = set.union(*[set(fsa.props) for fsa in fsa_tuple])
    product_fsa = Fsa(product_props, multi=False)
    product_fsa.init[init_state] = 1

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
#             bitmaps = product_fsa.get_guard_bitmap(guard)

            aux = [set(it.chain.from_iterable(
                                         [tr[s] for s in fsa.g[u][v]['input']]))
                        for u, v, fsa, tr in it.izip(current_state,
                                      next_state, fsa_tuple, symbol_tables)]
            bitmaps = set.intersection(*aux)

            if bitmaps:
                if next_state not in product_fsa.g:
                    stack.append((next_state, it.product(*[fsa.g[s]
                               for s, fsa in it.izip(next_state, fsa_tuple)])))
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

    from_current: bool, optional (default: False)
        Indicates whether the product automaton should be constructed starting
        from the current TS and FSA states.

    expand_finals: bool, optional (default: True)
        Indicates whether the product automaton should be extended beyond
        reachable final states.

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
    the from_current option set. The current state is retrieved from the ts
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
        for is_current, fsa in it.izip(from_current[1:], fsa_tuple):
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
        if all(s in fsa.final for s, fsa in it.izip(pfsa_current, fsa_tuple)):
            product_model.final.add(init_state)
    else:
        # Iterate over initial states of the TS
        for init_ts in ts.init:
            init_prop = ts.g.node[init_ts].get('prop', set())
            # Iterate over the initial states of the FSA
            for init_pfsa in it.product(*[fsa.init for fsa in fsa_tuple]):
                # Add the initial states to the graph and mark them as initial
                act_init_pfsa = tuple(fsa.next_state(init_fsa, init_prop)
                             for init_fsa, fsa in it.izip(init_pfsa, fsa_tuple))
                if all(fsa_state is not None for fsa_state in act_init_pfsa):
                    init_state = (init_ts, act_init_pfsa)
                    product_model.init[init_state] = 1
                    init_state_data = get_state_data_(init_state)
                    product_model.g.add_node(init_state, **init_state_data)
                    if all(fsa_state in fsa.final
                       for fsa_state, fsa in it.izip(act_init_pfsa, fsa_tuple)):
                        product_model.final.add(init_state)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    while stack:
        current_state = stack.popleft()
        ts_state, pfsa_state = current_state
        # Skip propagation beyond final states
        if not expand_finals and current_state in product_model.final:
            continue
        # Loop over next states of transition system
        for ts_next_state, _, _ in ts.next_states_of_wts(ts_state,
                                                     traveling_states=False):
            # Get the propositions satisfied at the next state
            ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
            # Get next product FSA state using the TS prop
            pfsa_next_state = tuple(fsa.next_state(fsa_state, ts_next_prop)
                        for fsa, fsa_state in it.izip(fsa_tuple, pfsa_state))

            process_product_transition(product_model, stack,
                current_state=current_state,
                next_state=(ts_next_state, pfsa_next_state),
                blocking=any(s is None for s in pfsa_next_state),
                is_final=all(s in fsa.final for s, fsa in
                                          it.izip(pfsa_next_state, fsa_tuple)),
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

def markov_times_markov(markov_tuple, asynchronous=True):
    '''TODO:
    '''
    if asynchronous:
        markov_times_markov_asynchronous(markov_tuple)
    else:
        markov_times_markov_synchronous(markov_tuple)

def markov_times_markov_synchronous(markov_tuple):
    '''TODO:
    '''
    raise NotImplementedError

def markov_times_markov_asynchronous(markov_tuple):
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
        init_prob = reduce(lambda x,y: x*y, map(lambda m, s: m.init[s],
                                                markov_tuple, init_state))
        init_prop = reduce(lambda x,y: x|y,
                           map(lambda m, s: m.g.node[s].get('prop',set()),
                               markov_tuple, init_state))

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
        source_state = tuple(map(lambda q: q[0] if isinstance(q, tuple)
                                        and len(q)==3
                                        and isinstance(q[2], (int, float, long))
                                        else q,
                                 cur_state))
        # Time spent since actual source states
        time_spent = tuple(map(lambda q: q[2] if isinstance(q, tuple)
                                        and len(q)==3
                                        and isinstance(q[2], (int, float, long))
                                        else 0,
                               cur_state))

        # Iterate over all possible transitions
        for tran_tuple in it.product(*map(lambda t, q:
                                                    t.next_states_of_markov(q),
                                          markov_tuple, cur_state)):
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
                next_prop = map(lambda m,ns:
                                         m.g.node.get(ns,{}).get('prop', set()),
                                markov_tuple, next_state)
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

def markov_times_fsa(markov, fsa):
    '''TODO:
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
            for act_init_fsa in fsa.next_states(init_fsa, init_prop):
                init_state = (init_markov, act_init_fsa)
                # Flatten state label
                flat_init_state = flatten_tuple(init_state)
                # Probabilities come from the markov model as FSA is deterministic
                p.init[flat_init_state] = markov.init[init_markov]
                p.g.add_node(flat_init_state, {'prop': init_prop,
                        'label':r'{}\n{:.2f}\n{}'.format(flat_init_state,
                                    p.init[flat_init_state], list(init_prop))})
                if act_init_fsa in fsa.final:
                    p.final.add(flat_init_state)
                # Add this initial state to stack
                stack.append(init_state)

    # Consume the stack
    while stack:
        cur_state = stack.pop()
        flat_cur_state = flatten_tuple(cur_state)
        markov_state, fsa_state = cur_state

        for markov_next_state, weight, control, prob in \
           markov.next_states_of_markov(markov_state, traveling_states = False):
            markov_next_prop = markov.g.node[markov_next_state]['prop']

            for fsa_next_state in fsa.next_states(fsa_state, markov_next_prop):
                next_state = (markov_next_state, fsa_next_state)
                flat_next_state = flatten_tuple(next_state)
                #print "%s -%d-> %s" % (cur_state, weight, next_state)

                if flat_next_state not in p.g:
                    next_prop = markov.g.node[markov_next_state].get('prop',
                                                                     set())

                    # Add the new state
                    p.g.add_node(flat_next_state, {'prop': next_prop,
                                    'label': "{}\\n{}".format(flat_next_state,
                                                              list(next_prop))})

                    # Add transition w/ weight and prob
                    p.g.add_edge(flat_cur_state, flat_next_state,
                                 attr_dict={'weight': weight,
                                            'control': control,
                                            'prob': prob})

                    # Mark as final if final in fsa
                    if fsa_next_state in fsa.final:
                        p.final.add(flat_next_state)

                    # Continue search from next state
                    stack.append(next_state)

                elif flat_next_state not in p.g[flat_cur_state]:
                    p.g.add_edge(flat_cur_state, flat_next_state,
                                 attr_dict={'weight': weight,
                                            'control': control,
                                            'prob': prob})

    return p
