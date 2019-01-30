#!/usr/bin/env python

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

# Case studies presented in:
#
# A. Ulusoy, T. Wongpiromsarn, C. Belta, "Incremental Controller
# Synthesis in Probabilistic Environments with Temporal Logic
# Constraints," The International Journal of Robotics Research,
# vol. 33, no. 8, pp. 1130-1144, 2014.

import lomap
import logging
import networkx as nx
import time
from lomap.algorithms.dijkstra import *
import pprint as pp
import pdb
import copy

# Logger configuration
logger = logging.getLogger(__name__)

def set_props_1(mdp):
    for s in mdp.g:
        # Reset properties of this state
        mdp.g.node[s]['prop'] = set()
        # State of the vehicle
        vehicle = s[0]
        if vehicle == 'vehc2':
            # Define col proposition
            for i in range(0,5):
                ss = 'ped%dc2' % i
                pp = 'col'
                if ss in s:
                    mdp.g.node[s]['prop'] |= set([pp])
        if vehicle == 'vehc4':
            mdp.g.node[s]['prop'] |= set(['end'])

def set_props_2(mdp, assumed_props=()):
    for s in mdp.g:
        # Reset properties of this state
        mdp.g.node[s]['prop'] = set()
        # State of the vehicle
        vehicle = s[0]
        if vehicle == 'vehc2':
            # Can collide or catch
            if 'ped4c2' in s:
                mdp.g.node[s]['prop'] |= set(['col4'])
            # Define regular and assumed props
            for i in range(0,4):
                ss = 'ped%dc2' % i
                pp = 'catch%d' % i
                if ss in s or ss in assumed_props:
                    mdp.g.node[s]['prop'] |= set([pp])
        if vehicle == 'vehc4':
            mdp.g.node[s]['prop'] |= set(['end'])

def set_props_3(mdp):
    for s in mdp.g:
        # Reset properties of this state
        mdp.g.node[s]['prop'] = set()
        # Cell of the vehicle
        veh = int(s[0][4:])
        # Define end
        if veh == 22:
            mdp.g.node[s]['prop'] |= set(['end'])
        # Define unsafe
        trap_loc = [None, 9, 17, 19, 2, 11, 8]
        for i in range(1,7):
            if ('t%don' % i) in s and veh == trap_loc[i]:
                mdp.g.node[s]['prop'] |= set(['unsafe'])

def case_1():

    # Read the vehicle model
    vehicle = lomap.Ts.load('./vehicle_1.yaml')
    # Convert the vehicle model to an MDP
    vehicle_mdp = lomap.Markov()
    vehicle_mdp.mdp_from_det_ts(vehicle)

    # Read the models of the pedestrians
    targets = []
    for i in range(1,6):
        t = lomap.Markov.load('./target_{}.yaml'.format(i))
        targets.append(t)

    formula = '! col U end'

    # Construct the full-state fsa using scheck
    # (full-state ensures proper MDP after product)
    logger.info('Formula: %s' % formula)
    fsa = lomap.Fsa()
    fsa.from_formula(formula)
    fsa.add_trap_state()

    # Classical
    with lomap.Timer('Classical (non-incremental) Method: Case 1 - '
                     'Avoid pedestrians'):
        lomap.classical_synthesis(vehicle_mdp, fsa, targets, set_props_1)
        pass

    # Incremental
    with lomap.Timer('Incremental Method: Case 1 - Avoid pedestrians'):
        lomap.incremental_synthesis(vehicle_mdp, fsa, targets, set_props_1)

def case_2a():

    # Read the vehicle model
    vehicle = lomap.Ts.load('./vehicle_1.yaml')
    # Convert the vehicle model to an MDP
    vehicle_mdp = lomap.Markov()
    vehicle_mdp.mdp_from_det_ts(vehicle)

    # Read the models of the pedestrians
    targets = []
    for i in range(1,6):
        t = lomap.Markov.load('./target_{}.yaml'.format(i))
        targets.append(t)

    formula = 'F catch0 & F catch1 & F catch2 & F catch3 & ( ! col4 U end )'

    # Construct the full-state fsa using scheck
    # (full-state ensures proper MDP after product)
    logger.info('Formula: %s' % formula)
    fsa = lomap.Fsa()
    fsa.from_formula(formula)
    fsa.add_trap_state()

    # Classical
    with lomap.Timer('Classical (non-incremental) Method: Case 2a - '
                     'Save all friendlies'):
        lomap.classical_synthesis(vehicle_mdp, fsa, targets, set_props_2)
        pass

    # Incremental
    targets_inc = [targets[-1]] + targets[:-1]
    assumed_props = [('ped0c2','ped1c2','ped2c2','ped3c2'),
        ('ped1c2','ped2c2','ped3c2'),
        ('ped2c2','ped3c2'),
        ('ped3c2'),
        ()]

    with lomap.Timer('Incremental Method: Case 2a - Save all friendlies'):
        lomap.incremental_synthesis(vehicle_mdp, fsa, targets_inc, set_props_2,
                                    assumed_props)
        pass

def case_2b():

    # Read the vehicle model
    vehicle = lomap.Ts.load('./vehicle_1.yaml')
    # Convert the vehicle model to an MDP
    vehicle_mdp = lomap.Markov()
    vehicle_mdp.mdp_from_det_ts(vehicle)

    # Read the models of the pedestrians
    targets = []
    for i in range(1,6):
        t = lomap.Markov.load('./target_{}.yaml'.format(i))
        targets.append(t)

    formula = '( F catch0 | F catch1 | F catch2 | F catch3 ) & ( ! col4 U end )'

    # Construct the full-state fsa using scheck
    # (full-state ensures proper MDP after product)
    logger.info('Formula: %s' % formula)
    fsa = lomap.Fsa()
    fsa.from_formula(formula)
    fsa.add_trap_state()

    # Classical
    with lomap.Timer('Classical (non-incremental) Method: Case 2b - '
                     'Save at least one friendly'):
        lomap.classical_synthesis(vehicle_mdp, fsa, targets, set_props_2)
        pass

    # Incremental
    targets_inc = [targets[-1]] + targets[:-1]
    assumed_props = [('ped0c2','ped1c2','ped2c2','ped3c2'),
        ('ped1c2','ped2c2','ped3c2'),
        ('ped2c2','ped3c2'),
        ('ped3c2'),
        ()]

    with lomap.Timer('Incremental Method: Case 2b - Save at least one friendly'):
        lomap.incremental_synthesis(vehicle_mdp, fsa, targets_inc, set_props_2,
                                    assumed_props)
        pass

def case_3a():

    # Read the vehicle model
    vehicle = lomap.Ts.load('./vehicle_2.yaml')
    # Convert the vehicle model to an MDP
    vehicle_mdp = lomap.Markov()
    vehicle_mdp.mdp_from_det_ts(vehicle)

    # Read the models of the guards
    targets = []
    for i in range(1,7):
        t = lomap.Markov.load('./trap_{}.yaml'.format(i))
        targets.append(t)

    # Reach end safely
    formula = '! unsafe U end'
    # Construct the full-state fsa using scheck
    # (full-state ensures proper MDP after product)
    logger.info('Formula: %s' % formula)
    fsa = lomap.Fsa()
    fsa.from_formula(formula)
    fsa.add_trap_state()
    #fsa.visualize()

    # Classical
    with lomap.Timer('Classical (non-incremental) Method: Case 3a - Order 1'):
        lomap.classical_synthesis(vehicle_mdp, fsa, targets, set_props_3)
        pass

    # Incremental
    targets_inc = targets
    with lomap.Timer('Incremental Method: Case 3a - Order 1'):
        lomap.incremental_synthesis(vehicle_mdp, fsa, targets_inc, set_props_3)
        pass

def case_3b():

    # Read the vehicle model
    vehicle = lomap.Ts.load('./vehicle_2.yaml')
    # Convert the vehicle model to an MDP
    vehicle_mdp = lomap.Markov()
    vehicle_mdp.mdp_from_det_ts(vehicle)

    # Read the models of the guards
    targets = []
    for i in range(1,7):
        t = lomap.Markov.load('./trap_{}.yaml'.format(i))
        targets.append(t)

    # Reach end safely
    formula = '! unsafe U end'
    # Construct the full-state fsa using scheck
    # (full-state ensures proper MDP after product)
    logger.info('Formula: %s' % formula)
    fsa = lomap.Fsa()
    fsa.from_formula(formula)
    fsa.add_trap_state()
    #fsa.visualize()

    # Classical
    with lomap.Timer('Classical (non-incremental) Method: Case 3b - Order 2'):
        lomap.classical_synthesis(vehicle_mdp, fsa, targets, set_props_3)
        pass

    # Incremental
    targets_inc = [targets[2], targets[3], targets[0], targets[1], targets[5],
                   targets[4]]
    with lomap.Timer('Incremental Method: Case 3b - Order 2'):
        lomap.incremental_synthesis(vehicle_mdp, fsa, targets_inc, set_props_3)
        pass

def main():
    case_1()
    case_2a()
    case_2b()
    case_3a()
    case_3b()

def config_debug():
    # create root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # create file handler
    fh = logging.FileHandler('lomap.log', mode='w')
    fh.setLevel(logging.DEBUG)
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    #formatter = logging.Formatter('%(levelname)s %(name)s %(asctime)s - '
    #                              '%(message)s', datefmt='%m/%d/%Y %H:%M:%S')
    formatter = logging.Formatter('%(levelname)s %(name)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.debug('Logger initialization complete.')

if __name__ == '__main__':
    config_debug()
    main()
