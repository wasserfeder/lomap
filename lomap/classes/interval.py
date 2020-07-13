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

"""LOMAP interval class."""

import logging

# Logger configuration
logger = logging.getLogger(__name__)

class Interval(object):
    """
    LOMAP interval class.
    Supports addition, subtraction, negation, scalar multiplication,
    scalar division, intersection and difference.
    """

    def __init__(self, start, end, closed_start, closed_end):
        """
        Creates and initializes a new Interval object.

        Examples:
        ---------
        >>> Interval(2, 3, True, True)
        [2.000, 3.000], length: 1.000, empty: False
        >>> Interval(1, 2, False, True)
        (1.000, 2.000], length: 1.000, empty: False
        >>> Interval(1, 2, False, False)
        (1.000, 2.000), length: 1.000, empty: False
        >>> Interval(3, 4, True, False)
        [3.000, 4.000), length: 1.000, empty: False
        >>> Interval(4, 3, True, True)
        [4.000, 3.000], length: 0.000, empty: True
        """
        if not isinstance(closed_start, bool):
            raise TypeError("Invalid type for argument 'closed_start': {}."
                            .format(closed_start.__class__.__name__))
        if not isinstance(closed_end, bool):
            raise TypeError("Invalid type for argument 'closed_end': {}."
                            .format(closed_end.__class__.__name__))
        self.start = start
        self.end = end
        self.closed_start = closed_start
        self.closed_end = closed_end

    def __setattr__(self, name, value):
        """
        Makes Interval objects immutable
        """
        if getattr(self, name, None) != None:
            raise TypeError("'{}' object does not support attribute change."
                            .format(self.__class__.__name__))
        else:
            self.__dict__[name] = value

    def __delattr__(self, name):
        """
        Makes Interval objects immutable
        """
        raise TypeError("'{}' object does not support attribute change."
                        .format(self.__class__.__name__))

    def __repr__(self):
        """
        Returns a string representation of an interval object.
        """
        s = ''
        if self.closed_start:
            s += '['
        else:
            s += '('
        s += "%.3f, %.3f" % (self.start, self.end)
        if self.closed_end:
            s += ']'
        else:
            s += ')'
        s += ', length: {:.3f}, empty: {}'.format(self.length(),
                                                  not self.__nonzero__())
        return s

    def __eq__(self, other):
        """
        Returns True if two interval objects are equal.

        Examples:
        ---------
        >>> Interval(1, 2, False, False) == Interval(1, 2, False, False)
        True
        """
        try:
            return True if (self.start == other.start and
                    self.end == other.end and
                    self.closed_start == other.closed_start and
                    self.closed_end == other.closed_end) else False
        except:
            return False

    def __ne__(self, other):
        """
        Returns True if two interval objects are not equal.

        Examples:
        >>> Interval(0, 0, True, True) != Interval(0, 0, True, False)
        True
        """
        return False if self.__eq__(other) else True

    def __neg__(self):
        """
        Unary negation operator.

        Examples:
        ---------
        >>> -Interval(1, 2, True, False) == Interval(-2, -1, False, True)
        True
        >>> Interval(1, 2, True, False).length() == 1
        True
        >>> (-Interval(1, 2, True, False)).length() == 1
        True
        """
        return Interval(-self.end, -self.start, self.closed_end, self.closed_start)

    def __add__(self, other):
        """
        Binary addition operator.

        Examples:
        ---------
        >>> Interval(1, 2, True, True) + Interval(1, 2, True, True)
        [2.000, 4.000], length: 2.000, empty: False
        """
        try:
            return Interval(self.start + other.start, self.end + other.end,
                    self.closed_start and other.closed_start,
                    self.closed_end and other.closed_end)
        except:
            raise TypeError("Unsupported operand types for +: '{}' and '{}'."
                    .format(self.__class__.__name__, other.__class__.__name__))

    def __sub__(self, other):
        """
        Binary subtraction operator.

        Examples:
        ---------
        >>> Interval(3, 4, True, True) - Interval(1, 2, False, False)
        (1.000, 3.000), length: 2.000, empty: False
        """
        return self.__add__(-other)

    __or__ = __add__

    def __and__(self, other):
        """
        Returns the intersecting interval of two interval objects.
        Returns None if they are not intersecting.

        Examples:
        ---------
        >>> Interval(1, 2, True, False) & Interval(1.5, 2.5, False, True)
        (1.500, 2.000), length: 0.500, empty: False
        >>> Interval(1, 2, True, True) & Interval(3, 4, True, False) is None
        True
        """
        try:
            # Find the total span of the intervals including any space in between
            spanned_length = max(self.end, other.end) - min(self.start, other.start)
            total_length = (self.length() + other.length())
            if spanned_length > total_length:
                # Cannot have an intersection by definition
                return None
            else:
                # Starts w/ the later starting interval
                int_start = max(self.start, other.start)
                if self.start != other.start:
                    # Different start points
                    int_closed_start = self.closed_start if int_start == self.start else other.closed_start
                else:
                    # Identical start points
                    int_closed_start = self.closed_start and other.closed_start
                # Ends w/ the earlier ending interval
                int_end = min(self.end, other.end)
                if self.end != other.end:
                    # Different end points
                    int_closed_end = self.closed_end if int_end == self.end else other.closed_end
                else:
                    # Identical end points
                    int_closed_end = self.closed_end and other.closed_end
                # Intersecting interval
                int_iv = Interval(int_start, int_end, int_closed_start, int_closed_end)
                # Return None if empty interval
                if int_iv:
                    return int_iv
                else:
                    return None
        except:
            raise TypeError("Unsupported operand types for +: '{}' and '{}'."
                    .format(self.__class__.__name__, other.__class__.__name__))

    intersection = __and__

    def difference(self, other):
        """
        Returns the set difference self \ other.
        Return value is a tuple of interval objects or None.

        Examples:
        ---------
        >>> Interval(1, 2, False, True).difference(Interval(1.5, 5, False, True))
        ((1.000, 1.500], length: 0.500, empty: False,)
        >>> Interval(0, 10, True, True).difference(Interval(2, 6, False, True))
        ([0.000, 2.000], length: 2.000, empty: False, (6.000, 10.000], length: 4.000, empty: False)
        >>> Interval(3, 5, True, True).difference(Interval(3, 5, False, True))
        ([3.000, 3.000], length: 0.000, empty: False,)
        >>> Interval(3, 5, True, False).difference(Interval(9, 10, True, True))
        ([3.000, 5.000), length: 2.000, empty: False,)
        >>> Interval(1, 3, True, False).difference(Interval(1, 3, True, False)) == ()
        True
        """
        int_iv = self.__and__(other)
        if int_iv:
            # Interval fragment before intersection
            iv_before_int = Interval(self.start, int_iv.start, self.closed_start, not int_iv.closed_start)
            # Interval fragment after intersection
            iv_after_int = Interval(int_iv.end, self.end, not int_iv.closed_end, self.closed_end)
            # Filter None
            diff = [iv for iv in [iv_before_int, iv_after_int] if iv]
            if diff:
                # Some intersection
                return tuple(diff)
            else:
                # Complete intersection
                return ()
        else:
            # No intersection
            return (self,)

    def __mul__(self, other):
        """
        Scalar multiplication.

        Examples:
        ---------
        >>> 2.1 * Interval(3, 5, True, False)
        [6.300, 10.500), length: 4.200, empty: False
        """
        try:
            return Interval(self.start * other, self.end * other, self.closed_start, self.closed_end)
        except:
            raise TypeError("Unsupported operand types for *: '{}' and '{}'."
                    .format(self.__class__.__name__, other.__class__.__name__))

    __rmul__ = __mul__

    def __div__(self, other):
        """
        Scalar division.

        Examples:
        ---------
        >>> Interval(2, 4, True, True) / 2
        [1.000, 2.000], length: 1.000, empty: False
        """

        return self.__mul__(1/float(other))

    __rdiv__ = __div__

    def length(self):
        """
        Returns the length of the interval, or 0 if interval is empty.

        Examples:
        ---------
        >>> Interval(1, 4, True, False).length()
        3
        >>> Interval(3, 1, True, True).length()
        0
        """
        return max(self.end - self.start, 0)

    def __cmp__(self, other):
        try:
            if self.start < other.start:
                return -1
            elif self.start > other.start:
                return 1
            else:
                return 0
        except:
            raise TypeError("Unsupported operand types for comparison: '{}' and '{}'."
                    .format(self.__class__.__name__, other.__class__.__name__))

    def __nonzero__(self):
        """
        Returns True if the interval is non-empty.
        Note that an interval can be 0-length but still be non-empty.

        Examples:
        ---------
        >>> Interval(3, 1, True, True).__nonzero__()
        False
        >>> Interval(1, 2, True, True).__nonzero__()
        True
        >>> Interval(5, 5, True, True).length()
        0
        >>> Interval(5, 5, True, True).__nonzero__()
        True
        >>> Interval(5, 5, True, False).__nonzero__()
        False
        """

        if self.length() > 0:
            # A nonzero interval
            return True
        elif self.start == self.end and self.closed_start and self.closed_end:
            # A single element interval
            return True
        else:
            # An empty interval
            return False

    def __hash__(self):
        """
        Custom hash function for an Interval object.
        """
        return hash((self.start, self.end, self.closed_start, self.closed_end))

    def closure(self):
        """
        Returns the closure of an interval which is obtained by including its endpoints.

        Examples:
        ---------
        >>> Interval(1, 2, False, False).closure()
        [1.000, 2.000], length: 1.000, empty: False
        >>> Interval(3, 1, False, False).closure()
        [3.000, 1.000], length: 0.000, empty: True
        """
        return Interval(self.start, self.end, True, True)

    def interior(self):
        """
        Returns the interior of an interval which is obtained by excluding its endpoints.

        Examples:
        ---------
        >>> Interval(1, 2, True, True).interior()
        (1.000, 2.000), length: 1.000, empty: False
        >>> Interval(3, 1, True, True).interior()
        (3.000, 1.000), length: 0.000, empty: True
        """
        return Interval(self.start, self.end, False, False)

# Doctest
if __name__ == "__main__":
    import doctest
    doctest.testmod()
