import networkx as nx
import portion
import itertools

def remove_repeated_ints(old_list):

	'''This function is used for merging the intervals with same values in the final distance dictionaries'''

	for node in old_list:
		rev1_dict = {}
		for key, value in old_list[node].items():
			rev1_dict.setdefault(value, set()).add(key)
		# If repeated values found, store the corresponding keys in a set
		result = set(itertools.chain.from_iterable(values for key, values in rev1_dict.items() if len(values) > 1))

		if len(result) :
			print("repeated intervals: ", result)
			result = list(result)
			# Portion's function for taking a union of intervals
			Iv_merged = result[0] | result[1]
			print("merged:", Iv_merged)
			# As the values corresponding to all keys in result are the same, store one of them in the final distance dictionary
			old_list[node][Iv_merged] = old_list[node][result[0]]
			for reps in result:
				del old_list[node][reps]
	return old_list


# def createList(r1, r2):
# 	return [item for item in range(r1, r2+1)]


def dijkstra2(G, source):
	''' A parametric Dijkstra function for a two-weight directed edges planar graph problem'''

	d1 = {} 							#dictionary of distances corresponding to w1
	d2 = {} 							#dictionary of distances corresponding to w2
	p = {}  							#dictionary of predecessors

	Iu = portion.closed(0,1) 			#A closed interval for parameter values
	Iv = portion.closed(0,1) 			#A closed interval for parameter values

	q = [] 								#Priority queue

	#Initially all distances are infinite and distance of source from itself is zero


	for node in G.nodes(): 
		d1 [node] = {}
		d2 [node] = {}
		p[node] = {}
		# d1 [node][Iu] = float('inf')
		# d2 [node][Iu] = float('inf')
		d1 [node][Iu] = 100000   # Temporary adjustment
		d2 [node][Iu] = 100000
		if node == source:
			d1[node][Iu] = 0
			d2[node][Iu] = 0
		q.append([node,Iu])
		
	while len(q): 
		loop_function(G,q,d1,d2,p)

	remove_repeated_ints(d1)
	remove_repeated_ints(d2)

	return d1, d2

def loop_function(G,q,d1,d2,p):

	'''This function computes the priority queue for the nodes to be visited'''

	cost = {}

	for v,Iv in q:
		cost[v] = {}
		Iv_value = list(d1[v])
		Iv = Iv_value[0]
		# ------------------------------------------------------------
		## min value for lower OR upper bound
		current_cost = []
		for param in [Iv.lower, Iv.upper]:       # Assuming that the min values appear at the end points
			current_cost.append( param * d1[v][Iv] + (1-param)* d2 [v][Iv])
		cost[v][Iv] = min(current_cost)

		# ------------------------------------------------------------
		## Initial implementation
		# for param in [Iv.lower, Iv.upper]:
		# 	cost[v][Iv] = param * d1[v][Iv] + (1-param)* d2 [v][Iv]

		# ------------------------------------------------------------
		## summation of costs for upper and lower bounds

		# lambda_low = Iv.lower
		# lambda_upper = Iv.upper
		# cost_low = lambda_low * d1[v][Iv] + (1-lambda_low)* d2 [v][Iv]
		# cost_upper = lambda_upper * d1[v][Iv] + (1-lambda_upper)* d2 [v][Iv]
		# cost[v][Iv] = cost_low + cost_upper
		# --------------------------------------------------------------

	# Finding the argmin of minimum values of the cost function
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

	for next_pair in q:
		if next_pair[0] == u:
			q.remove(next_pair)

	# iterate over successors of the current node u
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

	'''This function compares the outputs the intervals in which a particular path is optimal and the corresponding cost'''

	i_int = Iu & Iv
	assert not i_int.empty

	weights = G.get_edge_data(u,v)
	d1_temp = d1[u][Iu] + weights['weight1']
	d2_temp = d2[u][Iu] + weights['weight2']
	print("new d: ", d1_temp, d2_temp)
	param_low, param_high = i_int.lower, i_int.upper
	J_l = param_low * d1[v][Iv] + (1 - param_low) * d2[v][Iv]
	J_h = param_high * d1[v][Iv] + (1 - param_high)\
		  * d2[v][Iv]

	J_l_new = param_low * d1_temp + (1 - param_low)* d2_temp
	J_h_new = param_high * d1_temp + (1 - param_high)* d2_temp

	print ("costs: ", J_l, J_h, J_l_new, J_h_new)

	if (J_l <= J_l_new) and (J_h <= J_h_new):   # no improvement
		print("no improvement")
		pass

	## Todo: include conditions for combinations of equal costs

	elif (J_l > J_l_new) and (J_h > J_h_new):  # all improve
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
		Iv1 = i_int
		Iv2 = Iv - i_int
		print("Iv2: ", Iv2)

		if Iv2.empty:
			print("Iv2 is phi")
			if denom > 0 :
				Iv_new = portion.closed(split,param_high)
				d1[v][Iv_new] = d1_temp
				d2[v][Iv_new] = d2_temp
				p[v][Iv_new] = u
				
				Iv_remaining = portion.closed(Iv.lower, split) 
				d1[v][Iv_remaining] = d1[v][Iv]
				d2[v][Iv_remaining] = d2[v][Iv]
				del d1[v][Iv]
				del d2[v][Iv]
			else:
				Iv_new = portion.closed(param_low,split)
				d1[v][Iv_new] = d1_temp
				d2[v][Iv_new] = d2_temp
				p[v][Iv_new] = u
				
				Iv_remaining = portion.closed( split, Iv.upper)
				d1[v][Iv_remaining] = d1[v][Iv]
				d2[v][Iv_remaining] = d2[v][Iv]
				del d1[v][Iv]
				del d2[v][Iv]

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
				
				Iv_remaining = portion.closed( split, Iv.upper)
				d1[v][Iv_remaining] = d1[v][Iv]
				d2[v][Iv_remaining] = d2[v][Iv]
				del d1[v][Iv]
				del d2[v][Iv]

	print ("d1:", d1)
	print ("d2:", d2)


def find_split(d1_temp, d2_temp, d1_value, d2_value):

	denominator = d1_value - d1_temp + d2_temp - d2_value
	assert denominator != 0 
	split = (d2_temp-d2_value)/ denominator

	return  split, denominator


if __name__== '__main__':

	G = nx.DiGraph()
	G.add_nodes_from([1,2,3,4,5])
	G.add_edges_from([(1,2,{'weight1':10, 'weight2': 1}), (1,3,{'weight1':2, 'weight2': 2}), (1,4,{'weight1':1, 'weight2': 10}),
		(2,5,{'weight1':10, 'weight2': 1}), (3,5,{'weight1':2, 'weight2': 2}),(4,5,{'weight1':1, 'weight2': 10})])

	source = 1
	d1, d2 = dijkstra2(G, source)
	print(d1)
	print(d2)
