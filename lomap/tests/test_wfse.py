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
    in_symbol = wfse.bitmap_of_props(set(['c']))
    out_symbol = wfse.bitmap_of_props(set(['b']))

    weighted_symbols = [(in_symbol, out_symbol, 2)]
    for symbol in wfse.prop_bitmaps:
        if symbol >= 0:
            weighted_symbols.append((symbol, symbol, 1))
    print('weighted_symbols:', weighted_symbols)
    wfse.g.add_edge('q0', 'q0', attr_dict={'symbols': weighted_symbols})

    # set the initial state
    wfse.init.add('q0')

    # set the final state
    wfse.final.add('q0')

    return wfse


def main():
    fsa = fsa_constructor()
    print(fsa)
    ts = ts_constructor()
    print(ts)
    wfse = wfse_constructor()
    print(wfse)

    product_model = ts_times_wfse_times_fsa(ts, wfse, fsa)
    print(product_model)

    print('Product: Init:', product_model.init) # initial states
    print('Product: Final:', product_model.final) # final states

    # get initial state in product model -- should be only one
    pa_initial_state = next(iter(product_model.init))
    # compute shortest path lengths from initial state to all other states
    lengths = nx.shortest_path_length(product_model.g, source=pa_initial_state)
    # keep path lenghts only for final states in the product model
    lengths = {final_state: lengths[final_state]
               for final_state in product_model.final}
    # find the final state with minimum length
    pa_optimal_final_state = min(lengths, key=lengths.get)
    print('Product: Optimal Final State:', pa_optimal_final_state)
    # get optimal solution path in product model from initial state to optimal
    # final state
    pa_optimal_path = nx.shortest_path(product_model.g, source=pa_initial_state,
                                       target=pa_optimal_final_state)
    print('Product: Optimal trajectory:', pa_optimal_path)
    # get optimal solution path in the transition system (robot motion model)
    ts_optimal_path, wfse_state_path, fsa_state_path = zip(*pa_optimal_path)
    print('TS: Optimal Trajectory:', ts_optimal_path)
    print('WFSE: Optimal Trajectory:', wfse_state_path)
    print('FSA: Optimal Trajectory:', fsa_state_path)

    print('Symbol translations:')
    for ts_state, state, next_state in zip(ts_optimal_path[1:], pa_optimal_path,
                                           pa_optimal_path[1:]):
        print(ts_state, '->', product_model.g[state][next_state]['prop'])

    # MODIFY HERE // IN PROGRESS

    # Important questions for the next move:
    # I need to figure out what the wfse constructor outputs
    # I need to figure out how to extract the corrected path
    # To do that I will use the functions from product_wfse
    # I will print the corrected/alternate/substiture path


if __name__ == '__main__':
    main()
