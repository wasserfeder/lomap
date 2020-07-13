# Copyright (C) 2017, Cristian-Ioan Vasile (cvasile@mit.edu)
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

from lomap.classes import Buchi, Fsa, Rabin

def test_buchi():
    specs = ['F a && G ! b']

    for spec in specs:
        aut = Buchi()
        aut.from_formula(spec)
        print(aut)

def test_fsa():
    specs = ['F a && F !b']

    for spec in specs:
        aut = Fsa()
        aut.from_formula(spec)
        print(aut)

def test_rabin():
    specs = ['F a && G ! b']

    for spec in specs:
        aut = Rabin()
        aut.from_formula(spec)
        print(aut)

if __name__ == '__main__':
    test_buchi()
    test_fsa()
    test_rabin()
