import networkx as nx
from lomap import Fsa, Ts, ts_times_fsa, ts_times_ts_unsorted

def construct_fsa():
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
    fsa.init.add('s0')
    # add `s3` to set of final/accepting states
    fsa.final.add('s3')
    return fsa

def construct_ts():
    ts = Ts(directed=True, multi=False)
    ts.g = nx.grid_2d_graph(4, 3)
    
    ts.init.add((1, 1))
    
    ts.g.add_node((0, 0), attr_dict={'prop': set(['a'])})
    ts.g.add_node((3, 2), attr_dict={'prop': set(['b'])})
    
    ts.g.add_edges_from(ts.g.edges(), weight=1)

    #for two tss uncomment these two lines and return pts 
    pts =ts_times_ts_unsorted((ts, ts))
    pts.g.add_edges_from(pts.g.edges(), weight=1)

    return pts

if __name__ == '__main__':
    fsa = construct_fsa()
    print(fsa)
    ts = construct_ts()
    print(ts)
    # compute product model that captures motion and mission satisfaction at the
    # same time
    product_model = ts_times_fsa(ts, fsa)
    print(product_model)
    print(product_model.init) # initial states
    print(product_model.final) # final states
    # get initial state in product model -- should be only one
    pa_initial_state = next(iter(product_model.init))
    # compute shortest path lengths from initial state to all other states
    lengths = nx.shortest_path_length(product_model.g, source=pa_initial_state)
    # keep path lenghts only for final states in the product model
    lengths = {final_state: lengths[final_state]
               for final_state in product_model.final}
    # find the final state with minimum length
    pa_optimal_final_state = min(lengths, key=lengths.get)
    print(pa_optimal_final_state)
    # get optimal solution path in product model from initial state to optimal
    # final state
    pa_optimal_path = nx.shortest_path(product_model.g, source=pa_initial_state,
                                       target=pa_optimal_final_state)
    print(pa_optimal_path)
    # get optimal solution path in the transition system (robot motion model)
    ts_optimal_path, fsa_state_trajectory = zip(*pa_optimal_path)
    print(ts_optimal_path)
    print(fsa_state_trajectory)
    print('\n')
    print('\n')
    print('\n')

    for node in product_model.g.nodes():
        print(node)
    print('\n')
    print('\n')
    print('\n')
    
    for edge in product_model.g.edges():
        print(edge)
