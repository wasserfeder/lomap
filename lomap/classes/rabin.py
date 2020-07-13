# Copyright (C) 2015-2017, Cristian-Ioan Vasile (cvasile@bu.edu)
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
#from builtins import next
#from builtins import str
#from builtins import zip
#from builtins import range
import re
import subprocess as sp
import shlex
from collections import deque, defaultdict
import operator as op
import logging
from copy import deepcopy

import networkx as nx

from lomap.classes.model import Model
from functools import reduce

# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())


ltl2filt = "ltlfilt -f '{formula}' --lbt"
ltl2rabin = '''ltl2dstar --ltl2nba="spin:ltl2tgba@-B -D -s" --stutter=no --output-format=native - -'''


class Rabin(Model):
    """
    Base class for deterministic Rabin automata.
    """

    yaml_tag = u'!Rabin'

    def __init__(self, props=None, multi=True):
        """
        LOMAP Rabin Automaton object constructor
        """
        Model.__init__(self, directed=True, multi=multi)

        if type(props) is dict:
            self.props = dict(props)
        else:
            self.props = list(props) if props is not None else []
            # Form the bitmap dictionary of each proposition
            # Note: range goes upto rhs-1
            self.props = dict(list(zip(self.props,
                                  [2 ** x for x in range(len(self.props))])))

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
                   init=list(self.init.keys()), final=self.final,
                   nodes=self.g.nodes(data=True),
                   edges=self.g.edges(data=True))

    def clone(self):
        ret = Rabin(self.props, self.directed, self.multi)
        ret.g = self.g.copy()
        ret.name = str(self.name)
        ret.init = dict(self.init)
        ret.final = deepcopy(self.final)
        return ret

    def from_formula(self, formula, prune=False, load=False):
        """
        Creates a Rabin automaton in-place from the given LTL formula.

        TODO: add support for loading and saving.
        """
        # execute ltl2dstar and get output
        try:
            l2f = sp.Popen(shlex.split(ltl2filt.format(formula=formula)), stdout=sp.PIPE)
            lines = sp.check_output(shlex.split(ltl2rabin), stdin=l2f.stdout).splitlines()
            l2f.wait()
        except Exception as ex:
            raise Exception(__name__, "Problem running ltl2dstar: '{}'".format(ex))

        lines = deque([x.strip() for x in lines])

        self.name = 'Deterministic Rabin Automaton'
        # skip version and comment
        line = lines.popleft()
        assert line == 'DRA v2 explicit'
        line = lines.popleft()
        if line.startswith('Comment:'):
            line = lines.popleft()
        # parse number of states
        assert line.startswith('States:')
        nstates = int(line.split()[1])
        # parse number of acceptance pairs
        line = lines.popleft()
        assert line.startswith('Acceptance-Pairs:')
        npairs = int(line.split()[1])
        self.final = tuple([(set(), set()) for _ in range(npairs)])
        # parse start state
        line = lines.popleft()
        assert line.startswith('Start:')
        self.init[int(line.split()[1])] = 1
        # parse atomic propositions
        line = lines.popleft()
        assert line.startswith('AP:')
        toks = line.split()
        nprops = int(toks[1])
        props = [p[1:-1] for p in toks[2:]]
        assert len(props) == nprops
        # Form the bitmap dictionary of each proposition
        # Note: range goes upto rhs-1
        self.props = dict(list(zip(self.props,
                                  [2 ** x for x in range(len(self.props))])))
        # Alphabet is the power set of propositions, where each element
        # is a symbol that corresponds to a tuple of propositions
        # Note: range goes upto rhs-1
        self.alphabet = set(range(0, 2 ** len(self.props)))

        line = lines.popleft()
        assert line == '---'

        # parse states
        for k in range(nstates):
            # parse state name
            line = lines.popleft()
            assert line.startswith('State:')
            tok = line.split()
            assert 2 <= len(tok) <=3
            name = int(tok[1])
            assert name == k
            # parse acceptance signature
            line = lines.popleft()
            assert line.startswith('Acc-Sig:')
            tok = line.split()
            assert len(tok) >= 1
            f, b = deque(), deque()
            for acc_sig in tok[1:]:
                pair = int(acc_sig[1:])
                assert 0 <= pair < npairs
                if acc_sig[0] == '+': # add to good states
                    f.append(pair)
                    self.final[pair][0].add(name)
                elif acc_sig[0] == '-': # add to bad states
                    b.append(pair)
                    self.final[pair][1].add(name)
                else: # parse error
                    raise ValueError('Unknown signature: %s!', acc_sig)
            # add state to Rabin automaton
            self.g.add_node(name, attr_dict={'good': f, 'bad': b})
            # parse transitions
            transitions = defaultdict(set)
            for bitmap in range(2**nprops):
                nb = int(lines.popleft())
                transitions[nb].add(bitmap)
            # add transitions to Rabin automaton
            self.g.add_edges_from([(name, nb, {'weight': 0, 'input': bitmaps,
                                     'label': self.guard_from_bitmaps(bitmaps)})
                                   for nb, bitmaps in transitions.items()])

        logging.info('DRA:\n%s', str(self))

        if prune:
            st, tr = self.prune()
            logging.info('DRA after prunning:\n%s', str(self))
            logging.info('Prunned: states: %s transitions: %s', str(st), str(tr))

    def prune(self):
        """TODO:
        """
        # set of allowed symbols, i.e. singletons and emptyset
        symbols = set([0] + list(self.props.values()))
        # update transitions and mark for deletion
        del_transitions = deque()
        for u, v, d in self.g.edges_iter(data=True):
            sym = d['input'] & symbols
            if sym:
                d['input'] = sym
            else:
                del_transitions.append((u, v))
        self.g.remove_edges_from(del_transitions)
        # delete states unreachable from the initial state
        init = next(iter(self.init.keys()))
        reachable_states = list(nx.shortest_path_length(self.g, source=init).keys())
        del_states = [n for n in self.g.nodes_iter() if n not in reachable_states]
        self.g.remove_nodes_from(del_states)
        # update accepting pairs
        for f, b in self.final:
            f.difference_update(del_states)
            b.difference_update(del_states)
        return del_states, del_transitions

    def guard_from_bitmaps(self, bitmaps):
        """TODO:
        """
        return '' #TODO:

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

        # Handler negated sets
        guard = re.sub('!self.symbols_w_prop', 'self.symbols_wo_prop', guard)

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
                    attr_dict = {'weight': 0, 'input': self.alphabet,
                                 'guard': '(1)', 'label': '(1)'}
                    self.g.add_edge('trap', 'trap', **attr_dict)
                    trap_added = True
                attr_dict = {'weight': 0, 'input': rem_alphabet,
                             'guard': 'trap_guard', 'label': 'trap_guard'}
                self.g.add_edge(s, 'trap', **attr_dict)

        if not trap_added:
            logger.info('No trap states were added.')
        else:
            logger.info('Trap states were added.')
        return trap_added

    @DeprecationWarning
    def remove_trap_states(self):
        '''
        Removes all states of the automaton which do not reach a final state.
        Returns True whenever trap states have been removed from the automaton.
        '''
        # add virtual state which has incoming edges from all final states
        self.g.add_edges_from([(state, 'virtual') for state in self.final])
        # compute trap states
        trap_states = set(self.g.nodes_iter())
        trap_states -= set(nx.shortest_path_length(self.g, target='virtual'))
        # remove trap state and virtual state
        self.g.remove_nodes_from(trap_states | set(['virtual']))
        return len(trap_states - set(['virtual'])) == 0

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

    def next_state(self, q, props):
        """
        Returns the next state of state q given input proposition set props.
        """
        # Get the bitmap representation of props
        prop_bitmap = self.bitmap_of_props(props)
        # Return an array of next states
        nq = [v for _, v, d in self.g.out_edges_iter(q, data=True)
                                                   if prop_bitmap in d['input']]
        assert len(nq) <= 1
        if nq:
            return nq[0]
        return None # This is reached only for blocking automata
