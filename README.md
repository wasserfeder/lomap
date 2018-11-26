This is a fork of Alphan Ulusoys' LOMAP library, and is maintained by
Cristian-Ioan Vasile (cristian.ioan.vasile@gmail.com).

The license is still GNU GPL v2, but might change to v3 in the future.
You can find the lincense text in a file called 'LICENSE'.
Please see the copyright and warranty information of the third party
software below.

----------------------------------------------------------------------

Installation Instructions

Linux (Ubuntu)
1) Clone into the lomap repository
    Navigate to desired location
    Run the following line in shell:
      git clone https://github.com/wasserfeder/lomap.git

2) Install Spot using Debian Packages (https://spot.lrde.epita.fr/install.html)
  Run the following lines in shell:
    wget -q -O - https://www.lrde.epita.fr/repo/debian.gpg | apt-key add -
    echo 'deb http://www.lrde.epita.fr/repo/debian/ stable/' >> /etc/apt/sources.list
    apt-get update
    apt-get install spot libspot-dev spot-doc python3-spot # Or a subset of those

3) Install necessary dependencies:
  Run the following lines in shell:
    apt install python-pip
    pip2 install matplotlib
    pip2 install numpy
    apt-get install python-tk
    pip2 install networkx==1.11
    pip2 install pyyamlCollecting pyyaml
    pip2 install pp

    (Note: ensure that Python 2.7 is installed)

  4) Set $PYTHONPATH to include the location of the lomap library:
    Run the following line in shell:
      export PYTHONPATH="${PYTHONPATH}:/path/to/lomap"

  5) Test if the setup worked properly:
    Navigate to /lomap/lomap/tests
    Run any of the Python test files
      Ex. python test_automata.py

  Common Issues:
    1) ImportError: No module named lomap.classes
      Problem: The lomap library is not in the path variable
      Possible Solution: Manually add lomap to your Python directory

    2)  File "/usr/bin/pip", line 9, in <module>
        from pip import main
        ImportError: cannot import name main
          Problem: Wrong version of pip (are using Python 3 pip)
          Solution: Run commands with pip2

    3) AttributeError: 'Graph' object has no attribute 'nodes_iter' (or other graph issues)
        Problem: Wrong version of networkx installed
        Solution: Uninstall networkx and install networkx1.11 (see above)


----------------------------------------------------------------------

UROP 2018-19 Todo List:
- Allow usage of nc 2.x
- Allow usage of Python 3.x
- Remove Old Ts/Markov file format system, use yaml
- Revise installation instructions
- Revise developer instructions, add more tests 
- Create more testing examples with instructions (docs)
- Improve visualization
- Implement dfsa and dfsca minimization
- Add support for DFSCAs
- Integrate logic minimization
- Add Buchi/Rabin games
- Sync with twtl, reactive-lfl, lurmod, purp, golfe-firne
- Integrate GDTL and predicate system
- Upgrade GDTL/TWTL grammars to ANTLRv4
- Add more examples
- Add RH/MPC framework
- General clean-up of code
- Test for functions and continuous integration system
- BDDs for guards

----------------------------------------------------------------------

LTL Optimal Multi-Agent Planner (LOMAP)
Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.

A copy of the GNU General Public License is included in this
distribution, in a file called 'COPYING'.

----------------------------------------------------------------------

LTL Optimal Multi-Agent Planner (LOMAP) is a python package for
automatic planning of optimal paths for multi-agent systems.
See the directory 'examples' (either in the source archive or in
the installation directory) for examples.

----------------------------------------------------------------------

LOMAP uses two third party programs: LTL2BA and scheck. You can
find their sources in this distribution, in a directory called
'third_party_sources'. For your convenience, binaries of these
programs are already included in this distribution, in a folder
called 'binaries'. LOMAP also includes some code that is adapted
and/or taken from NetworkX Python package v1.6, available at
http://networkx.github.io. See below for copyright notices and
licenses of LTL2BA, scheck, and NetworkX.

LTL2BA
------
LTL2BA - Version 1.0 - October 2001
Written by Denis Oddoux, LIAFA, France
Copyright (C) 2001  Denis Oddoux

LTL2BA - Version 1.1 - August 2007
Modified by Paul Gastin, LSV, France
Copyright (C) 2007  Paul Gastin
Available at http://www.lsv.ens-cachan.fr/~gastin/ltl2ba

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version. GNU GPL is included in this
distribution, in a file called 'LICENSE'

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

The LTL2BA software was written by Denis Oddoux and modified by Paul
Gastin.  It is based on the translation algorithm presented at CAV '01:
    P.Gastin and D.Oddoux
    "Fast LTL to Büchi Automata Translation"
    in 13th International Conference on Computer Aided Verification, CAV 2001,
    G. Berry, H. Comon, A. Finkel (Eds.)
    Paris, France, July 18-22, 2001,
    Proceedings - LNCS 2102, pp. 53-65

Send bug-reports and/or questions to Paul Gastin
http://www.lsv.ens-cachan.fr/~gastin

Part of the code included is issued from the SPIN software Version 3.4.1
The SPIN software is written by Gerard J. Holzmann, originally as part
of ``Design and Validation of Protocols,'' ISBN 0-13-539925-4,
1991, Prentice Hall, Englewood Cliffs, NJ, 07632
Here are the files that contain some code from Spin v3.4.1 :   

    cache.c  (originally tl_cache.c)
    lex.c    (           tl_lex.c  )
    ltl2ba.h (       tl.h      )
    main.c   (       tl_main.c )
    mem.c    (       tl_mem.c  )
    parse.c  (       tl_parse.c)
    rewrt.c  (       tl_rewrt.c)
    trans.c  (       tl_trans.c)

scheck
------
scheck - Version 1.2
Copyright (C) 2003 Timo Latvala (timo.latvala@hut.fi)
Modified by Amit Bhatia, Computer Science Department, Rice University
Copyright (C) 2011 Amit Bhatia

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

scheck is a tool for translating safety LTL formulae to finite automata.
The algorithm used in the tool was presented in the paper:

Timo Latvala. Efficient Model Checking of Safety Properties. In:
  T. Ball and S.K. Rajamani (eds.), Model Checking Software. 10th
  International SPIN Workshop. Volume 2648 of LNCS, pp. 74-88, Springer, 2003.

This version of scheck incorporates some changes into scheck 1.2 that
is available for download from Timo Latvala's website. The changes were
made so that scheck could be compiled on newer gcc compilers. The code
compiles fine with gcc 4.4.5. However, please note that I am not the
original developer or the current maintainer of this code. For further
details, please refer to README.html.

Amit Bhatia, Computer Science Department, Rice University,
April 7, 2011.

NetworkX
--------
Copyright (C) 2004-2012, NetworkX Developers
Aric Hagberg <hagberg@lanl.gov>
Dan Schult <dschult@colgate.edu>
Pieter Swart <swart@lanl.gov>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above
    copyright notice, this list of conditions and the following
    disclaimer in the documentation and/or other materials provided
    with the distribution.

  * Neither the name of the NetworkX Developers nor the names of its
    contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
