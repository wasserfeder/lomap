import numpy as np
import networkx as nx
from random import uniform
import random
from lomap import Fsa


class incremental_tree(object):

    def __init__(self, ts, fsa, init_state):
        self.ts = ts
        self.fsa = fsa
        self.init = init_state
        current_ts = self.init[0]
        self.init_fsa = init_state[1]
        self.final_states = [final for final in fsa.final]
        self.product_tree = nx.DiGraph(type='PA', mmulti=False)
        print("final:", self.final_states)
        print("fsa_eddges", self.fsa.g.edges(data=True))

        current_state = self.init_fsa

        neighbors = self.get_one_reachable_set(current_state)
        next_neighbors = self.get_two_reachable_set()
        print("nnnext:", next_neighbors)

        self.modify_partitions( next_neighbors)
        next_state = self.sample_fsa_state()
        symbol = fsa.g.get_edge_data(current_state[0], next_state[0])
        print("sym:", list(symbol.get('input')))
        symbol = list(symbol.get('input'))
        shortest_path = project_on_ts(ts, current_ts, self.fsa, symbol[0])

    def get_one_reachable_set(self, fsa_current_state):
        neighbors = []
        print(fsa_current_state)
        # fsa_current_state = tuple(fsa_current_state)
        for next_node in self.fsa.g.successors(fsa_current_state[0]):
            neighbors.append(next_node)
            self.construct_partition(next_node)
        print("neighbors:", neighbors)
        return neighbors

    def construct_partition(self, nq):

        '''
        Create two partitions self.q_min2final and self.not_q_min2final
        list self.q_min2final : maintains a list of one-step reachable states wrt current state in FSA that have min distance to the accepting state
        list self.not_q_min2final : a list of one-step reachable states wrt the current state in FSA whose distance from final state is more than min_dis1


        Sample from self.q_min2final with a higher probability than from self.not_q_min2final
        '''
        self.q_min2final = []
        self.not_q_min2final = []

        self.min_dis1 = np.inf

        if len(nx.shortest_path(self.fsa.g, nq, self.final_states[0])) < self.min_dis1:
            # self.min_dis = self.fsa.min_length[(q_p_new[1], self.fsa_final)]
            self.min_dis1 = nx.dijkstra_path_length(self.fsa.g, nq, self.final_states[0], weight='weight')
            print("distance:", self.min_dis1)
            self.path_fsa = nx.bidirectional_shortest_path(self.fsa.g, nq, self.final_states[0])

            print("path:", self.path_fsa)

            self.not_q_min2final = self.not_q_min2final + self.q_min2final
            self.q_min2final = [nq]

            # equivalent to
        elif nx.shortest_path(self.fsa.g, q_p_new[1], self.final_states[0]) == self.min_dis1:
            self.q_min2final = self.q_min2final + [q_p_new]
            # larger than
        else:
            self.not_q_min2final = self.not_q_min2final + [q_p_new]
        print("qmin:", self.q_min2final)


    def get_two_reachable_set(self):

        for each_node in self.q_min2final:
            neighbors_of_neighbors = {}
            neighbors = []
            for next_node in self.fsa.g.successors(each_node):
                neighbors.append(next_node)
            neighbors_of_neighbors[each_node] = neighbors
        return neighbors_of_neighbors
    
    
    def modify_partitions(self, next_next_neighbors):

        self.min_dis2 = np.inf

        for each_neighbor in self.q_min2final:
            for next_state in next_next_neighbors[each_neighbor]:
                if len(nx.shortest_path(self.fsa.g, next_state, self.final_states[0])) < self.min_dis2:
                    self.min_dis2 = nx.dijkstra_path_length(self.fsa.g, next_state, self.final_states[0], weight='weight')
                    self.path_fsa = nx.bidirectional_shortest_path(self.fsa.g, next_state, self.final_states[0])
                    print("path:", self.path_fsa)


            if self.min_dis2 - 1 == self.min_dis1:
                self.q_min2final.remove(each_neighbor)

    def sample_fsa_state(self):
        next = [[self.q_min2final], [self.not_q_min2final] ]
        indices = [0,1]
        prob = 0.8
        set_to_choose_from = random.choices(indices, weights = (prob, 1-prob))

        # n = len(set_to_choose_from)
        print(self.q_min2final)
        print("set:", set_to_choose_from)

        chosen_state = self.sample_uniform_geometry(next[set_to_choose_from[0]])
        print("choice:", chosen_state)
        return chosen_state

    def uniform_geometry(self, n):
        p = 1/n
        b = -p*numpy.log(p)/(1-p)
        for pdf in uniform_geometry_pdf(p, n):
            b += pdf
        return b

    def uniform_geometry_cdf(self, n, b_max):
        p = 1/n
        b = -p * numpy.log(p) / (1 - p)
        if b > b_max: return 1
        index = 1
        for pdf in uniform_geometry_pdf(p, n):
            b += pdf
            index += 1
            if b > b_max: return index


    def sample_uniform_geometry(self, group):
        if len(group) == 1:
            return group[0]
        reversed_group = group[::-1]
        n = len(reversed_group)
        b = uniform_geometry(n)
        cdf = numpy.random.uniform(0, b, 1)[0]
        return reversed_group[uniform_geometry_cdf(n, cdf)-1]


    def uniform_geometry_pdf(p, x):
        a = -p*numpy.log(p)/(1-p)
        for i in range(1, x):
            a -= p*numpy.power(1-p, i-1)/i
            yield a


def project_on_ts(ts, current_ts, fsa, symbol):

    '''Inputs:

    * ts <digraph>: TS model
    * symbol <bitmap value>: symbbol necessary to transition to the sampled FSA state from the current FSA state

    Output:
    * path_final <list>: Shortest path in TS, if one exists, that generates the required 'symbol'

    Note: For simplicity, we assume that the symbols are unique i.e., only one state in TS with a particular lable '''

    print(ts.g.edges(data=True))
    print(ts.g.nodes(data=True))
    print("looking for : ", symbol)
    node_data = ts.g.nodes(data=True)
    for item in node_data:
        print(item[1])
        if item[1].get('prop'):
            print(item[1].get('prop'))
            if fsa.bitmap_of_props(item[1].get('prop')) == symbol:
                path = nx.bidirectional_shortest_path(ts.g, current_ts, item[0])
                print("path found:", path)
                return path
