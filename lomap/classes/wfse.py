#! /usr/bin/python

# Defining the weighted error system:
# IN PROGRESS
# Description: the weighted finite e-system computes the difference between 2 words

# Imports 
import re
import subprocess as sp
import shlex
import operator as op
import logging
from __future__ import print_function
import networkx as nx

import lomap 
from lomap.classes.fsa import Fsa

from lomap.algorithms.product

# Logger configuration
logger = logging.getLogger(__name__)

# subclass of Fsa, which is the base class for deterministic finite state automata
# UNDER CONSTRUCTION !!
# This is a Fsa subclass that returns a Wfse object. 
# Wfse: weighted finite state e-system
# It is a pair beta : a trim e-NFA and a weight function of beta


# This class constructs a trim e-NFA and the weight function of beta

# Modify the DFA class to turn it into a trim e-NFA
class Wfse(Fsa):
   
    yaml_tag = u'!Wfse'

    def __init__(self, props= None, multi= True):
        
        #The alphabet is a subset of the alphabet of edit operations
        self.alphabet = set(range(0, 2 ** len(self.props)))

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
   
    def non_determinize(self):
        
        # Powerset construction

        # The new NON-deterministic automaton
        non_det = Wfse()

        # List of state sets
        state_map = []

        # New initial state
        state_map.append(set(self.init))
        non_det.init[0] = 1

        # Copy the old alphabet
        non_det.alphabet = set(self.alphabet)

        # Copy the old props
        non_det.props = dict(self.props)

        # Discover states and transitions
        stack = [0]
        done = set()
        while stack:
            cur_state_i = stack.pop()
            cur_state_set = state_map[cur_state_i]
            next_states = dict()
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
                attr_dict = {'weight':0, 'label':inp, 'input':set([inp])}
                non_det.g.add_edge(cur_state_i, next_state_i, **attr_dict)
                if next_state_i not in done:
                    stack.append(next_state_i)
                    done.add(next_state_i)

        # Sanity check
        # All edges of all states must be deterministic
        for state in non_det.g:
            ins = set()
            for _, _, d in non_det.g.out_edges_iter(state, True):
                assert len(d['input']) == 1
                inp = next(iter(d['input']))
                if inp in ins:
                    assert False
                ins.add(inp)

        # Mark final states
        for state_i, state_set in enumerate(state_map):
            if state_set & self.final:
                non_det.final.add(state_i)

        return non_det

    
    # Weight Function of beta that assigns a non-negative real number to every transition of the e-NFA
    def weight_function(self, weight, transition, number_of_transitions): # come back to this line 

       # weight: is the non-negative real number that needs to be assigned to the every transition // possibly a list or tuple
       # transition: each different edges that is reached while the NFA is executed
       # number_of_transitions: the number of all edges 
       # maybe: construct a while loop that will itereate through the transitions and assign a 'weight' to each edge

    