# -*- coding: utf-8 -*-

import numpy


def uniform_geometry_pdf(p, x):
    a = -p*numpy.log(p)/(1-p)
    for i in range(1, x):
        a -= p*numpy.power(1-p, i-1)/i
        yield a


def uniform_geometry(n):
    p = 1/n
    b = -p*numpy.log(p)/(1-p)
    for pdf in uniform_geometry_pdf(p, n):
        b += pdf
    return b


def uniform_geometry_cdf(n, b_max):
    p = 1/n
    b = -p * numpy.log(p) / (1 - p)
    if b > b_max: return 1
    index = 1
    for pdf in uniform_geometry_pdf(p, n):
        b += pdf
        index += 1
        if b > b_max: return index


def sample_uniform_geometry(group):
    if len(group) == 1:
        return group[0]
    reversed_group = group[::-1]
    n = len(reversed_group)
    b = uniform_geometry(n)
    cdf = numpy.random.uniform(0, b, 1)[0]
    return reversed_group[uniform_geometry_cdf(n, cdf)-1]