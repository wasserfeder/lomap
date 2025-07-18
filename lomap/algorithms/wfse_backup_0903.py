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
from lomap.classes import Model, Fsa
from lomap.algorithms.product import get_default_state_data, get_default_transition_data
import networkx as nx
import matplotlib.pyplot as plt
import time
# from linetimer import CodeTimer
from itertools import chain


# Logger configuration
logger = logging.getLogger(__name__)

def powerset(iterable):
    '''powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    Note: from https://docs.python.org/2.7/library/itertools.html#recipes
    '''
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r)
                                                      for r in range(len(s)+1))

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
                        print("act_init_fsa:", act_init_fsa)
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
    # start_stack = time.process_time()
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
        # start_ts = time.process_time()


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
                print("next prop relax: ", next_prop_relax)
                # with CodeTimer('in_sym'):
                wfse_in_sym = wfse.g[wfse_state][wfse_next_state]["symbols"]
                print("wfse in sym: ", wfse_in_sym)
                # conditional_start = time.process_time()

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
                        print("weights are correct")
                        # Update weighted transition
                        data = product_model.g[current_state][next_state]
                        weight = ts_weight * wfse_weight
                        if data['weight'] > weight:
                            data['weight'] = weight
                            data['prop'] = prop

                    # conditional_end = time.process_time()

        # end_ts = time.process_time()
    # end_stack = time.process_time()
    nx.draw(product_model.g, with_labels=True)
    plt.show()
    # time_stack = end_stack - start_stack
    # time_ts = end_ts - start_ts


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


        nx.draw(product_model.g, with_labels= True)
        plt.show()

        return product_model



def wfse_times_fsa(wfse, fsa, from_current=False,
                            expand_finals=True):
    '''
    wfse and fsa product: Disha

        Parameters
    ----------
    wfse: tuple
        iterable of LOMAP weighted finite state automaton

    fsa: LOMAP deterministic finite state automata

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
    product_automaton


    '''
    # Create the product_model
    print("======= start product ==============")
    print("fsa within product:", fsa)

    product_model = Model(multi=True)
    product_model.init = set() # Make initial a set # Hack
    if from_current:
        product_model.init.add((wfse.current, fsa.current))
    else:
        assert all([len(fsa.init) == 1])

        for wfse_init in wfse.init:
            for fsa_init in fsa.init:
                init_state = (wfse_init, fsa_init)

                # print("-------------------product begins-----------------------")
                print("wfse init : ", wfse_init)
                print("fsa init : ", fsa_init)
                product_model.init.add(init_state)
                product_model.g.add_node(init_state)

        print(next(iter(product_model.init)))
        print("wfse props:", wfse.props)

        print("wfse edges:", wfse.g.edges(data=True))

        ''' Add initial states to the product model
        The set of initial states is the cartesian product of 
        init states in WFSE and FSA'''

    stack = deque([init_state])
    # Add all initial states to the stack
    stack = deque(product_model.init)
    print("stack:",stack)
    # Consume the stack
    # start_stack = time.process_time()
    count = 0


    # with CodeTimer('while'):
    while stack:
        # count = count + 1

        # print("stack length:", len(stack))
        current_state = stack.pop()
        wfse_state, fsa_state = current_state
        # print("current_state:", current_state)
        # skip processing final beyond final states
        if (not expand_finals
            and fsa_state in fsa.final
            and wfse_state in wfse.final):
            product_model.final.add((wfse_state, fsa_state))
            continue
        # count =  0
        # start_ts = time.process_time()

        # for symbol in wfse.props:
            # print("sym:",symbol)
            # print("next:",  wfse.next_states(wfse_state, symbol))
        outgoing_edges = wfse.g.out_edges(wfse_state, data=True)
            # print("out:", outgoing_edges)

        for each_edge in outgoing_edges:
            wfse_next, in_sym, out_sym = each_edge
            edge_data = wfse.g.get_edge_data(wfse_state, wfse_next)
            print("edge data: ", edge_data)
            for each_edge in edge_data['attr_dict']['symbols']:
                in_prop, out_prop, weight = each_edge
                # print("check syms: ", next_state, in_sym,  out_sym)
                print("in out props", in_prop, out_prop)
                # print(fsa.g.edges(data=True))
                fsa_next = fsa.next_state(fsa_state, str(out_prop))
                print("fsa next:", fsa_next)

                if fsa_next in fsa.final and wfse_next in wfse_next.final:
                    product_model.final.add(wfse_next, fsa_next)
                    print("getting here")
                    continue
                product_model.g.add_edge(wfse_next, fsa_next, weight = weight, prop = out_prop)

        print("fsa final:", fsa.final)
        print("wfse final:", wfse.final)
        print("=================",product_model.final)


    return product_model


def pfsa_default_transition_data(current_state, next_state, guard, bitmaps,
                                 fsa_tuple):
    '''Returns the default data to store for a transition of a product FSA.'''
    return {'weight': 0, 'input': bitmaps, 'guard' : guard, 'label': guard}


def new_wfse_times_fsa(wfse, fsa,  from_current=False, expand_finals=True,
                       get_transition_data=pfsa_default_transition_data):
    automata = [wfse, fsa]

    # set of APs in product
    # product_props = set(wfse.props).union(set(fsa.props))
    product_props = set.union(*[set(component.props) for component in automata])

    print("prodcut_props: ", product_props)
    print("wfse: ",wfse.props)
    # Create the product_model
    product_model = Fsa(product_props, multi=False)
    product_model.init = set()  # Make initial a set

    for init_wfse in wfse.init:
        for init_fsa in fsa.init:
            init_state = (init_wfse, init_fsa)
            product_model.init.add((init_wfse, init_fsa))

    ## testing the bitmaps of the props in the product model
    for each_prop in powerset(product_model.props):
        print("bits:", product_model.bitmap_of_props(each_prop))

    stack = deque(product_model.init)

    get_state_data_ = lambda state: get_state_data(state, fsa_tuple=fsa_tuple)

    while stack:

        # current_state, neighbors = stack.popleft()
        current_state = stack.popleft()
        wfse_current, fsa_current = current_state

        if all([s in fsa.final for s, fsa in zip(current_state, automata)]):
            product_model.final.add(current_state)

        # Iterate over all possible transitions

        for each_edge in wfse.g.out_edges_iter(wfse_current, data=True):
            wfse_next_state, in_sym, out_sym = each_edge

            wfse_in_sym = wfse.g[wfse_current][wfse_next_state]["symbols"]
            print("in sym:", wfse_in_sym)

            edge_data = wfse.g.get_edge_data(wfse_current, wfse_next_state)

            print("edge data: ", edge_data)
            for each_edge in edge_data['symbols']:
                in_prop, out_prop, wfse_weight = each_edge
                # print("check syms: ", next_state, in_sym,  out_sym)
                in_symbol = wfse.symbol_from_bitmap(in_prop)
                out_symbol = wfse.symbol_from_bitmap(out_prop)
                prop = (in_prop, out_prop)

                if out_symbol is None:
                    fsa_next_state = fsa_state
                else:
                    fsa_next_state = fsa.next_state(fsa_current, out_symbol)

                if fsa_next_state is not None:
                    next_state = (wfse_next_state,
                                  fsa_next_state)
                    weight = wfse_weight

                    if next_state not in product_model.g:
                        # with CodeTimer('if'):
                        # Add the new state
                        product_model.g.add_node(next_state)
                        # Add weighted transition
                        product_model.g.add_edge(current_state, next_state,
                                                 weight=weight, prop=prop, symbols = (in_symbol, out_symbol))
                        # Mark as final if final in fsa
                        if (fsa_next_state in fsa.final
                            and wfse_next_state in wfse.final):

                            product_model.final.add(next_state)

                        # Continue search from next state
                        stack.append(next_state)

                    elif next_state not in product_model.g[current_state]:

                        product_model.g.add_edge(current_state, next_state,
                                                 weight = weight, prop=prop, symbols = (in_symbol, out_symbol))


    return product_model