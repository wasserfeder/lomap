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

from .buchi import Buchi
from .fsa import Fsa
from .rabin import Rabin
from .model import Model
from .ts import Ts
from .markov import Markov
from .timer import Timer


def model_representer(dumper, model):
    '''YAML representer for a model object.
    Note: it uses the object's yaml_tag attribute as its YAML tag.
    '''
    return dumper.represent_mapping(tag=model.yaml_tag, mapping={
        'name'     : model.name,
        'directed' : model.directed,
        'multi'    : model.multi,
        'init'     : list(model.init),
        'final'    : list(model.final),
        'graph'    : {
            'nodes' : dict(model.g.nodes(data=True)),
            'edges' : model.g.edges(data=True)
            }
        })

def model_constructor(loader, node, ModelClass):
    '''Model constructor from YAML document.
    Note: Creates an object of class ModelClass.
    '''
    data = loader.construct_mapping(node, deep=True)
    name = data.get('name', 'Unnamed')
    directed = data.get('directed', True)
    multi = data.get('multi', True)

    model = ModelClass(directed=directed, multi=multi)
    model.name = name
    model.init = set(data.get('init', []))
    model.final = set(data.get('final', []))
    model.g.add_nodes_from(data['graph'].get('nodes', dict()).iteritems())
    model.g.add_edges_from(data['graph'].get('edges', []))
    return model

# TODO: add representer and constructor for automata

# register yaml representers
try: # try using the libyaml if installed
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError: # else use default PyYAML loader and dumper
    from yaml import Loader, Dumper

Dumper.add_representer(Model, model_representer)
Dumper.add_representer(Ts, model_representer)

Loader.add_constructor(Model.yaml_tag,
    lambda loader, model: model_constructor(loader, model, Model))
Loader.add_constructor(Ts.yaml_tag,
    lambda loader, model: model_constructor(loader, model, Ts))
