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

#
# Environment class
#

class Environment(object):
	def __init__(self, case):
		"""Defines regions in the environment.
		"""
		# Global and local requests
		self.global_reqs = dict()
		self.local_reqs = dict()

		if case == 'case1':
			# Static requests (labels are cell coordinates)
			self.global_reqs[(3,1)] = {'reqs':{'photo'}, 'color':'green'}
			self.global_reqs[(5,10)] = {'reqs':{'upload'}, 'color':'blue'}
			self.global_reqs[(9,7)] = {'reqs':{'upload'}, 'color':'blue'}
			# Local requests (labels are cell coordinates)
			self.local_reqs = dict()
			self.local_reqs[(1,7)]  = {'reqs':{'unsafe'}, 'on':True, 'color':'yellow'}
			self.local_reqs[(2,7)]  = {'reqs':{'unsafe'}, 'on':True, 'color':'yellow'}
			self.local_reqs[(3,7)]  = {'reqs':{'unsafe'}, 'on':True, 'color':'yellow'}
			self.local_reqs[(4,7)]  = {'reqs':{'unsafe'}, 'on':True, 'color':'yellow'}
			self.local_reqs[(5,7)]  = {'reqs':{'unsafe'}, 'on':True, 'color':'yellow'}
			self.local_reqs[(6,7)]  = {'reqs':{'unsafe'}, 'on':True, 'color':'yellow'}
			self.local_reqs[(7,7)]  = {'reqs':{'unsafe'}, 'on':True, 'color':'yellow'}
			self.local_reqs[(9,4)] = {'reqs':{'extinguish'}, 'on':True, 'color':'red'}
			self.local_reqs[(9,2)] = {'reqs':{'assist'}, 'on':True, 'color':'cyan'}
		elif case == 'case2':
			# Static requests (labels are cell coordinates)
			self.global_reqs[(3,3)] = {'reqs':{'photo1'}, 'color':'LightGreen'}
			self.global_reqs[(19,6)] = {'reqs':{'photo2'}, 'color':'Green'}
			self.global_reqs[(11,10)] = {'reqs':{'upload'}, 'color':'blue'}
			# Local requests (labels are cell coordinates)
			self.local_reqs = dict()
			self.local_reqs[(8,8)] = {'reqs':{'pickup'}, 'on':True, 'color':'red'}
			self.local_reqs[(6,7)] = {'reqs':{'dropoff'}, 'on':True, 'color':'cyan'}
			self.local_reqs[(9,6)] = {'reqs':{'pickup'}, 'on':True, 'color':'red'}
			self.local_reqs[(3,5)] = {'reqs':{'dropoff'}, 'on':True, 'color':'cyan'}
		elif case == 'case3':
			# Static requests (labels are cell coordinates)
			self.global_reqs[(3,3)] = {'reqs':{'photo1'}, 'color':'LightGreen'}
			self.global_reqs[(19,6)] = {'reqs':{'photo2'}, 'color':'DarkGreen'}
			self.global_reqs[(11,10)] = {'reqs':{'upload'}, 'color':'blue'}
			# Local requests (labels are cell coordinates)
			self.local_reqs = dict()
			self.local_reqs[(14,8)] = {'reqs':{'pickup1'}, 'on':True, 'color':'Red'}
			self.local_reqs[(12,7)] = {'reqs':{'dropoff1'}, 'on':True, 'color':'Cyan'}
			self.local_reqs[(13,4)] = {'reqs':{'pickup2'}, 'on':True, 'color':'DarkRed'}
			self.local_reqs[(16,6)] = {'reqs':{'dropoff2'}, 'on':True, 'color':'DarkCyan'}
		else:
			assert False, 'Case %s is not implemented' % case
