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

from .classes import Model, Ts, Markov
from .classes import Automaton, Buchi, Fsa, Rabin
from .classes import Timer
from .algorithms.product import *
from .algorithms.optimal_run import optimal_run
from .algorithms.multi_agent_optimal_run import multi_agent_optimal_run
from .algorithms.robust_multi_agent_optimal_run import robust_multi_agent_optimal_run
from .algorithms.value_iteration import *
from .algorithms.inc_syn import *
from .algorithms.srfs import *
from .classes.automata import spot_output_encoding, ltl2dstar_output_encoding

__version__ = (0, 1, 2)
