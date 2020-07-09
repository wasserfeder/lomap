#! /usr/local/bin/python3
from __future__ import print_function

# Defining the weighted error system:
# IN PROGRESS
# Description: the weighted finite e-system computes the difference between 2 words

# Imports 
import re
import random
import subprocess as sp
import shlex
import operator as op
import logging
import networkx as nx

import itertools as it

import lomap 
from lomap.classes import Fsa
from lomap.classes import Model

#from lomap.algorithms.product

# Logger configuration
logger = logging.getLogger(__name__)

# subclass of Fsa, which is the base class for deterministic finite state automata
# UNDER CONSTRUCTION !!
# This is a Fsa subclass that returns a Wfse object. 
# Wfse: weighted finite state e-system
# It is a pair beta : a trim e-NFA and a weight function of beta


# This class constructs a DFA (a trim e-NFA) and the weight function of beta

class Wfse(Fsa):
   
    yaml_tag = u'!Wfse'

    def __init__(self, props= None, multi= True):
        
        if type(props) is dict:
            self.props = dict(props)
        else:
            self.props = list(props) if props is not None else []
            # Form the bitmap dictionary of each proposition
            # Note: range goes upto rhs-1
            self.props = dict(list(zip(self.props,
                                  [2 ** x for x in range(len(self.props))])))

        #The alphabet is a subset of the alphabet of edit operations
        self.alphabet = set(it.product(range(-1,2**len(self.props)), repeat=2)) - {(-1,-1)}

    def __repr__(self):
        return '''
Name: {name}
Directed: {directed}
Multi: {multi}
Props: {props}
Alphabet: {alphabet} 
Initial: {init}
Final: {final}
Nodes: {nodes}
Edges: {edges}
        '''.format(name=self.name, directed=self.directed, multi=self.multi,
                   props=self.props, alphabet=self.alphabet,
                   init=list(self.init.keys()), final=self.final,
                   nodes=self.g.nodes(data=True),
                   edges=self.g.edges(data=True))

    @staticmethod
   
    def determinize(self):
        
        # Powerset construction

        # The new deterministic automaton
        det = Wfse()

        # List of state sets
        state_map = []

        # New initial state
        state_map.append(set(self.init))
        det.init[0] = 1

        # Copy the old alphabet
        det.alphabet = set(self.alphabet)

        # Copy the old props
        det.props = dict(self.props)

        # Discover states and transitions
        stack = [0]
        done = set()
        while stack:
            cur_state_i = stack.pop()
            cur_state_set = state_map[cur_state_i]
            
            weight_var = 0
            weight = weight_function(weight_var)
            
            next_states = get_next_states(cur_state_i, props, props, weight)
            #next_states = dict() 

            for cur_state in cur_state_set:
                for _,next_state,data in self.g.out_edges_iter(cur_state, True):
                    inp = next(iter(data['input']))
                    if inp not in next_states:
                        next_states[inp] = set()
                    next_states[inp].add(next_state)

            for inp,next_state_set in next_states.items():
                if next_state_set not in state_map:
                    state_map.append(next_state_set)
                next_state_i = state_map.index(next_state_set)

                # USING THE WEIGHT FUNCTION
                attr_dict = {'weight':weight_function(weight_var), 'label':inp, 'input':set([inp])}

                det.g.add_edge(cur_state_i, next_state_i, **attr_dict)
                if next_state_i not in done:
                    stack.append(next_state_i)
                    done.add(next_state_i)

        # Sanity check
        # All edges of all states must be deterministic
        for state in det.g:
            ins = set()
            for _, _, d in det.g.out_edges_iter(state, True):
                assert len(d['input']) == 1
                inp = next(iter(d['input']))
                if inp in ins:
                    assert False
                ins.add(inp)

        # Mark final states
        for state_i, state_set in enumerate(state_map):
            if state_set & self.final:
                det.final.add(state_i)

        return det

    
    # Weight Function of beta that assigns a non-negative real number to every transition of the e-NFA
    # weight: is the non-negative real number that needs to be assigned to every transition // possibly a list or tuple
    def weight_function(weight):
       weight = random.randrange(0, 100,1)
       return weight


    # I BELIEVE THE NEXT STATE FUNCTION SHOULD BE HERE 
    # Next state function:
    # UNDER CONSTRUCTION

    def get_next_states(self, state, input_props, output_props): 

        input_bitmap = self.bitmap_of_props(input_props) # this is the set of props/labels that come w the fsa states (a,b,ab,empty), it indicates current stat

        transitions = self.g.out_edges_iter(state, data = True)
        # TODO: finish up with the tuples !! / get the tuples as the output: output_symbol, weight, next_state!
        
        output_bitmap = self.bitmap_of_props(output_props)
        return (transitions, output_bitmap) # the function returns a tuple with the output_symbol, the next state
        