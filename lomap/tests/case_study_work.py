#! /usr/bin/python

#! /usr/bin/python

# Test case for using Weighted Finite State Error Systems.
# Copyright (C) 2020, Cristian-Ioan Vasile (cvasile@lehigh.edu)
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

from __future__ import print_function

import networkx as nx

from lomap import Fsa, Ts, Wfse, ts_times_wfse_times_fsa

#FSA
def fsa_constructor(book):
    ap = set(['w1', 'w2', 'w3', 'w4','w5','w6']) # set of atomic propositions // MODIFY
    fsa = Fsa(props=ap, multi=False) # empty FSA with propsitions from `ap`
    # add states
    #FD: front desk
    #Bn: book and the number
    #CO: check-out
    fsa.g.add_nodes_from(['FD', 'B1', 'B2', 'B3', 'B4', 'B5','B6', 'CO']) #'B7','B8','B9','B10','B11','B12','B13','B14','B15','B16','B17','B18','B19','CO'])
    
    #add transitions
    #all the possible transitions

    if book == '1':

        inputs = set(fsa.bitmap_of_props(value) for value in [set()]) #empty set
        fsa.g.add_edge('FD', 'FD', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w1'])]) 
        fsa.g.add_edge('FD', 'B1', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['w1'])])
        fsa.g.add_edge('B1', 'B1', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['w2']), set(['w1', 'w2', 'w3'])])
        fsa.g.add_edge('B1', 'CO', attr_dict={'input': inputs})

        fsa.g.add_edge('CO', 'CO', attr_dict={'input': fsa.alphabet})

    if book == '2':
    
        inputs = set(fsa.bitmap_of_props(value) for value in [set()]) #empty set
        fsa.g.add_edge('FD', 'FD', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w2'])])
        fsa.g.add_edge('FD', 'B2', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['w2'])])
        fsa.g.add_edge('B2', 'B2', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['w3']), set(['w1', 'w2','w3'])])
        fsa.g.add_edge('B2', 'CO', attr_dict={'input': inputs})

        fsa.g.add_edge('CO', 'CO', attr_dict={'input': fsa.alphabet})

        
    
    if book == '3':
        inputs = set(fsa.bitmap_of_props(value) for value in [set()]) #empty set
        fsa.g.add_edge('FD', 'FD', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w3'])])
        fsa.g.add_edge('FD', 'B3', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['w3'])])
        fsa.g.add_edge('B3', 'B3', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['w1']), set(['w1', 'w2', 'w3'])])
        fsa.g.add_edge('B3', 'CO', attr_dict={'input': inputs})

        fsa.g.add_edge('CO', 'CO', attr_dict={'input': fsa.alphabet})
    
    if book == '4':
        inputs = set(fsa.bitmap_of_props(value) for value in [set()]) #empty set
        fsa.g.add_edge('FD', 'FD', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w4'])])
        fsa.g.add_edge('FD', 'B4', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['w4'])])
        fsa.g.add_edge('B4', 'B4', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(['b']), set(['a', 'b'])])
        fsa.g.add_edge('B4', 'CO', attr_dict={'input': inputs})

        fsa.g.add_edge('CO', 'CO', attr_dict={'input': fsa.alphabet})


    if book =='5':
        inputs = set(fsa.bitmap_of_props(value) for value in [set()]) #empty set
        fsa.g.add_edge('FD', 'FD', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w5'])])
        fsa.g.add_edge('FD', 'B5', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['w5'])])
        fsa.g.add_edge('B5', 'B5', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) #idk if that s right // come back to it
                 for value in [set(), set(['B5'])])
        fsa.g.add_edge('B5', 'CO', attr_dict={'input': inputs})

        fsa.g.add_edge('CO', 'CO', attr_dict={'input': fsa.alphabet})


    if book=='6':
        inputs = set(fsa.bitmap_of_props(value) for value in [set()]) #empty set
        fsa.g.add_edge('FD', 'FD', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w6'])])
        fsa.g.add_edge('FD', 'B6', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value) for value in [set(), set(['w6'])])
        fsa.g.add_edge('B6', 'B6', attr_dict={'input': inputs})

        inputs = set(fsa.bitmap_of_props(value)
                 for value in [set(), set(['B6'])])
        fsa.g.add_edge('B6', 'CO', attr_dict={'input': inputs})

        fsa.g.add_edge('CO', 'CO', attr_dict={'input': fsa.alphabet})

    # set the initial state
    fsa.init['FD'] = 1 #initial state: front desk
    # final
    fsa.final.add('CO') #final state: check-out

    return fsa


#TS
def ts_constructor(): 
    ts = Ts(directed=True, multi=False)
    ts.g = nx.DiGraph()
    ts.g.add_edges_from((u, u) for u in ts.g) 

    ts.init[(0)] = 1 
    ts.g.add_node((0), attr_dict={'prop': set()})
    ts.g.add_node((1), attr_dict={'prop': set(['w1'])})
    ts.g.add_node((2), attr_dict={'prop': set(['w2'])})
    ts.g.add_node((3), attr_dict={'prop': set(['w3'])})
    ts.g.add_node((4), attr_dict={'prop': set(['w4'])})
    ts.g.add_node((5), attr_dict={'prop': set(['w5'])})
    ts.g.add_node((6), attr_dict={'prop': set(['w6'])})
    
    return ts

    #WFSE
def wfse_constructor(book):

    ap = set(['w1', 'w2','w3','w4','w5','w6']) # set of atomic propositions
    wfse = Wfse(props=ap, multi=False)
    wfse.init = set() # HACK
        
    # add states
    wfse.g.add_nodes_from(['fd', 'q1', 'q2', 'q3', 'q4','q5','q6','co'])

    # add transitions
    pass_through_symbols = [(symbol, symbol, 1) for symbol in wfse.prop_bitmaps
                            if symbol >= 0]
    print('pass through symbols:', pass_through_symbols)
    wfse.g.add_edge('fd', 'fd', attr_dict={'symbols': pass_through_symbols})

    if book == '1':
        # Substitute w1 by w2 with a penalty (book 1 is not found but book 2 is)
        in_symbol = wfse.bitmap_of_props(set(['w1']))
        out_symbol = wfse.bitmap_of_props(set(['w2']))

        weighted_symbols = [(in_symbol, out_symbol, 5)]
        wfse.g.add_edge('fd', 'q1', attr_dict={'symbols': weighted_symbols})

        weighted_symbols = [( -1, out_symbol, 0)] 
        wfse.g.add_edge('q1', 'co', attr_dict={'symbols': weighted_symbols})

    if book == '2':
        # Substitute w2 by w3 with a penalty (book 2 is not found but book 3 is)
        in_symbol = wfse.bitmap_of_props(set(['w2']))
        out_symbol = wfse.bitmap_of_props(set(['w3']))

        weighted_symbols = [(in_symbol, out_symbol, 5)]
        wfse.g.add_edge('fd', 'q2', attr_dict={'symbols': weighted_symbols})

        weighted_symbols = [( -1, out_symbol, 0)] 
        wfse.g.add_edge('q2', 'co', attr_dict={'symbols': weighted_symbols})

    if book =='3':
        # Substitute w3 by w1 with a penalty (book 3 is not found but book 1 is)
        in_symbol = wfse.bitmap_of_props(set(['w3']))
        out_symbol = wfse.bitmap_of_props(set(['w1']))

        weighted_symbols = [(in_symbol, out_symbol, 5)]
        wfse.g.add_edge('fd', 'q3', attr_dict={'symbols': weighted_symbols})

        weighted_symbols = [( -1, out_symbol, 0)] 
        wfse.g.add_edge('q3', 'co', attr_dict={'symbols': weighted_symbols})
        
    if book=='4':
        in_symbol = -1
        out_symbol= wfse.bitmap_of_props(set(['w4'])) 
        weighted_symbols = [(in_symbol, out_symbol, 10)]
        wfse.g.add_edge('fd', 'q4', attr_dict={'symbols': weighted_symbols})
        weighted_symbols = [(-1, -1, 0)] #modify the weights 
        wfse.g.add_edge('q4', 'co', attr_dict={'symbols': weighted_symbols})

    if book=='5':
        in_symbol = -1
        out_symbol= wfse.bitmap_of_props(set(['w5'])) 
        weighted_symbols = [(in_symbol, out_symbol, 10)]
        wfse.g.add_edge('fd', 'q5', attr_dict={'symbols': weighted_symbols})
        weighted_symbols = [(-1, -1, 0)] #modify the weights 
        wfse.g.add_edge('q5', 'co', attr_dict={'symbols': weighted_symbols})

    if book=='6':
        in_symbol = -1
        out_symbol= wfse.bitmap_of_props(set(['w6'])) 
        weighted_symbols = [(in_symbol, out_symbol, 10)]
        wfse.g.add_edge('fd', 'q6', attr_dict={'symbols': weighted_symbols})
        weighted_symbols = [(-1, -1, 0)] #modify the weights 
        wfse.g.add_edge('q6', 'co', attr_dict={'symbols': weighted_symbols})

    # set the initial state
    wfse.init.add('fd')

    # set the final state
    wfse.final.add('co')

    return wfse

def main():
    
    print("Please enter the book number")
    book = input()

    fsa = fsa_constructor(book)
    print(fsa)
    ts = ts_constructor()
    print(ts)
    wfse = wfse_constructor(book)
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
        
        data = product_model.g[state][next_state]
        if data['weight'] < 2:
            print(ts_state, '->', data)
        else:
            data['weight'] = 3
            data['prop'] = ({"w1"}, {"w2"})
            print(ts_state, '->', data)


if __name__ == '__main__':
    main()
