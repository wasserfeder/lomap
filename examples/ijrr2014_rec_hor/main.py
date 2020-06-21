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

# Case studies presented in:
#
# A. Ulusoy, C. Belta, "Receding Horizon Temporal Logic Control in
# Dynamic Environments," The International Journal of Robotics Research,
# vol. 33, no. 12, pp. 1593-1607, 2014.

import itertools as it
import matplotlib as mpl
#mpl.use("agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import Affine2D
from matplotlib import animation
import lomap
import logging

from quadrotor import Quadrotor
from environment import Environment
from view import View
from planner import Planner

from sys import exit
import pprint as pp

def config_debug():
	global logger
	# create root logger
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	# create file handler
	fh = logging.FileHandler('lomap.log', mode='w')
	fh.setLevel(logging.DEBUG)
	# create console handler
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	# create formatter and add it to the handlers
	#formatter = logging.Formatter('%(levelname)s %(name)s %(asctime)s - %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
	formatter = logging.Formatter('%(levelname)s %(name)s - %(message)s')
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)
	# add the handlers to the logger
	logger.addHandler(fh)
	logger.addHandler(ch)
	logger.debug('Logger initialization complete.')

def toggle_local_reqs(i):
	global case
	if case == 'case1':
		if i == 0:
			env.local_reqs[(9,2)]['on'] = False
			env.local_reqs[(9,4)]['on'] = False
		elif i == 25:
			env.local_reqs[(9,2)]['on'] = True
			env.local_reqs[(9,4)]['on'] = True
	elif case == 'case2':
		if i == 0:
			for cell in env.local_reqs:
				env.local_reqs[cell]['on'] = False
		if i == 50:
			env.local_reqs[(8,8)]['on'] = True
			env.local_reqs[(6,7)]['on'] = True
		if i == 90:
			env.local_reqs[(8,8)]['on'] = True
			env.local_reqs[(6,7)]['on'] = True
			env.local_reqs[(9,6)]['on'] = True
			env.local_reqs[(3,5)]['on'] = True
	elif case == 'case3':
		if i == 0:
			for cell in env.local_reqs:
				env.local_reqs[cell]['on'] = False
		if i == 48:
			for cell in env.local_reqs:
				env.local_reqs[cell]['on'] = True
	else:
		assert False

# Animation function
def animate(i):
	global quad, view, planner, cmd, anim_state
	logger.debug('Vehicle location - Frame %d: %s' % (i, (quad.x, quad.y)))
	toggle_local_reqs(i)
	quad.sense()
	if not i%2:
		# Draw the quad
		view.draw_quad()
	else:
		# Plan and the draw the path for the next time step
		with lomap.Timer('Online Computation - Frame %d:' % i):
			cmd, path = planner.next_command()
		view.draw_path(path)
		quad.move_quad(cmd)
#
# Main code
#

# Configure logging output
config_debug()

# Set to save video of the animation
video_name = None #'case2.mp4'

# Case studies
case_studies = {
		'case1': ('[]<>photo && [](photo -> X upload) && [](upload -> X photo)', '(assist|extinguish)*', {'assist':0, 'extinguish':1}, 3, 1, 5),
		'case2': ('[]<>photo1 && [](photo1 -> X photo2) && [](photo2 -> X upload) && [](upload -> X photo1)', '(pickup.dropoff)*', {'pickup':0, 'dropoff':0}, 3, 3, 7),
		'case3': ('[]<>photo1 && [](photo1 -> X photo2) && [](photo2 -> X upload) && [](upload -> X photo1)', '(pickup1.dropoff1|pickup2.dropoff2)*', {'pickup1':0, 'pickup2':1, 'dropoff1':0, 'dropoff2':1}, 3, 3, 7),
		}

# Select the case-study to run
case = 'case2'

# Set the mission specification
global_spec, local_spec, prio, init_x, init_y, sensing_range = case_studies[case]

# Create the environment
env = Environment(case)

# Create the quadrotor
quad = Quadrotor(env, init_x, init_y, sensing_range)

# Create the view
view = View(env, quad)

with lomap.Timer('Offline Computation'):
	planner = Planner(env, quad, global_spec, local_spec, prio)

# Animation
anim = animation.FuncAnimation(view.fig, animate, frames=list(range(0,200)), interval=250, repeat=False)
if video_name:
	anim.save(video_name)
	exit(0)

plt.show()
