Version 0.1.2 notes and API changes

This page reflects API changes from LOMAP 0.1.1 to NetworkX 0.1.2.
Note: The original code written by Alphan Ulusoy has version number 0.1.1.

API changes
- Added options for directed and multi-graph models. The default
values are true for backward compatibility.
- Added __repr__ function to model classes for quick debugging.
- Added clone functions to model classes.
- Added support for matplotlib in visualization function, detault is still
using pygraphviz for backward compatibilty.
- Added class for Rabin automata.
- Added support for {\em spot} and {\em ltl2dstar}, and removed support for
{\em ltl2ba} and {\em scheck2}. Removed binary distribution of {\em ltl2ba} and
{\em scheck}.
- Added version number (__version__) to package.
- Changed methods {\em buchi_from_formula} and {\em fsa_from_cosafe_formula}
of Buchi and Fsa classes to {\em from_formula}, respectively.
- Changed methods {\em next_states_of_buchi} and {\em next_states_of_fsa} of
Buchi and Fsa classes to {\em next_states}, respectively.

Models
- In Buchi class, simplified methods {\em bitmaps_from_props} and
{\em next_states_of_buchi}.

Tests
- Added basic tests for LTL to Buchi, Fsa, and Rabin translation.

Bug fixes
- Fixed problem with parsing negated proposition in guards. The solution may
still be error prone.
- Added missing parsing of empty set guard '(0)'.
- Deleted unused imports in some modules.

Miscellaneous
- Switched from tabs to spaces for indentation.
- General code clean-up.
