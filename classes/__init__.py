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

import sys
import pkg_resources as pr
import os
import subprocess

# Initialize binaries
if sys.platform[0:5] == 'linux':
	assert(pr.resource_exists('lomap','binaries/linux/ltl2ba'))
	assert(pr.resource_exists('lomap','binaries/linux/scheck2'))
	ltl2ba_binary = pr.resource_filename('lomap','binaries/linux/ltl2ba')
	scheck_binary = pr.resource_filename('lomap','binaries/linux/scheck2')
elif sys.platform == 'darwin':
	assert(pr.resource_exists('lomap','binaries/mac/ltl2ba'))
	assert(pr.resource_exists('lomap','binaries/mac/scheck2'))
	ltl2ba_binary = pr.resource_filename('lomap','binaries/mac/ltl2ba')
	scheck_binary = pr.resource_filename('lomap','binaries/mac/scheck2')
else:
	print>>sys.stderr, sys.platform, 'platform not supported yet!'
	print>>sys.stderr, 'Binaries will not work!'
	ltl2ba_binary = None
	scheck_binary = None
	

# Check and fix chmod as needed
if ltl2ba_binary != None and scheck_binary != None:
	if not os.access(ltl2ba_binary, os.X_OK) or not os.access(scheck_binary, os.X_OK):
		try:
			print "You'll be prompted for root password to make some third party binaries executable."
			print "Binaries that will be made executable are:"
			print ltl2ba_binary
			print scheck_binary
			subprocess.Popen(['sudo', 'chmod', '+x', ltl2ba_binary, scheck_binary], stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate()
		except Exception as ex:
			raise Exception(__name__, "Problem setting permissions of binaries: '%s'" % ex)
