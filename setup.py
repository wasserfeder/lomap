# Copyright (C) 2012-2015, Alphan Ulusoy (alphan@bu.edu)
#               2015-2017, Cristian-Ioan Vasile (cvasile@mit.edu)
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

from setuptools import setup

import lomap

version = '.'.join(map(str, lomap.__version__))

setup(
    name='lomap',
    version=version,
    description='LTL Optimal Multi-Agent Planner (LOMAP)',
    long_description = '',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    url='https://github.com/wasserfeder/lomap',
    author='Alphan Ulusoy, Cristian-Ioan Vasile',
    author_email='cvasile@mit.edu',
    license='GNU GPLv2',
    packages=['lomap', 'lomap.algorithms', 'lomap.classes'],
    package_dir={'lomap': 'lomap'},
    install_requires=['networkx >= 1.11', 'pp >= 1.6.2', 'matplotlib >= 1.3.1',
                      'setuptools >= 1.1.6'],
    zip_safe=False
)
