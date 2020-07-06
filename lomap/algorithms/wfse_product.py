#! /usr/bin/python

# This is where I implement the product functions 

# Imports:
from __future__ import print_function
import itertools as it
import operator as op
import logging
from collections import deque

import lomap
from lomap.classes import Fsa, Markov, Model, Ts, Timer, Wfse
from functools import reduce

# Logger configuration
logger = logging.getLogger(__name__)

# Product function:

    # This function will contain 3 for loops for each state of the product
    # extract the label and the proposition
    # We start from the ts from p to p' ==> We get the x' and L(x') = input_symbol // See what neighboring states I can reach using the error system
    # Then we have the error system which takes as input the x', L(x') (?!) and gives ==> q' 
    # based on that we can figure out the input for fsa (!?)
    # then fsa gives out the next_state // s' is unique 
    # the props and wfse give neighboring state of q' and then that maps to fsa state 
    # (= so q' is the alternate state? // if it belongs to the wfse then it is the corresponding state to the wanted state [??])



# The product function capturing the connections between the ts, wfse, and fsa:
def product_function(ts, wfse, fsa, from_current=False, expand_finals=True,
                 get_state_data=get_default_state_data,
                 get_transition_data=get_default_transition_data):
    
    # Create the product_model
    product_model = Model()
    if from_current:
        product_model.init[(ts.current, wfse.current, fsa.current)] = 1
    else:
        # Iterate over initial states of the TS
        for init_ts in ts.init:
            init_prop = ts.g.node[init_ts].get('prop', set())

            # Iterate over the initial states of the WFSE
            for init_wfse in wfse.init:

                # Iterate over the initial states of the FSA
                    for init_fsa in fsa.init:

                    # Add the initial states to the graph and mark them as initial
                    act_init_wfse = wfse.next_state(init_wfse, init_prop)
                    if act_init_wfse is not None:
                        init_state = (init_ts, act_init_wfse)
                        product_model.init[init_state] = 1
                        init_state_data = get_state_data(init_state, prop=init_prop,
                                                        ts=ts, wfse=wfse)
                        product_model.g.add_node(init_state, **init_state_data)
                        if act_init_wfse in wfse.final:
                            product_model.final.add(init_state)

                    #Initial states of Fsa added to graph and marked as initial

                    act_init_fsa = fsa.next_state(init_fsa, init_prop)
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
        ts_state, wfse_state, fsa_state = cur_state

        # skip processing final beyond final states
        if not expand_finals and fsa_state in fsa.final:
            continue

        #IN PROGRESS !! COME BACK TO IT
        for ts_next_state, ts_cur_state, wfse_next_state, weight, control in ts.next_states_of_wts(ts_state,
                                                     traveling_states=False):
            
            ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
            
            ts_cur_prop = ts.g.node[ts_cur_state].get('prop', set())

            #THIS IS WHERE I USE THE NEXT STATE FUNCTION FROM WFSE
            wfse_next_state = wfse.get_next_states(wfse_state, ts_cur_prop, ts_next_prop, weight) #IS WEIGHT DEFINED IN THIS MODULE?

            #wfse_next_prop = wfse.g.node[wfse_next_state].get('prop', set())
            fsa_next_state = fsa.next_state(fsa_state, wfse_next_prop) # modified that to take the prop from wfse to get next state for fsa
            
            # WFSE:
            if wfse_next_state is not None:
                next_state = (ts_next_state, wfse_next_state) # NOT SURE ABOUT THIS // COME BACK TO IT
                if next_state not in product_model.g:
                    next_prop = wfse.g.node[wfse_next_state].get('prop', set()) 
            
            # THE FOLLOWING BLOCK OF CODE (next 5 lines) BELONGS TO THE ORIGINAL CODE
            if fsa_next_state is not None:
                # TODO: use process_product_transition instead
                next_state = (ts_next_state, fsa_next_state)
                if next_state not in product_model.g:
                    next_prop = ts.g.node[ts_next_state].get('prop', set())
                    
                    # Add the new state
                    next_state_data = get_state_data(next_state, prop=next_prop,
                                                     ts=ts, wfse=wfse,fsa=fsa)
                    product_model.g.add_node(next_state, **next_state_data)
                    
                    # Add transition w/ data
                    transition_data = get_transition_data(cur_state, next_state,
                                weight=weight, control=control, ts=ts, wfse=wfse,fsa=fsa)
                    product_model.g.add_edge(cur_state, next_state,
                                             attr_dict=transition_data)
                    
                    # Mark as final if final in fsa // MAYBE THIS NEEDS MODIFICATION (WE LL SEE)
                    if fsa_next_state in fsa.final:
                        product_model.final.add(next_state)
                    
                    # Continue search from next state
                    stack.append(next_state)
                
                elif next_state not in product_model.g[cur_state]:
                    
                    # Add transition w/ data
                    transition_data = get_transition_data(cur_state, next_state,
                                weight=weight, control=control, ts=ts, wfse=wfse, fsa=fsa)
                    product_model.g.add_edge(cur_state, next_state,
                                             attr_dict=transition_data)

    return product_model

