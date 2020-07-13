#! /usr/bin/env python

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

from __future__ import division
import itertools as it
import lomap
import logging

# Logger configuration
logger = logging.getLogger(__name__)

#
# Quadrotor Class
#

class Quadrotor(object):
	def __init__(self, env, x, y, sensing_range):
		# Environment object to use in sensing
		self.env = env
		# Set position (center of quadrotor)
		self.x, self.y = x, y
		# Set sensing size (one side of the sensing square)
		assert sensing_range % 2 == 1, "sensing_range must be an odd value, '%d' is not odd!" % sensing_range
		self.sensing_range = sensing_range
		# Define the motion primitives/other commands
		self.cmds = {'n': 'self.y += 1', 'e': 'self.x += 1', 's': 'self.y -= 1', 'w': 'self.x -= 1', 'h':''}
		# Perform first sensing
		self.sense()



	def get_sensing_cell_global_coords(self, cell):
		# Returns the global x,y coordinates of the sensing cell cx, cy
		# Bottom left cell is the 0,0 cell
		cx, cy = cell
		assert cx >= 0 and cy >=0
		return (cx-(self.sensing_range // 2)+self.x, cy-(self.sensing_range // 2)+self.y) # integer division



	def sense(self):
		# Dict of sets to hold local sensing information (names of regions and local info)
		self.sensed = [[{'local_reqs':set([]), 'global_reqs':set([])} for y in range(0, self.sensing_range)] for x in range(0, self.sensing_range)]
		for cx, cy in it.product(range(0, self.sensing_range), repeat=2):
			# cx, cy are the local cell coords and x,y are the global coords
			x, y = self.get_sensing_cell_global_coords((cx, cy))
			# Get local requests (if active)
			if (x,y) in self.env.local_reqs and self.env.local_reqs[(x,y)]['on']:
				self.sensed[cx][cy]['local_reqs'] = self.env.local_reqs[(x,y)]['reqs']
			# Get global requests
			if (x,y) in self.env.global_reqs:
				self.sensed[cx][cy]['global_reqs'] = self.env.global_reqs[(x,y)]['reqs']



	def move_quad(self, cmd):
		# Execute the command
		exec(self.cmds[cmd])
		# Sense at new position
		self.sense()
