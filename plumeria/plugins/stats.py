"""Commands to do statistics."""

import statistics

from plumeria.command import commands
from plumeria.util.command import string_filter
from plumeria.message.lists import parse_numeric_list


def format_output(n):
    return "{:f}".format(n)


@commands.create('mean', category='Statistics')
@string_filter
def mean(text):
    """
    Finds the mean of a space-separated list of numbers.

    Example::

        /mean 33 54 43 65 43 62
    """
    return format_output(statistics.mean(parse_numeric_list(text)))


@commands.create('median', category='Statistics')
@string_filter
def median(text):
    """
    Finds the median of a space-separated list of numbers.

    Example::

        /median 33 54 43 65 43 62
    """
    return format_output(statistics.median(parse_numeric_list(text)))


@commands.create('median low', category='Statistics')
@string_filter
def median_low(text):
    """
    Finds the low median of a space-separated list of numbers.

    Example::

        /median low 33 54 43 65 43 62
    """
    return format_output(statistics.median_low(parse_numeric_list(text)))


@commands.create('median high', category='Statistics')
@string_filter
def median_high(text):
    """
    Finds the high median of a space-separated list of numbers.

    Example::

        /median high 33 54 43 65 43 62
    """
    return format_output(statistics.median_high(parse_numeric_list(text)))


@commands.create('median grouped', category='Statistics')
@string_filter
def median_grouped(text):
    """
    Finds the grouped median of a space-separated list of numbers.

    Calculates the median of grouped continuous data, calculated as the 50th percentile, using interpolation.

    Example::

        /median grouped 33 54 43 65 43 62
    """
    return format_output(statistics.median_grouped(parse_numeric_list(text)))


@commands.create('mode', category='Statistics')
@string_filter
def mode(text):
    """
    Finds the mode of a space-separated list of numbers.

    Example::

        /mode 33 54 43 65 43 62
    """
    return format_output(statistics.mode(parse_numeric_list(text)))


@commands.create('pstdev', category='Statistics')
@string_filter
def pstdev(text):
    """
    Finds the population standard deviation of a space-separated list of numbers.

    Example::

        /pstdev 33 54 43 65 43 62
    """
    return format_output(statistics.pstdev(parse_numeric_list(text)))


@commands.create('pvariance', category='Statistics')
@string_filter
def pvariance(text):
    """
    Finds the population variance of a space-separated list of numbers.

    Example::

        /pvariance 33 54 43 65 43 62
    """
    return format_output(statistics.pvariance(parse_numeric_list(text)))


@commands.create('stdev', category='Statistics')
@string_filter
def stdev(text):
    """
    Finds the standard deviation of a space-separated list of numbers.

    Example::

        /stdev 33 54 43 65 43 62
    """
    return format_output(statistics.stdev(parse_numeric_list(text)))


@commands.create('variance', category='Statistics')
@string_filter
def variance(text):
    """
    Finds the variance of a space-separated list of numbers.

    Example::

        /variance 33 54 43 65 43 62
    """
    return format_output(statistics.variance(parse_numeric_list(text)))


def setup():
    commands.add(mean)
    commands.add(median)
    commands.add(median_low)
    commands.add(median_high)
    commands.add(median_grouped)
    commands.add(mode)
    commands.add(pstdev)
    commands.add(pvariance)
    commands.add(stdev)
    commands.add(variance)
