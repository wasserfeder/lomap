#! /usr/local/bin/python3

# Implementing a test case similar to test_fsa.py
import networkx as nx

import lomap
from lomap.classes.fsa import Fsa
from lomap.classes.ts import Ts
from lomap.algorithms.wfse_product import product_function
from lomap.classes.wfse import Wfse 

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
    ts.g.add_node((3, 2), attr_dict={'prop': set(['b'])})
    
    ts.g.add_edges_from(ts.g.edges(), weight=1)

    return ts

# IN PROGRESS // FIX
def wfse_constructor():

    ap_wfse = set(['a', 'b']) # atomic props
    wfse = Wfse(props=ap_wfse, multi=False) # empty FSA with propsitions from `ap_wfse`
   
    # states
    # add transitions // these are the 'potential' neighboring states (!?!)
    # So in this function the transitions listes can correspond to wfse states that will then trigger the next_fsa_state
    inputs = set(fsa.bitmap_of_props(value) for value in [set()])

    wfse.g.add_edge('q0', 'q0', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['a'])])
    
    wfse.g.add_edge('q0', 'q1', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['b'])])
    
    wfse.g.add_edge('q0', 'q2', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['a', 'b'])])
    
    wfse.g.add_edge('q0', 'q3', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['a'])])
    
    wfse.g.add_edge('q1', 'q1', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['b']), set(['a', 'b'])])
    
    wfse.g.add_edge('q1', 'q3', attr_dict={'input': inputs})
    inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['b'])])
    
    wfse.g.add_edge('q2', 'q2', attr_dict={'input': inputs}) 
    inputs = set(fsa.bitmap_of_props(value) for value in [set(['a']), set(['a', 'b'])])
    
    wfse.g.add_edge('q2', 'q3', attr_dict={'input': inputs})
    wfse.g.add_edge('q3', 'q3', attr_dict={'input': fsa.alphabet})
    
    # set the initial state
    wfse.init['q0'] = 1
    
    # add `s3` to set of final/accepting states
    wfse.final.add('q3')

    return wfse


if __name__ == '__main__':
    fsa = fsa_constructor()
    print(fsa)
    ts = ts_constructor()
    print(ts)
    wfse = wfse_constructor()
    print(wfse)
       
    model_product = product_function(ts, wfse, fsa)
    print(model_product)
    
    print(model_product.init) # initial states
    print(pmodel_product.final) # final states
    
    # how do I extract the corrected path?
    # I need to print the corrected/alternate/substiture path


    #alternate_path = 
    #print(alternate_path)
   
    