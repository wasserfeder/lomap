# Defining the weighted error system:
# IN PROGRESS
# Description: the weighted finite e-system computes the difference between 2 words

import logging
import itertools as it

import networkx as nx

from lomap.classes import Fsa


# Logger configuration
logger = logging.getLogger(__name__)


class Wfse(Fsa):
    '''TODO:
    This class constructs a DFA (a trim e-NFA) and the weight function of beta

    subclass of Fsa, which is the base class for deterministic finite state automata
    UNDER CONSTRUCTION !!
    This is a Fsa subclass that returns a Wfse object.
    Wfse: weighted finite state e-system
    It is a pair beta : a trim e-NFA and a weight function of beta
    '''

    yaml_tag = u'!Wfse'

    def __init__(self, props=None, multi=True):
        '''TODO:
        '''
        Fsa.__init__(self, props=(), multi=multi)
        if type(props) is dict:
            self.props = dict(props)
        else:
            self.props = list(props) if props is not None else []
            # Form the bitmap dictionary of each proposition
            # Note: range goes upto rhs-1
            self.props = dict(list(zip(self.props,
                                  [2 ** x for x in range(len(self.props))])))

        #The alphabet is a subset of the alphabet of edit operations
        prop_bitmaps = range(-1, 2**len(self.props))
        self.alphabet = set(it.product(prop_bitmaps, repeat=2)) - {(-1,-1)}

    def next_states(self, state, input_props, output_props):
        '''TODO:
        '''
        # the input symbol
        input_bitmap = self.bitmap_of_props(input_props)

        output = []
        for _, v, d in self.g.out_edges_iter(state, data=True):
            for in_symbol, out_symbol, weight in d['symbols']:
                if in_symbol == input_bitmap:
                    output.append((v, out_symbol, weight))

        return output
