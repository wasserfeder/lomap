#! /usr/bin/python

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

from __future__ import print_function

import sys
import traceback
import logging

try:
    import pp
    pp_installed = True
except ImportError:
    pp_installed = False
import networkx as nx

from lomap.classes import Buchi
from lomap.algorithms.product import ts_times_buchi
from lomap.algorithms.dijkstra import (source_to_target_dijkstra,
                                       subset_to_subset_dijkstra_path_value)

# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

# Cluster configuration
#SERVER_ADDR is the ip address of the computer running lomap
#pp_servers is a tuple of server ips that are running ppserver.py
#SERVER_ADDR = '107.20.62.59'
#pp_servers = ('23.22.80.26', '50.17.177.92', '50.16.82.182', '50.16.116.126')
SERVER_ADDR = 'localhost'
pp_servers = ()
SERVER_PORT = 60001
data_source = (SERVER_ADDR, SERVER_PORT)

def optimal_run(t, formula, opt_prop):
    try:
        logger.info('T has %d states', len(t.g))
        # Convert formula to Buchi automaton
        b = Buchi()
        b.from_formula(formula)
        logger.info('B has %d states', len(b.g))
        # Compute the product automaton
        p = ts_times_buchi(t, b)
        logger.info('P has %d states', len(p.g))
        logger.info('Set F has %d states', len(p.final))
        # Find the set S of states w/ opt_prop
        s = p.nodes_w_prop(opt_prop)
        logger.info('Set S has %d states', len(s))
        # Compute the suffix_cycle* and suffix_cycle_cost*
        suffix_cycle_cost, suffix_cycle_on_p = min_bottleneck_cycle(p.g, s, p.final)
        # Compute the prefix: a shortest path from p.init to suffix_cycle
        prefix_length = float('inf')
        prefix_on_p = ['']
        i_star = 0
        for init_state in p.init.keys():
            for i in range(0,len(suffix_cycle_on_p)):
                length, prefix = source_to_target_dijkstra(p.g, init_state, suffix_cycle_on_p[i], degen_paths = True)
                if(length < prefix_length):
                    prefix_length = length
                    prefix_on_p = prefix
                    i_star = i

        if(prefix_length == float('inf')):
            raise Exception(__name__, 'Could not compute the prefix.')

        # Wrap suffix_cycle_on_p as required
        if i_star != 0:
            # Cut and paste
            suffix_cycle_on_p = suffix_cycle_on_p[i_star:] + suffix_cycle_on_p[1:i_star+1]

        # Compute projection of prefix and suffix-cycle to T and return
        suffix_cycle = [x[0] for x in suffix_cycle_on_p]
        prefix = [x[0] for x in prefix_on_p]
        return (prefix_length, prefix, suffix_cycle_cost, suffix_cycle)
    except Exception as ex:
        if(len(ex.args) == 2):
            print("{}: {}".format(*ex.args))
        else:
            print("{}: Unknown exception {}: {}".format(__name__, type(ex), ex))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            exit(1)

def find_best_cycle(f, s, d_f_to_s, d_s_to_f, d_bot):
    import itertools

    cost_star = float('inf')
    len_star = float('inf')
    cycle_star = None
    for triple in itertools.product(f, s, s):
        (ff, s1, s2) = triple
        f_s_cycle_cost = d_f_to_s[ff][s1] + d_s_to_f[s2][ff]
        # Cost and length of this triple
        if s1 == s2 and ff != s1:
            cost = f_s_cycle_cost
            this_len = f_s_cycle_cost
        else:
            cost = max(f_s_cycle_cost, d_bot[s1][s2][0])
            this_len = f_s_cycle_cost + d_bot[s1][s2][1]

        if(cost < cost_star or (cost == cost_star and this_len < len_star)):
            cost_star = cost
            len_star = this_len
            cycle_star = triple

    return (cost_star, len_star, cycle_star)

def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def job_worker(chunk, data_source, func_name):
    global data_id
    global my_data
    import socket
    import pickle

    need_data = False

    # Get new_data_id
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(data_source)
    sock.sendall('data_id')
    new_data_id = sock.recv(64)
    sock.close()

    if 'data_id' in globals():
        if new_data_id != data_id:
            need_data = True
    else:
        need_data = True

    if need_data:# or 'my_data' not in globals():
        # Get new data from data_address
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(data_source)
        sock.sendall('data')
        new_data = ''
        while True:
            this_data = sock.recv(8192)
            if not this_data:
                break
            new_data += this_data
        sock.close()
        my_data = pickle.loads(new_data)
        # set the data_id
        data_id = new_data_id

    # Call the dijkstra routine for this source_chunk
    return eval(func_name+'(chunk, *my_data)')

def job_dispatcher(job_server, func, arg_to_split, chunk_size, data_id, data, data_source):
    import socket
    import threading
    from six.moves import socketserver
    import pickle

    pickled_data = pickle.dumps(data,pickle.HIGHEST_PROTOCOL)

    # Data Server Configuration
    class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
        def handle(self):
            req = self.request.recv(32)
            if req == 'data_id':
                self.request.sendall(data_id)
                #logger.info('data_id req received from %s', self.client_address)
            elif req == 'data':
                self.request.sendall(pickled_data)
                logger.info('Served dataset %s to %s', data_id, self.client_address)
            else:
                assert(False)

    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        pass

    # Start the server
    server = ThreadedTCPServer(('0.0.0.0',data_source[1]), ThreadedTCPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    # Array of dispatched jobs
    jobs = []
    # Split sl to chunks of size chunk_size
    arg_chunks = chunks(arg_to_split, chunk_size)
    # Dispatch jobs, job_worker will load static data from data_source
    for chunk in arg_chunks:
        jobs.append(job_server.submit(job_worker, (chunk, data_source, func.__name__), (func,)))

    # Wait for all jobs to complete
    job_server.wait()
    job_server.print_stats()

    # Shutdown the data server
    server.shutdown()
    server.server_close()

    return jobs

def min_bottleneck_cycle(g, s, f):
    """ Returns the minimum bottleneck cycle from s to f in graph g.

    An implementation of the Min-Bottleneck-Cycle Algortihm
    in S.L. Smith, J. Tumova, C. Belta, D. Rus " Optimal Path Planning
    for Surveillance with Temporal Logic Constraints", in IJRR.

    Parameters
    ----------
    g : NetworkX graph

    s : A set of nodes
        These nodes satisfy the optimizing proposition.

    f : A set of nodes
        These nodes are the final states of B x T product.

    Returns
    -------
    cycle : List of node labels.
        The minimum bottleneck cycle S->F->S

    Examples
    --------

    Notes
    -----

    """

    global pp_installed
    if not pp_installed:
        raise Exception('This functionality is not enables because, '
                        'Parallel Python not installed!')

    # Start job server
    job_server = pp.Server(ppservers=pp_servers, secret='trivial')

    # Compute shortest S->S and S->F paths
    logger.info('S->S+F')
    #d = subset_to_subset_dijkstra_path_value(g, s, s|f, degen_paths = False)
    jobs = job_dispatcher(job_server, subset_to_subset_dijkstra_path_value, list(s), 1, '0', (g, s|f, 'sum', False, 'weight'), data_source)
    d = dict()
    for i in range(0,len(jobs)):
        d.update(jobs[i]())
        jobs[i]=''
    del jobs
    logger.info('Collected results for S->S+F')

    # Create S->S, S->F dict of dicts
    g_s_edges = []
    d_s_to_f = dict()
    for src in d.keys():
        for dest in d[src].keys():
            if dest in s:
                w = d[src][dest]
                g_s_edges.append((src,dest,w))
            if dest in f:
                # We allow degenerate S->F paths
                w = 0 if src == dest else d[src][dest]
                if src not in d_s_to_f:
                    d_s_to_f[src] = dict()
                d_s_to_f[src][dest] = w

    # Create the G_s graph
    g_s = nx.MultiDiGraph()
    g_s.add_weighted_edges_from(g_s_edges)
    # Remove d and g_s_edges to save memory
    del d
    del g_s_edges

    # Compute shortest F->S paths
    logger.info('F->S')
    #d_f_to_s = subset_to_subset_dijkstra_path_value(g, f, s, degen_paths = True)
    jobs = job_dispatcher(job_server, subset_to_subset_dijkstra_path_value, list(f), 1, '1', (g, s, 'sum', True, 'weight'), data_source)
    d_f_to_s = dict()
    for i in range(0,len(jobs)):
        d_f_to_s.update(jobs[i]())
        jobs[i]=''
    del jobs
    logger.info('Collected results for F->S')

    # Compute shortest S-bottleneck paths between verices in s
    logger.info('S-bottleneck')
    #d_bot = subset_to_subset_dijkstra_path_value(g_s, s, s, combine_fn = (lambda a,b: max(a,b)), degen_paths = False)
    jobs = job_dispatcher(job_server, subset_to_subset_dijkstra_path_value, list(s), 1, '2', (g_s, s, 'max', False, 'weight'), data_source)

    d_bot = dict()
    for i in range(0,len(jobs)):
        d_bot.update(jobs[i]())
        jobs[i]=''
    del jobs
    logger.info('Collected results for S-bottleneck')

    # Find the triple \in F x S x S that minimizes C(f,s1,s2)
    logger.info('Path*')
    jobs = job_dispatcher(job_server, find_best_cycle, list(f), 1, '3', (s, d_f_to_s, d_s_to_f, d_bot), data_source)
    cost_star = float('inf')
    len_star = float('inf')
    cycle_star = None
    for i in range(0,len(jobs)):
        this_cost, this_len, this_cycle = jobs[i]()
        jobs[i]=''
        if (this_cost < cost_star or (this_cost == cost_star and this_len < len_star)):
            cost_star = this_cost
            len_star = this_len
            cycle_star = this_cycle
    del jobs
    logger.info('Collected results for Path*')
    logger.info('Cost*: %d, Len*: %d, Cycle*: %s', cost_star, len_star, cycle_star)

    if cost_star == float('inf'):
        raise Exception(__name__, 'Failed to find a satisfying cycle, spec cannot be satisfied.')

    else:
        logger.info('Extracting Path*')
        (ff, s1, s2) = cycle_star
        # This is the F->S1 path
        (cost_ff_to_s1, path_ff_to_s1) = source_to_target_dijkstra(g, ff, s1, degen_paths = True, cutoff = d_f_to_s[ff][s1])
        # This is the S2->F path
        (cost_s2_to_ff, path_s2_to_ff) = source_to_target_dijkstra(g, s2, ff, degen_paths = True, cutoff = d_s_to_f[s2][ff])
        if s1 == s2 and ff != s1:
            # The path will be F->S1==S2->F
            path_star = path_ff_to_s1[0:-1] + path_s2_to_ff
            assert(cost_star == (cost_ff_to_s1 + cost_s2_to_ff))
            assert(len_star == (cost_ff_to_s1 + cost_s2_to_ff))
        else:
            # The path will be F->S1->S2->F
            # Extract the path from s_1 to s_2
            (bot_cost_s1_to_s2, bot_path_s1_to_s2) = source_to_target_dijkstra(g_s, s1, s2, combine_fn = 'max', degen_paths = False, cutoff = d_bot[s1][s2][0])
            assert(cost_star == max((cost_ff_to_s1 + cost_s2_to_ff),bot_cost_s1_to_s2))
            path_s1_to_s2 = []
            cost_s1_to_s2 = 0
            for i in range(1,len(bot_path_s1_to_s2)):
                source = bot_path_s1_to_s2[i-1]
                target = bot_path_s1_to_s2[i]
                cost_segment, path_segment = source_to_target_dijkstra(g, source, target, degen_paths = False)
                path_s1_to_s2 = path_s1_to_s2[0:-1] + path_segment
                cost_s1_to_s2 += cost_segment
            assert(len_star == cost_ff_to_s1 + cost_s1_to_s2 + cost_s2_to_ff)

            # path_ff_to_s1 and path_s2_to_ff can be degenerate paths,
            # but path_s1_to_s2 cannot, thus path_star is defined as this:
            # last ff is kept to make it clear that this is a suffix-cycle
            path_star = path_ff_to_s1[0:-1] + path_s1_to_s2[0:-1] + path_s2_to_ff

        return (cost_star, path_star)
