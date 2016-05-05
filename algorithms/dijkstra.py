# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
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

__all__ = ['subset_to_subset_dijkstra_path_value', 'source_to_target_dijkstra', 'dijkstra_to_all']

def subset_to_subset_dijkstra_path_value(source_set, G, target_set, combine_fn = 'sum', degen_paths = False, weight_key = 'weight'):
	"""
	Compute the shortest path lengths between two sets of nodes in a weighted graph.
	Adapted from 'single_source_dijkstra_path_length' in NetworkX, available at
	http://networkx.github.io.

	Parameters
	----------
	G: NetworkX graph

	source_set: Set of node labels
		Starting nodes for paths

	target_set: Set of node labels
		Ending nodes for paths

	combine_fn: Function, optional (default: (lambda a,b: a+b))
		Function used to combine two path values

	degen_paths: Boolean, optional (default: False)
		Controls whether degenerate paths (paths that do not traverse any edges)
		are acceptable.

	weight_key: String, optional (default: 'weight')
		Edge data key corresponding to the edge weight.

	Returns
	-------
	length : dictionary
		Dictionary of dictionaries of shortest lengths keyed by source and target labels.

	Notes
	-----
	Edge weight attributes must be numerical.
	This algorithm is not guaranteed to work if edge weights
	are negative or are floating point numbers
	(overflows and roundoff errors can cause problems). 
	Input is assumed to be a MultiDiGraph with singleton edges.
	"""
	import heapq

	all_dist = {} # dictionary of final distances from source_set to target_set

	if combine_fn == 'sum':
		# Classical dijkstra
	
		for source in source_set:
			dist = {} # dictionary of final distances from source
			fringe=[] # use heapq with (distance,label) tuples 
	
			if degen_paths:
				# Allow degenerate paths
				# Add zero length path from source to source
				seen = {source:0} 
				heapq.heappush(fringe,(0,source))
			else:
				# Don't allow degenerate paths
				# Add all neighbors of source to start the algorithm
				seen = dict()
				for w,edgedict in iter(G[source].items()):
					edgedata = edgedict[0]
					vw_dist = edgedata[weight_key]
					seen[w] = vw_dist
					heapq.heappush(fringe,(vw_dist,w))
	
			while fringe:
				(d,v)=heapq.heappop(fringe)
	
				if v in dist: 
					continue # Already searched this node.
	
				dist[v] = d	# Update distance to this node
	
				for w,edgedict in iter(G[v].items()):
					edgedata = edgedict[0]
					vw_dist = dist[v] + edgedata[weight_key]
					if w in dist:
						if vw_dist < dist[w]:
							raise ValueError('Contradictory paths found:','negative weights?')
					elif w not in seen or vw_dist < seen[w]:
						seen[w] = vw_dist
						heapq.heappush(fringe,(vw_dist,w))
	
			# Remove the entries that we are not interested in 
			for key in dist.keys():
				if key not in target_set:
					dist.pop(key)
	
			# Add inf cost to target nodes not in dist
			for t in target_set:
				if t not in dist.keys():
					dist[t] = float('inf')
	
			# Save the distance info for this source
			all_dist[source] = dist

	elif combine_fn == 'max':
		# Path length is (max edge length, total edge length)
	
		for source in source_set:
			dist = {} # dictionary of final distances from source
			fringe=[] # use heapq with (bot_dist,dist,label) tuples 
	
			if degen_paths:
				# Allow degenerate paths
				# Add zero length path from source to source
				seen = {source:(0,0)} 
				heapq.heappush(fringe,(0,0,source))
			else:
				# Don't allow degenerate paths
				# Add all neighbors of source to start the algorithm
				seen = dict()
				for w,edgedict in iter(G[source].items()):
					edgedata = edgedict[0]
					vw_dist = edgedata[weight_key]
					seen[w] = (vw_dist,vw_dist)
					heapq.heappush(fringe,(vw_dist,vw_dist,w))
	
			while fringe:
				(d_bot,d_sum,v)=heapq.heappop(fringe)
	
				if v in dist: 
					continue # Already searched this node.
	
				dist[v] = (d_bot,d_sum)	# Update distance to this node
	
				for w,edgedict in iter(G[v].items()):
					edgedata = edgedict[0]
					vw_dist_bot = max(dist[v][0],edgedata[weight_key])
					vw_dist_sum = dist[v][1] + edgedata[weight_key]
					if w in dist:
						if vw_dist_bot < dist[w][0]:
							raise ValueError('Contradictory paths found:','negative weights?')
					elif w not in seen or vw_dist_bot < seen[w][0] or (vw_dist_bot == seen[w][0] and vw_dist_sum < seen[w][1]):
						seen[w] = (vw_dist_bot, vw_dist_sum)
						heapq.heappush(fringe,(vw_dist_bot,vw_dist_sum,w))
	
			# Remove the entries that we are not interested in 
			for key in dist.keys():
				if key not in target_set:
					dist.pop(key)
	
			# Add inf cost to target nodes not in dist
			for t in target_set:
				if t not in dist.keys():
					dist[t] = (float('inf'),float('inf'))
	
			# Save the distance info for this source
			all_dist[source] = dist
	else:
		assert(False)

	return all_dist



def dijkstra_to_all(G, source, degen_paths = False, weight_key='weight'):
	"""
	Compute shortest paths and lengths in a weighted graph G.
	Adapted from 'single_source_dijkstra_path' in NetworkX, available at
	http://networkx.github.io.

	Parameters
	----------
	G : NetworkX graph

	source : Node label
		Starting node for the path

	weight_key: String, optional (default: 'weight')
		Edge data key corresponding to the edge weight.

	Returns
	-------
	distance,path : Tuple
		Returns a tuple distance and path from source to target.

	Notes
	---------
	Edge weight attributes must be numerical.

	Based on the Python cookbook recipe (119466) at 
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/119466

	This algorithm is not guaranteed to work if edge weights
	are negative or are floating point numbers
	(overflows and roundoff errors can cause problems). 
	"""
	import heapq

	dist = {}	# dictionary of final distances
	fringe=[] # use heapq with (distance,label) tuples 

	if degen_paths:
		# Allow degenerate paths
		# Add zero length path from source to source
		seen = {source:0} 
		heapq.heappush(fringe,(0,source))
		paths = {source:[source]}
	else:
		# Don't allow degenerate paths
		# Add all neighbors of source to start the algorithm
		paths = dict()
		seen = dict()
		for w,edgedict in iter(G[source].items()):
			edgedata = edgedict[0]
			vw_dist = edgedata[weight_key]
			paths[w] = [source, w]
			seen[w] = vw_dist
			heapq.heappush(fringe,(vw_dist,w))

	while fringe:
		(d,v)=heapq.heappop(fringe)

		if v in dist: 
			continue # already searched this node.

		dist[v] = d	# Update distance to this node

		for w,edgedict in iter(G[v].items()):
			edgedata = edgedict[0]
			vw_dist = dist[v] + edgedata[weight_key]
			if w in dist:
				if vw_dist < dist[w]:
					raise ValueError('Contradictory paths found:', 'negative weights?')
			elif w not in seen or vw_dist < seen[w]:
				seen[w] = vw_dist
				paths[w] = paths[v]+[w]
				heapq.heappush(fringe,(vw_dist,w))

	return (dist, paths)


def source_to_target_dijkstra(G, source, target, combine_fn = 'sum', degen_paths = False, cutoff=None, weight_key='weight'):
	"""
	Compute shortest paths and lengths in a weighted graph G.
	Adapted from 'single_source_dijkstra_path' in NetworkX, available at
	http://networkx.github.io.

	Parameters
	----------
	G : NetworkX graph

	source : Node label
		Starting node for the path

	target : Node label
		Ending node for the path 

	degen_paths: Boolean, optional (default: False)
		Controls whether degenerate paths (paths that do not traverse any edges)
		are acceptable.

	cutoff : integer or float, optional (default: None)
		Depth to stop the search. Only paths of length <= cutoff are returned.

	weight_key: String, optional (default: 'weight')
		Edge data key corresponding to the edge weight.

	Returns
	-------
	distance,path : Tuple
		Returns a tuple distance and path from source to target.

	Examples
	--------
	>>> G=networkx.path_graph(5)
	>>> length,path=source_to_target_dijkstra(G,0,4)
	>>> print(length)
	4
	>>> path
	[0, 1, 2, 3, 4]

	Notes
	---------
	Edge weight attributes must be numerical.

	Based on the Python cookbook recipe (119466) at 
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/119466

	This algorithm is not guaranteed to work if edge weights
	are negative or are floating point numbers
	(overflows and roundoff errors can cause problems). 
	"""
	import heapq

	dist = {}	# dictionary of final distances
	fringe=[] # use heapq with (distance,label) tuples 

	if combine_fn == 'sum':
		if degen_paths:
			# Allow degenerate paths
			if source==target: 
				# Terminate immediately if source == target
				return (0, [source])
			else:
				# Add zero length path from source to source
				paths = {source:[source]}	# dictionary of paths
				seen = {source:0} 
				heapq.heappush(fringe,(0,source))
		else:
			# Don't allow degenerate paths
			# Add all neighbors of source to start the algorithm
			paths = dict()
			seen = dict()
			for w,edgedict in iter(G[source].items()):
				edgedata = edgedict[0]
				vw_dist = edgedata[weight_key]
				paths[w] = [source, w]
				seen[w] = vw_dist
				heapq.heappush(fringe,(vw_dist,w))

		while fringe:
			(d,v)=heapq.heappop(fringe)

			if v in dist: 
				continue # already searched this node.

			dist[v] = d	# Update distance to this node
			if v == target: 
				break	# Discovered path to target node

			for w,edgedict in iter(G[v].items()):
				edgedata = edgedict[0]
				vw_dist = dist[v] + edgedata[weight_key]
				if cutoff is not None:
					if vw_dist>cutoff: 
						continue	# Longer than cutoff, ignore this path
				if w in dist:
					if vw_dist < dist[w]:
						raise ValueError('Contradictory paths found:', 'negative weights?')
				elif w not in seen or vw_dist < seen[w]:
					seen[w] = vw_dist
					paths[w] = paths[v]+[w]
					heapq.heappush(fringe,(vw_dist,w))

		# Add inf cost to target if not in dist
		if target not in dist.keys():
			dist[target] = float('inf')
			paths[target] = ['']

		return (dist[target],paths[target])

	elif combine_fn == 'max':

		if degen_paths:
			# Allow degenerate paths
			if source==target: 
				# Terminate immediately if source == target
				return (0, [source])
			else:
				# Add zero length path from source to source
				paths = {source:[source]}	# dictionary of paths
				seen = {source:(0,0)} 
				heapq.heappush(fringe,(0,0,source))
		else:
			# Don't allow degenerate paths
			# Add all neighbors of source to start the algorithm
			paths = dict()
			seen = dict()
			for w,edgedict in iter(G[source].items()):
				edgedata = edgedict[0]
				vw_dist = edgedata[weight_key]
				paths[w] = [source, w]
				seen[w] = (vw_dist, vw_dist)
				heapq.heappush(fringe,(vw_dist,vw_dist,w))

		while fringe:
			(d_bot,d_sum,v)=heapq.heappop(fringe)

			if v in dist: 
				continue # already searched this node.

			dist[v] = (d_bot,d_sum)	# Update distance to this node
			if v == target: 
				break	# Discovered path to target node

			for w,edgedict in iter(G[v].items()):
				edgedata = edgedict[0]
				vw_dist_bot = max(dist[v][0], edgedata[weight_key])
				vw_dist_sum = dist[v][1] + edgedata[weight_key]
				if cutoff is not None:
					if vw_dist_bot>cutoff: 
						continue	# Longer than cutoff, ignore this path
				if w in dist:
					if vw_dist_bot < dist[w][0]:
						raise ValueError('Contradictory paths found:', 'negative weights?')
				elif w not in seen or vw_dist_bot < seen[w][0] or (vw_dist_bot == seen[w][0] and vw_dist_sum < seen[w][1]):
					seen[w] = (vw_dist_bot, vw_dist_sum)
					paths[w] = paths[v]+[w]
					heapq.heappush(fringe,(vw_dist_bot,vw_dist_sum,w))

		# Add inf cost to target if not in dist
		if target not in dist.keys():
			dist[target] = (float('inf'),float('inf'))
			paths[target] = ['']

		return (dist[target][0],paths[target])
	else:
		assert(False)
