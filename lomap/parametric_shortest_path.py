import networkx as nx
import numpy as np
import portion


def createList(r1, r2): 
	return [item for item in range(r1, r2+1)]


def construct_graph(G, source):


	d1 = {} #dictionary of distances corresponding to w1
	d2 = {} #dictionary of distances corresponding to w2
	p = {}  #dictionary of predecessors
	# Iu = (0,1)
	# Iv = (0,1)
	# interval_u = portion.closed(Iu[0],Iu[1])
	# interval_v = portion.closed(Iv[0],Iv[1])

	Iu = portion.closed(0,1)
	Iv = portion.closed(0,1)

	q = [] 

	#Initially all distances are infinite

	for node in G.nodes(): 
		d1 [node] = {}
		d2 [node] = {}
		p[node] = {}
		# d1 [node][Iu] = float('inf')
		# d2 [node][Iu] = float('inf')
		d1 [node][Iu] = 100000
		d2 [node][Iu] = 100000
		if node == source:
			d1[node][Iu] = 0
			d2[node][Iu] = 0

		q.append([node,Iu])
		
	while len(q): 
		loop_function(G,q,d1,d2,p)

	return d1, d2

def loop_function(G,q,d1,d2,p):

	cost = {}

	for v,Iv in q:
		cost[v] = {}
		Iv_value = list(d1[v])
		Iv = Iv_value[0]

		current_cost = []
		for param in [Iv.lower, Iv.upper]:       # Assuming that the min values appear at the end points
			current_cost.append( param * d1[v][Iv] + (1-param)* d2 [v][Iv])
		cost[v][Iv] = min(current_cost)

	print("cost:", cost)

	# for k1 in cost.items():
	# 	for k2 in k1:
	# 		print k1.values()
		# values.append(cost[k1][k2])


	# cost_flat = json_normalize(cost)
	# print cost_flat

	# print cost.items()
	key_one = []   	# u values
	key_two = []	# Iu values
	value = []
	for key in cost:
		key_one.append(key)
		key_two.append(*cost[key])
		for v in cost[key].values():
			value.append(v)

	min_index = value.index(min(value))
	u = key_one[min_index]
	print("min u: ", u)
	Iu = key_two[min_index]

	# 	# min_key = min(sub_dict, key=sub_dict.get)
	# u = min(cost.items(), key=lambda x: x[1])[0]        # corrections needed
	# cost_list = list(cost.items())
	# # print cost_list
	# Iu_sub = min(cost_list, key=lambda x: x[1])[1]
	# key_list = list(Iu_sub.keys())
	# dist_list = list(Iu_sub.values())


	# min_index = np.argmin(dist_list)
	# Iu = key_list[min_index]

	for next_pair in q:
		if next_pair[0] == u :
			q.remove(next_pair)


	neighbours = G.neighbors(u)

	for v in neighbours: 
		for Iv in list(d1[v]):
			assert Iv in d2[v]   # why?
			if Iu & Iv :
				print("---------")
				print("u, v:", u,v)
				print("iu, iv: ", Iu, Iv)
				relax(G,u,Iu,v,Iv,d1,d2, p)



def relax (G,u,Iu,v,Iv,d1,d2,p):

	i_int = Iu & Iv
	assert not i_int.empty

	weights = G.get_edge_data(u,v)
	print ("weights: ", weights)
	d1_temp = d1[u][Iu] + weights['weight1']
	d2_temp = d2[u][Iu] + weights['weight2']
	print("new d: ", d1_temp, d2_temp)
	param_low, param_high = i_int.lower, i_int.upper
	print("parameters:",param_low, param_high)
	J_l = param_low * d1[v][Iv] + (1 - param_low) * d2[v][Iv]
	J_h = param_high * d1[v][Iv] + (1 - param_high)\
		  * d2[v][Iv]

	J_l_new = param_low * d1_temp + (1 - param_low)* d2_temp
	J_h_new = param_high * d1_temp + (1 - param_high)* d2_temp

	print ("costs: ", J_l, J_h, J_h_new, J_l_new)

	if (J_l < J_l_new) and (J_h < J_h_new):   # no improvement
		print("no improvement")
		pass

	elif (J_l > J_l_new) and (J_h > J_h_new):  # all improved1[v][Iv]
		Iv1 = i_int
		Iv2 = Iv - Iv1
		print("improvement")

		if Iv2.empty:
			d1[v][Iv] = d1_temp
			d2[v][Iv] = d2_temp
			p[v][Iv] = u  

		else:                          ## double check this part 
			d1[v][Iv2] = d1[v][Iv]
			d2[v][Iv2] = d2[v][Iv]
			del d1[v][Iv]
			del d2[v][Iv]
			d1[v][Iv2] = d1_temp
			d2[v][Iv2] = d2_temp

			p[v][Iv2] = p[v][Iv]  # is the RHS p[v] or p[u]?
			del p[v][Iv]
			p[u][Iv] = u
	else:

		print("found a cut")

		split, denom = find_split(d1_temp, d2_temp, d1[v][Iv], d2[v][Iv])
		print("split:", split)
		print("denom:", denom)
		# set_distances (d1,d2,d1_temp, d2_temp, split, denom, p)
		Iv1 = i_int
		Iv2 = Iv - i_int

		if not Iv2:
			print("Iv2 is phi")
			if denom > 0 :
				Iv_new = portion.closed(split,param_high)
				d1[v][Iv_new] = d1_temp
				d2[v][Iv_new] = d2_temp
				p[v][Iv_new] = u
			else:
				Iv_new = portion.closed(param_low,split)
				d1[v][Iv_new] = d1_temp
				d2[v][Iv_new] = d2_temp
				p[v][Iv_new] = u

		else:
			if denom > 0:  # needs correction
				Iv_new = portion.closed(split, param_high)
				d1[v][Iv_new] = d1_temp
				d2[v][Iv_new] = d2_temp
				p[v][Iv_new] = u

				Iv_remaining = portion.closed(Iv.lower, split) 
				d1[v][Iv_remaining] = d1[v][Iv]
				d2[v][Iv_remaining] = d2[v][Iv]
				del d1[v][Iv]
				del d2[v][Iv]
			else:
				Iv_new = portion.closed(param_low, split)
				d1[v][Iv_new] = d1_temp
				d2[v][Iv_new] = d2_temp
				p[v][Iv_new] = u

	print ("d1:", d1)
	print ("d2:", d2)





def find_split(d1_temp, d2_temp, d1_value, d2_value):

	denominator = d1_temp - d2_temp + d2_value - d1_value
	assert denominator != 0 
	split = (d2_value-d2_temp)/ denominator

	return  split, denominator


if __name__== '__main__':

	G = nx.DiGraph()
	G.add_nodes_from([1,2,3,4,5])
	G.add_edges_from([(1,2,{'weight1':10, 'weight2': 1}), (1,3,{'weight1':2, 'weight2': 2}), (1,4,{'weight1':1, 'weight2': 10}),
		(2,5,{'weight1':10, 'weight2': 1}), (3,5,{'weight1':2, 'weight2': 2}),(4,5,{'weight1':1, 'weight2': 10})])

	source = 1
	d1, d2 = construct_graph(G, source)
	print(d1)