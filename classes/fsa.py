# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
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

import networkx as nx
import re
import subprocess as sp
import shlex
import operator as op
import logging

from model import Model


# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

ltl2fsa = "ltl2tgba -B -D -s -f '{formula}'"


class Fsa(Model):
    """
    Base class for deterministic finite state automata.
    """
    
    def __init__(self, props=None, directed=True, multi=True):
        """
        LOMAP Fsa Automaton object constructor
        """
        Model.__init__(self, directed=directed, multi=multi)
        
        if type(props) is dict:
            self.props = dict(props)
        else:
            self.props = list(props) if props is not None else []
            # Form the bitmap dictionary of each proposition
            # Note: range goes upto rhs-1
            self.props = dict(zip(self.props, map(lambda x: 2 ** x, range(0, len(self.props)))))

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
        ret = Fsa(self.props, self.directed, self.multi)
        ret.g = self.g.copy()
        ret.name = str(self.name)
        ret.init = dict(self.init)
        ret.final = set(self.final)
        return ret

    @staticmethod
    def infix_formula_to_prefix(formula):
        # This function expects a string where operators and parantheses 
        # are seperated by single spaces, props are lower-case.
        #
        # Tokenizes and reverses the input string.
        # Then, applies the infix to postfix algorithm.
        # Finally, reverses the output string to obtain the prefix string.
        #
        # Infix to postfix algorithm is taken from:
        # http://www.cs.nyu.edu/courses/fall09/V22.0102-002/lectures/InfixToPostfixExamples.pdf
        # http://www.programmersheaven.com/2/Art_Expressions_p1
        #
        # Operator priorities are taken from:
        # Principles of Model Checking by Baier, pg.232
        # http://www.voronkov.com/lics_doc.cgi?what=chapter&n=14
        # Logic in Computer Science by Huth and Ryan, pg.177

        # Operator priorities (higher number means higher priority)
        operators = { "I": 0, "|" : 1, "&": 1, "U": 2, "G": 3, "F": 3, "X": 3, "!": 3};
        output = []
        stack = []

        # Remove leading, trailing, multiple white-space, and
        # split string at whitespaces
        formula = re.sub(r'\s+',' ',formula).strip().split()

        # Reverse the input
        formula.reverse()

        # Invert the parantheses
        for i in range(0,len(formula)):
            if formula[i] == '(':
                formula[i] = ')'
            elif formula[i] == ')':
                formula[i] = '('

        # Infix to postfix conversion
        for entry in formula:

            if entry == ')':
                # Closing paranthesis: Pop from stack until matching '('
                popped = stack.pop()
                while stack and popped != '(':
                    output.append(popped)
                    popped = stack.pop()

            elif entry == '(':
                # Opening paranthesis: Push to stack
                # '(' has the highest precedence when in the input
                stack.append(entry)

            elif entry not in operators:
                # Entry is an operand: append to output
                output.append(entry)

            else:
                # Operator: Push to stack appropriately
                while True:
                    if not stack or stack[-1] == '(':
                        # Push to stack if empty or top is '('
                        # '(' has the lowest precedence when in the stack
                        stack.append(entry)
                        break
                    elif operators[stack[-1]] < operators[entry]:
                        # Push to stack if prio of top of the stack
                        # is lower than the current entry
                        stack.append(entry)
                        break
                    else:
                        # Pop from stack and try again
                        popped = stack.pop()
                        output.append(popped)

        # Pop remaining entries from the stack
        while stack:
            popped = stack.pop()
            output.append(popped)

        # Reverse the order and join entries w/ space
        output.reverse()
        formula = ' '.join(output)

        return formula

    def from_formula(self, formula, load=False):
        """
        Creates a finite state automaton in-place from the given scLTL formula.
        """
        # TODO: check that formula is syntactically co-safe 
        try: # Execute ltl2tgba and get output
            lines = sp.check_output(shlex.split(ltl2fsa.format(
                                                 formula=formula))).splitlines()
        except Exception as ex:
            raise Exception(__name__, "Problem running ltl2tgba: '%s'" % ex)
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
        self.props = dict(zip(props, map(lambda x: 2 ** x, range(0, len(props)))))
        self.name = 'FSA corresponding to formula: %s' % (formula)
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
                self.g.add_edge(this_state, next_state, **{'weight': 0, 'input': bitmaps, 'guard' : guard, 'label': guard})
            elif line[0:4] == 'skip':
                # Add self-looping edge
                self.g.add_edge(this_state, this_state, **{'weight': 0, 'input': self.alphabet, 'guard' : '(1)', 'label': '(1)'})
            else:
                this_state = line[0:-1]
                # Add state
                self.g.add_node(this_state)
                # Mark final or init
                if(this_state.endswith('init')):
                    self.init[this_state] = 1
                if(this_state.startswith('accept')):
                    self.final.add(this_state)

        # We expect a deterministic FSA
        assert(len(self.init)==1)

        return

    def get_guard_bitmap(self, guard):
        """
        Creates the bitmaps from guard string. The guard is a boolean expression
        over the atomic propositions.
        """
        # Get sets for all props
        for key in self.props:
            guard = re.sub(r'\b%s\b' % key, "self.symbols_w_prop('%s')" % key, guard)

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

    def add_trap_state(self):
        """
        Adds a trap state and completes the automaton. Returns True whenever a
        trap state has been added to the automaton.
        """
        trap_added = False
        for s in self.g.nodes():
            rem_alphabet = set(self.alphabet)
            for _, _, d in self.g.out_edges_iter(s, data=True):
                rem_alphabet -= d['input']
            if rem_alphabet:
                if not trap_added: #'trap' not in self.g:
                    self.g.add_node('trap')
                    self.g.add_edge('trap', 'trap', attr_dict={'weight': 0, 'input': self.alphabet, 'guard': '(1)', 'label': '(1)'})
                    trap_added = True
                self.g.add_edge(s,'trap', attr_dict={'weight': 0, 'input': rem_alphabet, 'guard': 'trap_guard', 'label': 'trap_guard'})

        if not trap_added:
            logger.info('No trap states were added.')
        else:
            logger.info('Trap states were added.')
        return trap_added
    
    def remove_trap_states(self):
        '''
        Removes all states of the automaton which do not reach a final state.
        Returns True whenever trap states have been removed from the automaton.
        '''
        # add virtual state which has incoming edges from all final states
        self.g.add_edges_from([(state, 'virtual') for state in self.final])
        # compute trap states
        trap_states = set(self.g.nodes_iter())
        trap_states -= set(nx.shortest_path_length(self.g, target='virtual').iterkeys())
        # remove trap state and virtual state
        self.g.remove_nodes_from(trap_states | set(['virtual']))
        return len(trap_states - set(['virtual'])) == 0

    def symbols_w_prop(self, prop):
        """
        Returns symbols from the automaton's alphabet which contain the given
        atomic proposition.
        """
        return set(filter(lambda symbol: True if self.props[prop] & symbol else False, self.alphabet))

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

    def next_states_of_fsa(self, q, props):
        """
        Returns the next states of state q given input proposition set props. 
        """
        # Get the bitmap representation of props
        prop_bitmap = self.bitmap_of_props(props)
        # Return an array of next states
        return [v for _, v, d in self.g.out_edges_iter(q, data=True)
                                                   if prop_bitmap in d['input']]
