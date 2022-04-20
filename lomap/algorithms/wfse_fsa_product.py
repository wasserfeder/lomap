# Copyright (C) 2020, Cristian-Ioan Vasile (cvasile@lehigh.edu)
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

from __future__ import print_function
import itertools as it
from functools import reduce
import operator as op
import logging
from collections import deque
from lomap import Timer
from lomap.classes import Model
from lomap.algorithms.product import get_default_state_data, get_default_transition_data
import networkx as nx
import matplotlib.pyplot as plt
import time
from linetimer import CodeTimer



# Logger configuration
logger = logging.getLogger(__name__)


def ts_times_wfse_times_fsa(ts, wfse, fsa, from_current=False,
                            expand_finals=True,
                            get_state_data=get_default_state_data,
                            get_transition_data=get_default_transition_data):
    '''
    TODO: 3-way product
    '''

    # Create the product_model

    product_model = Model(multi=False)
    product_model.init = set() # Make initial a set
    if from_current:
        product_model.init.add((ts.current, wfse.current, fsa.current))
    else:
        # Iterate over initial states of the TS
        for init_ts in ts.init:
            init_prop = ts.g.node[init_ts].get('prop', set())
            # Iterate over the initial states of the WFSE
            for init_wfse in wfse.init:
                for wfse_out in wfse.next_states(init_wfse, init_prop):
                    act_init_wfse, init_prop_relax, weight_relax = wfse_out
                    # Iterate over the initial states of the FSA
                    for init_fsa in fsa.init:
                        # Add the initial states to the graph and mark them as
                        # initial
                        act_init_fsa = fsa.next_state(init_fsa, init_prop_relax)
                        if act_init_fsa is not None:
                            init_state = (init_ts, act_init_wfse, act_init_fsa)
                            prop = (init_prop, init_prop_relax)
                            product_model.init.add(init_state)
                            product_model.g.add_node(init_state,
                                                     weight=weight_relax,
                                                     prop=prop)
                            if (act_init_fsa in fsa.final
                                and act_init_wfse in wfse.final):
                                product_model.final.add(init_state)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    start_stack = time.process_time()
    count = 0

    # with CodeTimer('while'):
    while stack:
        count = count + 1

        # print("stack length:", len(stack))
        current_state = stack.pop()
        ts_state, wfse_state, fsa_state = current_state
        # print("current_state:", current_state)

        # skip processing final beyond final states
        if (not expand_finals
            and fsa_state in fsa.final
            and wfse_state in wfse.final):
            continue
        # count =  0
        start_ts = time.process_time()


        # with CodeTimer('for'):
        for ts_next_state in it.chain(ts.g[ts_state], (None,)):
            count += 1
            if ts_next_state is None:
                ts_next_state = ts_state
                ts_next_prop = None
                ts_weight = 1
            else:

                # with CodeTimer('get_prop_weight'):
                ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
                # ts_weight = ts.g.node[ts_next_state].get('weight', 1)      ## Original implementation
                ts_weight = ts.g[current_state[0]][ts_next_state]["weight"]  ## Modified implementation

                # print ("ts_weight : ", ts_weight, ts_next_state)
            # print("next_states in WFSE:", len(wfse.next_states(wfse_state, ts_next_prop)))


            # with CodeTimer('inner for'):
            for wfse_out in wfse.next_states(wfse_state, ts_next_prop):

                count += 1

                wfse_next_state, next_prop_relax, wfse_weight = wfse_out

                ## The following modification takes care of the PA weights for deletion case [phantom transitions]

                # with CodeTimer('in_sym'):
                wfse_in_sym = wfse.g[wfse_state][wfse_next_state]["symbols"]

                conditional_start = time.process_time()

                if next_prop_relax is None:
                    fsa_next_state = fsa_state
                else:
                    fsa_next_state = fsa.next_state(fsa_state, next_prop_relax)
                if fsa_next_state is not None:
                    next_state = (ts_next_state, wfse_next_state,
                                  fsa_next_state)
                    weight = ts_weight * wfse_weight

                    if wfse_in_sym == -1:
                        weight = wfse_weight
                    # print("product_weight:", weight)

                    prop = (ts_next_prop, next_prop_relax)

                    # with CodeTimer('conditionals'):

                    if next_state not in product_model.g:

                        # with CodeTimer('if'):
                        # Add the new state
                        product_model.g.add_node(next_state)
                        # Add weighted transition
                        product_model.g.add_edge(current_state, next_state,
                                                 weight=weight, prop=prop)
                        # Mark as final if final in fsa
                        if (fsa_next_state in fsa.final
                            and wfse_next_state in wfse.final):
                            product_model.final.add(next_state)
                        # Continue search from next state
                        stack.append(next_state)
                    elif next_state not in product_model.g[current_state]:

                        # with CodeTimer('elif'):
                        # count = count + 1

                        # Add weighted transition
                        # with CodeTimer('weights'):

                        weight = ts_weight * wfse_weight

                        # with CodeTimer('add edge'):
                        product_model.g.add_edge(current_state, next_state,
                                                 weight=weight, prop=prop)
                    else:
                        # with CodeTimer('else'):

                        # Update weighted transition
                        data = product_model.g[current_state][next_state]
                        weight = ts_weight * wfse_weight
                        if data['weight'] > weight:
                            data['weight'] = weight
                            data['prop'] = prop

                    conditional_end = time.process_time()
            # nx.draw(product_model.g, with_labels= True)
            # plt.show()
        end_ts = time.process_time()
    end_stack = time.process_time()

    time_stack = end_stack - start_stack
    time_ts = end_ts - start_ts


    # print("time_stack:", end_stack - start_stack)
    # print("time_ts:", end_ts - start_ts)
    # print("stack iterations:", count)
    # print("conditions:", conditional_end - conditional_start)

    return product_model


def ts_times_wfse_times_fsa_pareto(ts, wfse, fsa, from_current=False,
                                expand_finals=True,
                                get_state_data=get_default_state_data,
                                get_transition_data=get_default_transition_data):
        '''
        TODO: 3-way product
        '''

        # Create the product_model

        product_model = Model(multi=False)
        product_model.init = set() # Make initial a set
        if from_current:
            product_model.init.add((ts.current, wfse.current, fsa.current))
        else:
            # Iterate over initial states of the TS
            for init_ts in ts.init:
                init_prop = ts.g.node[init_ts].get('prop', set())
                # Iterate over the initial states of the WFSE
                for init_wfse in wfse.init:
                    for wfse_out in wfse.next_states(init_wfse, init_prop):
                        act_init_wfse, init_prop_relax, weight_relax = wfse_out
                        # Iterate over the initial states of the FSA
                        for init_fsa in fsa.init:
                            # Add the initial states to the graph and mark them as
                            # initial
                            act_init_fsa = fsa.next_state(init_fsa, init_prop_relax)
                            if act_init_fsa is not None:
                                init_state = (init_ts, act_init_wfse, act_init_fsa)
                                prop = (init_prop, init_prop_relax)
                                product_model.init.add(init_state)
                                product_model.g.add_node(init_state,
                                                         weight=weight_relax,
                                                         prop=prop)
                                if (act_init_fsa in fsa.final
                                    and act_init_wfse in wfse.final):
                                    product_model.final.add(init_state)

        # Add all initial states to the stack
        stack = deque(product_model.init)
        # Consume the stack
        while stack:
            current_state = stack.pop()
            ts_state, wfse_state, fsa_state = current_state

            # skip processing final beyond final states
            if (not expand_finals
                and fsa_state in fsa.final
                and wfse_state in wfse.final):
                continue

            for ts_next_state in it.chain(ts.g[ts_state], (None,)):
                if ts_next_state is None:
                    ts_next_state = ts_state
                    ts_next_prop = None
                    ts_weight = 1
                else:
                    ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
                    # ts_weight = ts.g.node[ts_next_state].get('weight', 1)      ## Original implementation
                    ts_weight = ts.g[current_state[0]][ts_next_state]["weight"]  ## Modified implementation

                    # print ("ts_weight : ", ts_weight, ts_next_state)

                for wfse_out in wfse.next_states(wfse_state, ts_next_prop):
                    wfse_next_state, next_prop_relax, wfse_weight = wfse_out
                    if next_prop_relax is None:
                        fsa_next_state = fsa_state
                    else:
                        fsa_next_state = fsa.next_state(fsa_state, next_prop_relax)
                    if fsa_next_state is not None:
                        next_state = (ts_next_state, wfse_next_state,
                                      fsa_next_state)

                        ## ------------------Modified weight definition --------------------------

                        weight = wfse_weight
                        # print("product_weight:", weight)

                        ## ----------------------------------------------------------------------

                        prop = (ts_next_prop, next_prop_relax)

                        if next_state not in product_model.g:
                            # Add the new state
                            product_model.g.add_node(next_state)
                            # Add weighted transition
                            product_model.g.add_edge(current_state, next_state,
                                                     weight=weight, prop=prop)
                            # Mark as final if final in fsa
                            if (fsa_next_state in fsa.final
                                and wfse_next_state in wfse.final):
                                product_model.final.add(next_state)
                            # Continue search from next state
                            stack.append(next_state)
                        elif next_state not in product_model.g[current_state]:
                            # Add weighted transition
                            weight = ts_weight * wfse_weight
                            product_model.g.add_edge(current_state, next_state,
                                                     weight=weight, prop=prop)
                        else:
                            # Update weighted transition
                            data = product_model.g[current_state][next_state]
                            weight = ts_weight * wfse_weight
                            if data['weight'] > weight:
                                data['weight'] = weight
                                data['prop'] = prop


            # nx.draw(product_model.g, with_labels= True)
            # plt.show()

        return product_model


def wfse_times_fsa(wfse, fsa, from_current=False,
                            expand_finals=True,
                            get_state_data=get_default_state_data,
                            get_transition_data=get_default_transition_data):
    '''
    TODO: wfse and fsa product
    '''
    # Create the product_model

    print("fsa:", fsa)

    product_model = Model(multi=False)
    product_model.init = set() # Make initial a set # Hack
    if from_current:
        product_model.init.add((wfse.current, fsa.current))
    else:
        print("wfse props:", wfse.props)

        ''' Add initial states to the product model
        The set of initial states is the cartesian product of 
        init states in WFSE and FSA'''

        for init_wfse in wfse.init:
            for init_fsa in fsa.init:
                product_model.init.add((init_wfse, init_fsa))
                print("product_init:", product_model.init)

        for symbol in wfse.props:
            # Iterate over the initial states of the WFSE
            for init_wfse in wfse.init:
                for wfse_out in wfse.next_states(init_wfse, symbol):
                    act_init_wfse, init_prop_relax, weight_relax = wfse_out
                    # Iterate over the initial states of the FSA
                    for init_fsa in fsa.init:
                        print("init_fsa:", init_fsa)
                        # Add the initial states to the graph and mark them as
                        # initial
                        act_init_fsa = fsa.next_state(init_fsa, init_prop_relax)
                        if act_init_fsa is not None:
                            init_state = (act_init_wfse, act_init_fsa)
                            print("prod_state:", init_state)
                            prop = (init_prop_relax)                            # removed init prop (TS) from here
                            # product_model.add(init_state)
                            product_model.g.add_node(init_state,
                                                     weight=weight_relax,
                                                     prop=prop)
                            if (act_init_fsa in fsa.final
                                and act_init_wfse in wfse.final):
                                product_model.final.add(init_state)

    # Add all initial states to the stack
    stack = deque(product_model.init)
    # Consume the stack
    # start_stack = time.process_time()
    count = 0

    # with CodeTimer('while'):
    while stack:
        count = count + 1

        print("stack length:", len(stack))
        current_state = stack.pop()
        wfse_state, fsa_state = current_state
        print("current_state:", current_state)

        # skip processing final beyond final states
        if (not expand_finals
            and fsa_state in fsa.final
            and wfse_state in wfse.final):
            continue
        # count =  0
        # start_ts = time.process_time()

        for symbol in wfse.props:
            print("sym:",symbol)

        # with CodeTimer('for'):
        # for symbol in it.chain(ts.g[ts_state], (None,)):
            # count += 1
            # if ts_next_state is None:
            #     ts_next_state = ts_state
            #     ts_next_prop = None
            #     ts_weight = 1
            # else:
            #
            #     # with CodeTimer('get_prop_weight'):
            #     ts_next_prop = ts.g.node[ts_next_state].get('prop', set())
            #     # ts_weight = ts.g.node[ts_next_state].get('weight', 1)      ## Original implementation
            #     ts_weight = ts.g[current_state[0]][ts_next_state]["weight"]  ## Modified implementation
            #
            #     # print ("ts_weight : ", ts_weight, ts_next_state)
            # # print("next_states in WFSE:", len(wfse.next_states(wfse_state, ts_next_prop)))


            # with CodeTimer('inner for'):



            ## Iterate over the propositions (actual and relaxed) - iter.chain(wfse.g[wfse_state].get('prop', set()) and the corresponding wfse_next_state
            ## For the relaxed proposition, get fsa_nxt_state and add these two to the product
            for wfse_out in wfse.next_states(wfse_state, symbol):

                count += 1

                wfse_next_state, next_prop_relax, wfse_weight = wfse_out

                print("wfse_next, wfse_prop_relax", wfse_next_state, next_prop_relax)

                ## The following modification takes care of the PA weights for deletion case [phantom transitions]

                # with CodeTimer('in_sym'):
                wfse_in_sym = wfse.g[wfse_state][wfse_next_state]["symbols"]

                # conditional_start = time.process_time()

                if next_prop_relax is None:
                    fsa_next_state = fsa_state
                else:
                    fsa_next_state = fsa.next_state(fsa_state, next_prop_relax)
                if fsa_next_state is not None:
                    next_state = (wfse_next_state,
                                  fsa_next_state)
                    weight = wfse_weight

                    # print("product_weight:", weight)

                    prop =  next_prop_relax

                    # with CodeTimer('conditionals'):
                    print("next_state:", next_state)
                    print("product_states:", product_model.g.nodes())
                    if next_state not in product_model.g:

                        # with CodeTimer('if'):
                        # Add the new state
                        product_model.g.add_node(next_state)
                        # Add weighted transition
                        product_model.g.add_edge(current_state, next_state,
                                                 weight=weight, prop=prop)
                        # Mark as final if final in fsa
                        if (fsa_next_state in fsa.final
                            and wfse_next_state in wfse.final):
                            product_model.final.add(next_state)
                        # Continue search from next state
                        stack.append(next_state)
                    # elif next_state not in product_model.g[current_state]:
                    #
                    #     # with CodeTimer('elif'):
                    #     # count = count + 1
                    #
                    #     # Add weighted transition
                    #     # with CodeTimer('weights'):
                    #
                    #     weight = wfse_weight
                    #
                    #     # with CodeTimer('add edge'):
                    #     product_model.g.add_edge(current_state, next_state,
                    #                              weight=weight, prop=prop)
                    else:
                        # with CodeTimer('else'):

                        # Update weighted transition
                        data = product_model.g[current_state][next_state]
                        weight = wfse_weight
                        if data['weight'] > weight:
                            data['weight'] = weight
                            data['prop'] = prop

                    # conditional_end = time.process_time()
    nx.draw(product_model.g, with_labels= True)
    plt.show()
    #     end_ts = time.process_time()
    # end_stack = time.process_time()
    #
    # time_stack = end_stack - start_stack
    # time_ts = end_ts - start_ts


    # print("time_stack:", end_stack - start_stack)
    # print("time_ts:", end_ts - start_ts)
    # print("stack iterations:", count)
    # print("conditions:", conditional_end - conditional_start)

    return product_model
