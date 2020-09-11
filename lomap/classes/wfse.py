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

import logging
import itertools as it

import networkx as nx

from lomap.classes import Fsa


# Logger configuration
logger = logging.getLogger(__name__)


class Wfse(Fsa):
    '''TODO:
    Wfse: weighted finite state e-system
    This class constructs a DFA (a trim e-NFA) and the weight function of beta

    Subclass of Fsa, which is the base class for deterministic finite state automata
    '''

    yaml_tag = u'!Wfse'

    def __init__(self, name='WFSE', props=None, multi=False):
        '''TODO:
        '''
        Fsa.__init__(self, name=name, props=(), multi=multi)
        if type(props) is dict:
            self.props = dict(props)
        else:
            self.props = list(props) if props is not None else []
            # Form the bitmap dictionary of each proposition
            # Note: range goes upto rhs-1
            self.props = dict(list(zip(self.props,
                                  [2 ** x for x in range(len(self.props))])))

        #The alphabet is a subset of the alphabet of edit operations
        self.prop_bitmaps = range(-1, 2**len(self.props))
        self.alphabet = set(it.product(self.prop_bitmaps, repeat=2)) - {(-1,-1)}

    def next_states(self, state, input_props):
        '''TODO:
        '''
        # the input symbol
        if input_props is None:
            input_bitmap = -1
        else:
            input_bitmap = self.bitmap_of_props(input_props)

        output = []
        for _, v, d in self.g.out_edges_iter(state, data=True):
            for in_bitmap, out_bitmap, weight in d['symbols']:
                if in_bitmap == input_bitmap:
                    out_symbol = self.symbol_from_bitmap(out_bitmap)
                    output.append((v, out_symbol, weight))

        return output
