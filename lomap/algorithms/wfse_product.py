#! /usr/local/bin/python3.7

# This is where I implement the product functions

# Imports:
from __future__ import print_function
import itertools as it
import operator as op
import logging
from collections import deque

import lomap
from lomap.classes import Wfse
from lomap.algorithms.product import get_default_state_data, get_default_transition_data
from functools import reduce

# Logger configuration
logger = logging.getLogger(__name__)

# Product function:

    # This function will contain 3 for loops for each state of the product;
    # extract the label and the proposition.
    # We start from the ts from p to p' ==> We get the x' and L(x') = input_symbol // See what neighboring states I can reach using the error system
    # Then we have the error system which takes as input the x', L(x') (?!) and gives ==> q'
    # based on that we can figure out the input for fsa (!?)
    # then fsa gives out the next_state // s' is unique
    # the props and wfse give neighboring state of q' and then that maps to fsa state
    # (= so q' is the alternate state? // if it belongs to the wfse then it is the corresponding state to the wanted state [??])

#TODO: Here --> add the for loop / do the coupling (right) and then fix the import error!!

# The product function capturing the connections between the ts, wfse, and fsa:
def product_function(ts, wfse, fsa, from_current=False,
                            expand_finals=True,
                            get_state_data=get_default_state_data,
                            get_transition_data=get_default_transition_data):

    # Create the product_model
    product_model = Model()
    if from_current:
        product_model.init.add((ts.current, wfse.current, fsa.current))
    else:
        # Iterate over initial states of the TS
        for init_ts in ts.init:
            init_prop = ts.g.node[init_ts].get('prop', set())
            # Iterate over the initial states of the WFSE
            for init_wfse in wfse.init:
                for wfse_out in wfse.next_state(init_wfse, init_prop):
                    act_init_wfse, init_prop_relax, weight_relax = wfse_out
                    # Iterate over the initial states of the FSA
                    for init_fsa in fsa.init:
                        # Add the initial states to the graph and mark them as
                        # initial
                        act_init_fsa = fsa.next_state(init_fsa, init_prop_relax)
                        if act_init_fsa is not None:
                            init_state = (init_ts, act_init_wfse, act_init_fsa)
                            product_model.init.add(init_state)
                            product_model.g.add_node(init_state,
                                                     weight=weight_relax)
                            if act_init_fsa in fsa.final:
                                product_model.final.add(init_state)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    while stack:
        current_state = stack.pop()
        ts_state, wfse_state, fsa_state = current_state

        # skip processing final beyond final states
        if not expand_finals and fsa_state in fsa.final:
            continue

        for ts_next_state in ts.g.node[ts_state]:
            ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
            ts_weight = ts.g.node[ts_next_state].get('weight', 1)

            for wfse_out in wfse.next_states(wfse_state, ts_next_prop):
                wfse_next_state, next_prop_relax, wfse_weight = wfse_out

                fsa_next_state = fsa.next_state(fsa_state, next_prop_relax)
                if fsa_next_state is not None:
                    next_state = (ts_next_state, wfse_next_state,
                                  fsa_next_state)
                    if next_state not in product_model.g:
                        # Add the new state
                        product_model.g.add_node(next_state)
                        # Add weighted transition
                        weight = ts_weight * wfse_weight
                        product_model.g.add_edge(current_state, next_state,
                                                 weight=weight)
                        # Mark as final if final in fsa
                        if fsa_next_state in fsa.final:
                            product_model.final.add(next_state)
                        # Continue search from next state
                        stack.append(next_state)
                    elif next_state not in product_model.g[current_state]:
                        # Add weighted transition
                        weight = ts_weight * wfse_weight
                        product_model.g.add_edge(current_state, next_state,
                                                 weight=weight)

    return product_model
