# Copyright (C) 2018, Cristian-Ioan Vasile (cvasile@bu.edu)
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

import random
import os, tempfile

import networkx as nx

from lomap.classes import Automaton, Fsa, Buchi, Rabin, Model, Ts, Markov


def test_models_yaml():
    '''Creates a random models, saves them in yaml format, loads them from file,
    and compares the generated and loaded system models.
    '''
    for M, init_factory in ((Model, set), (Ts, set),
                            (Markov, lambda l: dict([(x, 1) for x in l]))):
        # generate random model
        model = M('Random system model', directed=True, multi=False)
        model.g = nx.gnp_random_graph(n=100, p=0.5, seed=1, directed=True)
        model.init = init_factory(random.sample(model.g.nodes(), 5))
        model.final = set(random.sample(model.g.nodes(), 5))

        # save system model to temporary yaml file
        f = tempfile.NamedTemporaryFile(mode='w+t', suffix='.yaml',
                                        delete=False)
        f.close()
        print('Saving', M.__name__, 'system model to', f.name)
        model.save(f.name)

        # load system model from temporary yaml file
        print('Loading', M.__name__, 'system model from', f.name)
        model2 = M.load(f.name)
    
        # test that the two system models are equal
        assert(model == model2), '{} are not equal!'.format(M.__name__)

        # remove temporary file
        os.remove(f.name)

def test_automata_yaml():
    '''Creates a automata from a formula, saves them in yaml format, loads them
    from file, and compares the computed and loaded automata.
    '''
    formula = 'F a && F b && (!b) U a'
    for A in (Automaton, Fsa, Buchi, Rabin):
        aut = A(multi=False)
        try:
            aut.from_formula(formula)
        except NotImplementedError:
            pass

        # save automaton to temporary yaml file
        f = tempfile.NamedTemporaryFile(mode='w+t', suffix='.yaml',
                                        delete=False)
        f.close()
        print('Saving', A.__name__ ,'automaton to', f.name)
        aut.save(f.name)

        # load automaton from temporary yaml file
        print('Loading', A.__name__, 'automaton from', f.name)
        aut2 = A.load(f.name)
    
        # test that the two automata are equal
        assert(aut == aut2), '{} are not equal!'.format(A.__name__)

        # remove temporary file
        os.remove(f.name)


if __name__ == '__main__':
    test_models_yaml()
    test_automata_yaml()
