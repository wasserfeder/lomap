#! /usr/bin/python

from __future__ import absolute_import
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


from lomap.classes.automata import Automaton, Buchi, Fsa, Rabin
from lomap.classes.model import Model
from lomap.classes.ts import Ts
from lomap.classes.markov import Markov
from lomap.classes.timer import Timer
from lomap.classes.interval import Interval

def model_representer(dumper, model,
                      init_representer=list, final_representer=list):
    '''YAML representer for a model object.
    Note: it uses the object's yaml_tag attribute as its YAML tag.
    '''
    return dumper.represent_mapping(tag=model.yaml_tag, mapping={
        'name'     : model.name,
        'directed' : model.directed,
        'multi'    : model.multi,
        'init'     : init_representer(model.init),
        'final'    : final_representer(model.final),
        'graph'    : {
            'nodes' : dict(model.g.nodes(data=True)),
            'edges' : list(map(list, model.g.edges(data=True)))
            }
        })

def model_constructor(loader, node, ModelClass,
                      init_factory=set, final_factory=set):
    '''Model constructor from YAML document.
    Note: Creates an object of class ModelClass.
    '''
    data = loader.construct_mapping(node, deep=True)
    name = data.get('name', 'Unnamed')
    directed = data.get('directed', True)
    multi = data.get('multi', True)

    model = ModelClass(name=name, directed=directed, multi=multi)
    model.init = init_factory(data.get('init', init_factory()))
    model.final = final_factory(data.get('final', final_factory()))
    model.g.add_nodes_from(data['graph'].get('nodes', dict()).items())
    model.g.add_edges_from(data['graph'].get('edges', []))
    return model

def automaton_representer(dumper, automaton):
    '''YAML representer for an automaton object.
    Note: it uses the object's yaml_tag attribute as its YAML tag.
    '''
    return dumper.represent_mapping(tag=automaton.yaml_tag, mapping={
        'name'     : automaton.name,
        'props'    : automaton.props,
        'multi'    : automaton.multi,
        'init'     : automaton.init, #FIXME: Why is init a dict?
        'final'    : automaton.final, #FIXME: list causes errors with Rabin
        'graph'    : {
            'nodes' : dict(automaton.g.nodes(data=True)),
            'edges' : list(map(list, automaton.g.edges(data=True)))
            }
        })

def automaton_constructor(loader, node, ModelClass, # FIXME: Why is init a dict?
                      init_factory=dict, final_factory=set):
    '''Model constructor from YAML document.
    Note: Creates an object of class ModelClass.
    '''
    data = loader.construct_mapping(node, deep=True)
    name = data.get('name', 'Unnamed')
    props = data.get('props', None)
    multi = data.get('multi', True)

    automaton = ModelClass(name=name, props=props, multi=multi)
    automaton.init = init_factory(data.get('init', init_factory()))
    automaton.final = final_factory(data.get('final', final_factory()))
    automaton.g.add_nodes_from(data['graph'].get('nodes', dict()).items())
    automaton.g.add_edges_from(data['graph'].get('edges', []))
    return automaton

# register yaml representers
try: # try using the libyaml if installed
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError: # else use default PyYAML loader and dumper
    from yaml import Loader, Dumper

Dumper.add_representer(Model, model_representer)
Dumper.add_representer(Ts, model_representer)
Dumper.add_representer(Markov,
    lambda dumper, model: model_representer(dumper, model, dict))
Dumper.add_representer(Automaton, automaton_representer)
Dumper.add_representer(Buchi, automaton_representer)
Dumper.add_representer(Fsa, automaton_representer)
Dumper.add_representer(Rabin, automaton_representer)

Loader.add_constructor(Model.yaml_tag,
    lambda loader, model: model_constructor(loader, model, Model))
Loader.add_constructor(Ts.yaml_tag,
    lambda loader, model: model_constructor(loader, model, Ts))
Loader.add_constructor(Markov.yaml_tag,
    lambda loader, model: model_constructor(loader, model, Markov, dict))
Loader.add_constructor(Automaton.yaml_tag,
  lambda loader, automaton: automaton_constructor(loader, automaton, Automaton))
Loader.add_constructor(Buchi.yaml_tag,
    lambda loader, automaton: automaton_constructor(loader, automaton, Buchi))
Loader.add_constructor(Fsa.yaml_tag,
    lambda loader, automaton: automaton_constructor(loader, automaton, Fsa))
Loader.add_constructor(Rabin.yaml_tag,
    lambda loader, automaton: automaton_constructor(loader, automaton, Rabin,
                                                    final_factory=tuple))
