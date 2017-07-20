# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
#               2015-2017, Cristian-Ioan Vasile (cvasile@mit.edu)
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

import re
import subprocess as sp
import shlex
import operator as op
import logging

from .model import Model


# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

ltl2ba = "ltl2tgba -B -s -f '{formula}'"


class Buchi(Model):
    """
    Base class for non-deterministic Buchi automata.
    """

    yaml_tag = u'!Buchi'

    def __init__(self, props=None, multi=True):
        """
        LOMAP Buchi Automaton object constructor
        """
        Model.__init__(self, directed=True, multi=multi)
        
        if type(props) is dict:
            self.props = dict(props)
        else:
            self.props = list(props) if props is not None else []
            # Form the bitmap dictionary of each proposition
            # Note: range goes upto rhs-1
            self.props = dict(zip(self.props,
                                  [2 ** x for x in range(len(self.props))]))

        # Alphabet is the power set of propositions, where each element
        # is a symbol that corresponds to a tuple of propositions
        # Note: range goes upto rhs-1
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
                   init=self.init.keys(), final=self.final,
                   nodes=self.g.nodes(data=True),
                   edges=self.g.edges(data=True))

    def clone(self):
        ret = Buchi(self.props, self.directed, self.multi)
        ret.g = self.g.copy()
        ret.name = str(self.name)
        ret.init = dict(self.init)
        ret.final = set(self.final)
        return ret

    def from_formula(self, formula):
        """
        Creates a Buchi automaton in-place from the given LTL formula.
        """
        try: # Execute ltl2tgba and get output
            lines = sp.check_output(shlex.split(ltl2ba.format(
                                                 formula=formula))).splitlines()
        except Exception as ex:
            raise Exception(__name__, "Problem running ltl2tgba: '{}'".format(ex))
        lines = map(lambda x: x.strip(), lines)
        
        # Get the set of propositions
        # Replace operators [], <>, X, !, (, ), &&, ||, U, ->, <-> G, F, X, R, V
        # with white-space
        props = re.sub(r'[\[\]<>X!\(\)\-&|UGFRV]', ' ', formula)
        # Replace true and false with white space
        props = re.sub(r'\btrue\b', ' ', props)
        props = re.sub(r'\bfalse\b', ' ', props)
        # What remains are propositions seperated by whitespaces
        props = set(props.strip().split())

        # Form the bitmap dictionary of each proposition
        # Note: range goes upto rhs-1
        self.props = dict(zip(self.props,
                              [2 ** x for x in range(len(self.props))]))
        self.name = 'Buchi corresponding to the formula: {}'.format(formula)
        self.final = set()
        self.init = {}

        # Alphabet is the power set of propositions, where each element
        # is a symbol that corresponds to a tuple of propositions
        # Note: range goes upto rhs-1
        self.alphabet = set(range(0, 2 ** len(self.props)))

        # Remove 'never' first line and '}' last line
        del lines[0]
        del lines[-1]

        # remove 'if', 'fi;' lines
        lines = filter(lambda x: x != 'if' and x != 'fi;', lines)

        # '::.*' means transition, '.*:' means state
        # print '\n'.join(lines)
        # print "\n"
        this_state = None
        for line in lines:
            if(line[0:2] == '::'):
                m = re.search(':: (.*) -> goto (.*)', line)
                guard = m.group(1)
                bitmaps = self.get_guard_bitmap(guard)
                next_state = m.group(2)
                # Add edge
                attr_dict = {'weight': 0, 'input': bitmaps,
                             'guard' : guard, 'label': guard}
                self.g.add_edge(this_state, next_state, **attr_dict)
            elif line[0:4] == 'skip':
                # Add self-looping edge
                attr_dict = {'weight': 0, 'input': self.alphabet,
                             'guard' : '(1)', 'label': '(1)'}
                self.g.add_edge(this_state, this_state, **attr_dict)
            else:
                this_state = line[0:-1]
                # Add state
                self.g.add_node(this_state)
                # Mark final or init
                if(this_state.endswith('init')):
                    self.init[this_state] = 1
                if(this_state.startswith('accept')):
                    self.final.add(this_state)

    def get_guard_bitmap(self, guard):
        """
        Creates the bitmaps from guard string. The guard is a boolean expression
        over the atomic propositions.
        """
        # Get sets for all props
        for key in self.props:
            guard = re.sub(r'\b{}\b'.format(key),
                           "self.symbols_w_prop('{}')".format(key),
                           guard)

        # Handle (1)
        guard = re.sub(r'\(1\)', 'self.alphabet', guard)
        # Handle (0)
        guard = re.sub(r'\(0\)', 'set()', guard)

        # Handler negated sets #FIXME: this might not work in the future.
        guard = re.sub('!self.symbols_w_prop', 'self.symbols_wo_prop', guard)
        guard = re.sub('!\(self.symbols_w_prop', '(self.symbols_wo_prop', guard)

        # Convert logic connectives
        guard = re.sub(r'\&\&', '&', guard)
        guard = re.sub(r'\|\|', '|', guard)

        return eval(guard)

    def symbols_w_prop(self, prop):
        """
        Returns symbols from the automaton's alphabet which contain the given
        atomic proposition.
        """
        bitmap = self.props[prop]
        return set([symbol for symbol in self.alphabet if bitmap & symbol])

    def symbols_wo_prop(self, prop):
        """
        Returns symbols from the automaton's alphabet which does not contain the
        given atomic proposition.
        """
        return self.alphabet.difference(self.symbols_w_prop(prop))

    def bitmap_of_props(self, props):
        """
        Returns bitmap corresponding the set of atomic propositions.
        """
        return reduce(op.or_, [self.props.get(p, 0) for p in props], 0)

    def next_states(self, q, props):
        """
        Returns the next states of state q given input proposition set props. 
        """
        # Get the bitmap representation of props
        prop_bitmap = self.bitmap_of_props(props)
        # Return an array of next states
        return [v for _, v, d in self.g.out_edges_iter(q, data=True)
                                                   if prop_bitmap in d['input']]
