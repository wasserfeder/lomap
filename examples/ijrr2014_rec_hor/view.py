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
from six.moves import zip as izip
import matplotlib as mpl
#mpl.use("agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import Affine2D
from matplotlib import animation

class View(object):
	def __init__(self, env, quad):
		"""Creates a figure window and initializes view parameters
		for the environment and the quadrotor.
		"""
		# Create the figure window
		self.fig = plt.figure(figsize=(4*3.13,3*3.13))
		self.ax = self.fig.gca()
		self.ax.xaxis.set_ticklabels([])
		self.ax.yaxis.set_ticklabels([])
		self.ax.xaxis.set_ticks(list(range(-100,100)))
		self.ax.yaxis.set_ticks(list(range(-100,100)))
		self.margin = quad.sensing_range // 2 # integer division
		# Scaled
		plt.axis('scaled')
		plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
		# Save pointer to env and quad
		self.env = env
		self.quad = quad
		# Defines the quadrotor
		self.define_quadrotor()
		# Defines polygons for locally sensed requests
		self.define_local()
		# Draw the a priori known regions in the environment (called once only here)
		self.draw_regions()
		# Path line object
		self.path_line = None
		self.arrow = None
		# Draw the quadrotor
		self.draw_quad()



	def define_quadrotor(self):
		# Create the square cells for local sensing range of the quadrotor
		# In quad_cells[i][j], 'cell' gives the object, 'text' gives the text on the cell
		cell_cmd = "plt.Rectangle((0, 0), 1, 1, edgecolor = 'black', fill=False, linewidth = 0.5)"
		self.quad_cells = [[dict() for y in range(0, self.quad.sensing_range)] for x in range(0, self.quad.sensing_range)]
		for x,y in it.product(range(0, self.quad.sensing_range), repeat=2):
			self.quad_cells[x][y] = {'cell': eval(cell_cmd), 'text': self.ax.text(0.5,0.5,'X',fontsize=10,ha='center',va='center',weight='bold')}
			self.ax.add_artist(self.quad_cells[x][y]['cell'])
		# Create circles for drawing the quad (0.20 radius)
		blade_cmd = 'plt.Circle((0,0),0.20,fill=False,linewidth=1)'
		self.quad_blades = [None]*4
		for i in range(0,4):
			self.quad_blades[i] = eval(blade_cmd)
			self.ax.add_artist(self.quad_blades[i])



	def get_vertices_of_cell(self, cell):
		x, y = cell
		lower_left = (x-0.5, y-0.5)
		lower_right = (x+0.5, y-0.5)
		upper_left = (x-0.5, y+0.5)
		upper_right = (x+0.5, y+0.5)
		return (lower_left, upper_left, upper_right, lower_right, lower_left)



	def draw_regions(self):
		"""Draws the regions
		"""
		global_reqs = self.env.global_reqs
		# For setting axis ranges properly
		min_x, max_x, min_y, max_y = (self.quad.x, self.quad.x, self.quad.y, self.quad.y)
		for cell in global_reqs:
			color = global_reqs[cell]['color']
			vertices = self.get_vertices_of_cell(cell)
			# x and y points of each vertex for matplotlib
			x, y = list(zip(*vertices))
			self.ax.fill(x,y,color,edgecolor=color)
			# For proper limits
			min_x = min(min_x, min(x))
			min_y = min(min_y, min(y))
			max_x = max(max_x, max(x))
			max_y = max(max_y, max(y))
		# Set appropriate limits
		plt.axis((min_x-self.margin, max_x+self.margin, min_y-self.margin, max_y+self.margin))
		self.ax.tight=True



	def define_local(self):
		"""Defines polygons for locally sensed requests
		"""
		local = self.env.local_reqs
		self.local_polygons = dict()
		for cell in local:
			color = local[cell]['color']
			vertices = self.get_vertices_of_cell(cell)
			self.local_polygons[cell] = plt.Polygon(vertices, facecolor=color, edgecolor=color, zorder=0)



	def draw_local(self):
		"""Draws locally sensed requests
		"""
		for name in self.local_polygons:
			artist = self.local_polygons[name]
			if artist not in self.ax.get_children():
				# Not child of axis
				if self.env.local_reqs[name]['on']:
					# Must be added
					self.ax.add_artist(artist)
			elif not self.env.local_reqs[name]['on']:
				# Child of axis and must be removed
				self.local_polygons[name].remove()



	def draw_quad(self):
		# Creates the local polygons
		self.draw_local()
		# Translations for quad blades (NW, NE, SE, SW)
		txty = ((-0.20, 0.20),(0.20, 0.20),(0.20,-0.20),(-0.20,-0.20))
		# Transform circles as needed (translation and optional rotation)
		for blade,(tx,ty) in izip(self.quad_blades,txty):
			trans = Affine2D().translate(tx,ty).translate(self.quad.x, self.quad.y) + self.ax.transData
			blade.set_transform(trans)
		# Translations and labels for quad sensing cells
		for x, y in it.product(range(0, self.quad.sensing_range), repeat = 2):
			# Center coords of cell x,y
			cell_x, cell_y = self.quad.get_sensing_cell_global_coords((x,y))
			cell_trans = Affine2D().translate(-0.5,-0.5).translate(cell_x, cell_y) + self.ax.transData
			self.quad_cells[x][y]['cell'].set_transform(cell_trans)
			self.quad_cells[x][y]['text'].set_transform(cell_trans)
			props = self.quad.sensed[x][y]['local_reqs'] | self.quad.sensed[x][y]['global_reqs']
			new_text = ','.join(props)
			self.quad_cells[x][y]['text'].set_text(new_text)
		# Remove path
		if self.path_line in self.ax.get_children():
			self.path_line.remove()
			self.arrow.remove()



	def draw_path(self, vertices):
		xs, ys = list(zip(*vertices))
		dx = (xs[-1]-xs[-2])/1.5
		dy = (ys[-1]-ys[-2])/1.5
		self.path_line = self.ax.plot(xs, ys, 'r-', lw=2)[0]
		self.arrow = self.ax.arrow(xs[-2], ys[-2], dx, dy, head_width=0.5, head_length=0.5, fc='r', ec='w')
