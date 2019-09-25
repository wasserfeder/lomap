LTL Optimal Multi-Agent Planner (LOMAP)
=======================================

LTL Optimal Multi-Agent Planner (LOMAP) is a python package for automatic
planning of optimal paths for multi-agent systems.
See the directory 'examples' (either in the source archive or in the
installation directory) for examples.

Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)

Copyright (C) 2013-2019, Cristian-Ioan Vasile (cvasile@mit.edu,
                                               cristian.ioan.vasile@gmail.com)

## Installation Instructions

Linux (Ubuntu)
1. Clone the _lomap_ repository
  * Navigate to desired location
  * Run the following line in shell:

  ```bash
  git clone https://github.com/wasserfeder/lomap.git
  ```

2. Install _Spot_ using Debian Packages (https://spot.lrde.epita.fr/install.html)
  * Run the following lines in shell:

    ```
    wget -q -O - https://www.lrde.epita.fr/repo/debian.gpg | apt-key add -
    echo 'deb http://www.lrde.epita.fr/repo/debian/ stable/' >> /etc/apt/sources.list
    apt-get update
    apt-get install spot libspot-dev spot-doc python3-spot # Or a subset of those
    ```

3. Install necessary dependencies:
  * Run the following lines in shell:

    ```bash
    apt install python-pip
    pip2 install future
    pip2 install matplotlib
    pip2 install numpy
    apt-get install python-tk
    pip2 install networkx==1.11
    pip2 install pyyaml
    pip2 install pp
    apt install cmake
    ```

  * Note: Ensure that Python 2.7 is installed.
  * Note: If Python3, install matplotlib==2.2.3 in order to maintain compatibility with network 1.11

4. Download and unpack _ltl2dstar_
  * Download from: https://www.ltl2dstar.de/
  * Unpack _ltl2dstar_
  * Navigate to the _ltl2dstar_ folder
  * Run the following lines in shell:

      ```bash
      mkdir build
      cd build/
      cmake -DCMAKE_BUILD_TYPE=Release ../src
      make
      ```

  * Optionally add the binary to folder in `PATH`
    * For example:

      ```bash
      mkdir ~/bin
      cp ltl2dstar ~/bin/
      echo 'export PATH="$PATH:$HOME/bin"' >> ~/.bashrc
      ```

5. Set `$PYTHONPATH` to include the location of the _lomap_ library:
  * Run the following line in shell:

      ```bash
      export PYTHONPATH="${PYTHONPATH}:/path/to/lomap"
      ```

  * Optionally make this setting persistent:

      ```bash
      echo 'export PYTHONPATH="${PYTHONPATH}:/path/to/lomap"' >> ~/.bashrc
      ```

6. Test if the setup worked properly:
  * Navigate to `/lomap/lomap/tests`
  * Run any of the Python test files
    * Ex. `python test_automata.py`

### Common Issues:
1. ```python
      ImportError: No module named lomap.classes
   ```
  * Problem: The _lomap_ library is not in the path variable
  * Possible Solution: Manually add _lomap_ to your Python directory

2. ```python
      File "/usr/bin/pip", line 9, in <module>
      from pip import main
      ImportError: cannot import name main
   ```
  * Problem: Wrong version of _pip_ (are using Python 3 _pip_)
  * Solution: Run commands with _pip2_

3. ```python
   AttributeError: 'Graph' object has no attribute 'nodes_iter' (or other graph issues)
   ```
  * Problem: Wrong version of _networkx_ installed
  * Solution: Uninstall _networkx_ and install _networkx1.11_ (see above)


## Todo List:

- Port to _networkx_ 2.x
- Add support for Python 3.x
- Remove old Ts/Markov file format system, use _yaml_
- Revise developer instructions, add more tests
- Create more testing examples with instructions (docs)
- Improve visualization
- Add support for DFSCAs
- Implement dfsa and dfsca minimization
- Integrate logic minimization
- Add Buchi/Rabin games
- Sync with twtl, reactive-ltl, lvrmod, pvrp, gdtl-firm
- Integrate GDTL and predicate system
- Add more examples
- Add RH/MPC framework
- General clean-up of code
- Test for functions and continuous integration system
- BDDs for guards

## Copyright and Warranty Information

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
distribution, in a file called 'license.txt'.
