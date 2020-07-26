#! /usr/bin/python

# Implementing a test case similar to test_fsa.py

import networkx as nx

from lomap import Fsa, Ts, Wfse, ts_times_wfse_times_fsa


def fsa_constructor():
    ap = set(['a', 'b']) # set of atomic propositions
    fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`
    # add states
    fsa.g.add_nodes_from(['s0', 's1', 's2', 's3'])

    #add transitions
    inputs = set(fsa.bitmap_of_props(value) for value in [set()])
    fsa.g.add_edge('s0', 's0', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['a'])])
    fsa.g.add_edge('s0', 's1', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['b'])])
    fsa.g.add_edge('s0', 's2', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['a', 'b'])])
    fsa.g.add_edge('s0', 's3', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['a'])])
    fsa.g.add_edge('s1', 's1', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['b']), set(['a', 'b'])])
    fsa.g.add_edge('s1', 's3', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['b'])])
    fsa.g.add_edge('s2', 's2', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['a']), set(['a', 'b'])])
    fsa.g.add_edge('s2', 's3', attr_dict={'input': inputs})
    fsa.g.add_edge('s3', 's3', attr_dict={'input': fsa.alphabet})
    # set the initial state
    fsa.init['s0'] = 1
    # add `s3` to set of final/accepting states
    fsa.final.add('s3')

    return fsa


def ts_constructor():
    ts = Ts(directed=True, multi=False)
    ts.g = nx.grid_2d_graph(4, 3)

    ts.init[(1, 1)] = 1

    ts.g.add_node((0, 0), attr_dict={'prop': set(['a'])})
    # ts.g.add_node((3, 2), attr_dict={'prop': set(['b'])})
    ts.g.add_node((3, 2), attr_dict={'prop': set(['c'])})

    ts.g.add_edges_from(ts.g.edges(), weight=1)

    return ts


def wfse_constructor():
    ap = set(['a', 'b', 'c']) # set of atomic propositions
    wfse = Wfse(props=ap, multi=False)
    wfse.init = set() # HACK

    # add states
    wfse.g.add_nodes_from(['q0'])

    # add transitions
    in_symbol = set(fsa.bitmap_of_props(value) for value in [set('c')])
    out_symbol = set(fsa.bitmap_of_props(value) for value in [set('b')])

    weighted_symbol = (in_symbol, out_symbol, 2)
    fsa.g.add_edge('q0', 'q0', attr_dict={'symbols': weighted_symbol})

    weighted_symbol = out_symbol, out_symbol, 1)
    fsa.g.add_edge('q0', 'q0', attr_dict={'symbols': weighted_symbol})

    # set the initial state
    wfse.init.add('q0')

    return wfse


if __name__ == '__main__':
    fsa = fsa_constructor()
    print(fsa)
    ts = ts_constructor()
    print(ts)
    wfse = wfse_constructor()
    print(wfse)

    product_model = ts_times_wfse_times_fsa(ts, wfse, fsa)
    print(product_model)

    print(product_model.init) # initial states
    print(product_model.final) # final states

    # MODIFY HERE // IN PROGRESS

    # Important questions for the next move:
    # I need to figure out what the wfse constructor outputs
    # I need to figure out how to extract the corrected path
    # To do that I will use the functions from product_wfse
    # I will print the corrected/alternate/substiture path



    alternate_path = None
    print(alternate_path)
