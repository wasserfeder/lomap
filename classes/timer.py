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

import time
import logging

__author__ = 'Alphan Ulusoy (alphan@bu.edu)'

# Logger configuration
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

class Timer:
	"""
	LOMAP timer class.

	Examples:
	---------
	>>> with lomap.Timer():
	>>>	 time.sleep(0.1)
	Operation took 100 ms.

	>>> with lomap.Timer('Taking product'):
	>>>	 time.sleep(0.1)
	Taking product took 100 ms.
	"""
	def __enter__(self):
		logger.info('%s started.' % self.op_name)
		self.start = time.time()
	def __init__(self, op_name=None):
		if op_name is not None:
			self.op_name = op_name
		else:
			self.op_name = "Operation"
	def __exit__(self, *args): 
		logger.info('%s took %0.3f ms.' % (self.op_name, (time.time() - self.start)*1000))
