#! /usr/bin/python

from __future__ import print_function
import logging
import networkx as nx
from lomap import Fsa, Ts, Wfse, ts_times_wfse_times_fsa
from lomap import Timer

#FSA
def fsa_constructor(book):
    ap = set(['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9','w10', 'w11', 'w12', 'w13', 'w14', 'w15', 'co']) #'w16', 'w17', 'w18', 'w19', 'w20', 'w21','w22', 'w23', 'w24']) # set of atomic propositions // MODIFY
    fsa = Fsa(props=ap, multi=False) 
    
    # add states
    #FD: front desk
    #Bn: book and the number
    #CO: check-out
    fsa.g.add_nodes_from(['FD', 'B1', 'B2', 'B3', 'B4', 'B5','B6', 'B7','B8','B9','B10', 'B11','B12','B13','B14','B15' 'CO']) #,'B16','B17','B18','B19','B20','B21','B22','B23','B24''CO'])
    #add transitions

    book = int(book)
    for book in range(1,16):
        inputs = set(fsa.bitmap_of_props(value) for value in [set()]) #empty set
        fsa.g.add_edge('FD', 'FD', attr_dict={'input': inputs})
        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w{}'.format(book)])])
        fsa.g.add_edge('FD', 'B{}'.format(book), attr_dict={'input': inputs})
        inputs = set(fsa.bitmap_of_props(value) for value in [set(['w{}'.format(book)]), set(['w1','w2','w3','w4','w5','w6', 'w7','w8','w9','w10'])])
        fsa.g.add_edge('B{}'.format(book), 'B{}'.format(book), attr_dict={'input': inputs})
        inputs = set(fsa.bitmap_of_props(value)
                 for value in [ set(['co'])]) # CHECKOUT PROP
        fsa.g.add_edge('B{}'.format(book), 'CO', attr_dict={'input': inputs})
        fsa.g.add_edge('CO', 'CO', attr_dict={'input': fsa.alphabet})
    
    # set initial and final states
    fsa.init['FD'] = 1 #initial state: front desk
    # final
    fsa.final.add('CO') #final state: check-out
    return fsa

#TS
def ts_constructor():
    # using a loop to make it easier for the programmer to modify the size of the ts (add nodes)
    ts = Ts(directed=True, multi=False)
    ts.g = nx.DiGraph()
    ts.init[(0)] = 1
    #modify the limits of the range for different sizes
    #adding nodes
    ts.g.add_node((0), attr_dict={'prop': set()}) #initial state: front desk
    ts.g.add_node((16), attr_dict={'prop': set(['co'])}) #modify according to which number the final state is for the different sizes
    for i in range(1,16):
        ts.g.add_node((i), attr_dict={'prop': set(['w{}'.format(i)])})
    ts.g.add_edges_from((u, u) for u in ts.g) # vary the weigths
    #adding edges (transitions)
    for i in range(1,16):
        #transition to an initial state
        ts.g.add_edge(0,i,weight=1)
        #self-loop
        ts.g.add_edge(i,i,weight=1)
        #final transition
        ts.g.add_edge(i,16,weight=1)
    ts.g.add_edge(0,0,weight=1) #initial state self-loop
    ts.g.add_edge(16,16,weight=1) #final state self-loop
    return ts
    
    
#WFSE
def wfse_constructor(book):
    ap = set(['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9','w10', 'w11', 'w12', 'w13', 'w14', 'w15', 'co']) #'w16', 'w17', 'w18', 'w19', 'w20', 
    wfse = Wfse(props=ap, multi=False)
    wfse.init = set() # HACK
    
    # add states
    wfse.g.add_nodes_from(['fd', 'q1', 'q2', 'q3', 'q4','q5','q6', 'q7', 'q8', 'q9', 'q10', 'q11', 'q12','q13','q14','q15', 'co']) #'q16','q17','q18', 'q19', 'q20'
    # add transitions
    pass_through_symbols = [(symbol, symbol, 1) for symbol in wfse.prop_bitmaps
                            if symbol >= 0]
    #print('pass through symbols:', pass_through_symbols) # THIS TAKES A WHILE TO PRINT
    wfse.g.add_edge('fd', 'fd', attr_dict={'symbols': pass_through_symbols})
    wfse.g.add_edge('co', 'co', attr_dict={'symbols': pass_through_symbols})
    
    book = int(book)
    if (book >= 1) and (book<= 13):
            book_str = 'w{}'.format(book+1) #substitute with the next book
            in_symbol = wfse.bitmap_of_props(set([book_str]))
            book_str = 'w{}'.format(book)
            out_symbol = wfse.bitmap_of_props(set([book_str]))
            weighted_symbols = [(in_symbol, out_symbol, 5)]
            state = 'q{}'.format(book)
            wfse.g.add_edge('fd', str(state), attr_dict={'symbols': weighted_symbols})
            weighted_symbols = [( -1, out_symbol, 2)]
            wfse.g.add_edge(str(state), 'co', attr_dict={'symbols': weighted_symbols})
    
    elif (book == 14):
            book_str = 'w1' #substitute with book 1
            in_symbol = wfse.bitmap_of_props(set([book_str]))
            book_str = 'w{}'.format(book)
            out_symbol = wfse.bitmap_of_props(set([book_str]))
            weighted_symbols = [(in_symbol, out_symbol, 5)]
            state = 'q{}'.format(book)
            wfse.g.add_edge('fd', str(state), attr_dict={'symbols': weighted_symbols})
            weighted_symbols = [( -1, out_symbol, 2)]
            wfse.g.add_edge(str(state), 'co', attr_dict={'symbols': weighted_symbols})
    
    elif (book == 15):
            book_str = 'w{}'.format(book)
            in_symbol = -1
            book_str = 'w{}'.format(book) #delete
            out_symbol = wfse.bitmap_of_props(set([book_str]))
            weighted_symbols = [(in_symbol, out_symbol, 7)]
            state = 'co'
            wfse.g.add_edge('fd', state, attr_dict={'symbols': weighted_symbols})
            weighted_symbols = [( -1, -1, 0)] #try
            wfse.g.add_edge('co', state, attr_dict={'symbols': weighted_symbols}) #try
            wfse.final.add('co')
    
    # set the initial state
    wfse.init.add('fd')
    # set the final state
    wfse.final.add('co')
    
    return wfse

def main():
    logging.basicConfig(level=logging.DEBUG)
    print("Please enter the book number")
    book = str(input())
    fsa = fsa_constructor(book)
    #print(fsa)
    ts = ts_constructor()
    #print(ts)
    wfse = wfse_constructor(book)
    #print(wfse)
    with Timer('Product construction'):
       product_model = ts_times_wfse_times_fsa(ts, wfse, fsa)
    #print(product_model.g.edges())
    print('Product: Init:', product_model.init) # initial states
    print('Product: Final:', product_model.final) # final states
    print('Product: Size', product_model.size()) # number of states and transitions1
    with Timer('Control Synthesis'):
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
        transition_data = product_model.g[state][next_state]
        original_symbol, transformed_symbol = transition_data['prop']
        print(ts_state, ':', original_symbol, '->', transformed_symbol)
if __name__ == '__main__':
    main()