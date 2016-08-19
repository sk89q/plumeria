import statistics

import re

from plumeria.command import commands, CommandError
from plumeria.util.command import string_filter


def get_numbers(s):
    numbers = re.split(" +", s.strip())
    try:
        return list(map(lambda x: float(x), numbers))
    except ValueError as e:
        raise CommandError("All the entries must be numbers")


def format_output(n):
    return "{:f}".format(n)


@commands.register('mean', category='Statistics')
@string_filter
def mean(text):
    """
    Finds the mean of a space-separated list of numbers.
    """
    return format_output(statistics.mean(get_numbers(text)))


@commands.register('median', category='Statistics')
@string_filter
def median(text):
    """
    Finds the median of a space-separated list of numbers.
    """
    return format_output(statistics.median(get_numbers(text)))


@commands.register('medianlow', category='Statistics')
@string_filter
def median_low(text):
    """
    Finds the low median of a space-separated list of numbers.
    """
    return format_output(statistics.median_low(get_numbers(text)))


@commands.register('medianhigh', category='Statistics')
@string_filter
def median_high(text):
    """
    Finds the high median of a space-separated list of numbers.
    """
    return format_output(statistics.median_high(get_numbers(text)))


@commands.register('mediagrouped', category='Statistics')
@string_filter
def median_grouped(text):
    """
    Finds the grouped median of a space-separated list of numbers.

    Calculates the median of grouped continuous data, calculated as the 50th percentile, using interpolation.
    """
    return format_output(statistics.median_grouped(get_numbers(text)))


@commands.register('mode', category='Statistics')
@string_filter
def mode(text):
    """
    Finds the mode of a space-separated list of numbers.
    """
    return format_output(statistics.mode(get_numbers(text)))


@commands.register('pstdev', category='Statistics')
@string_filter
def pstdev(text):
    """
    Finds the population standard deviation of a space-separated list of numbers.
    """
    return format_output(statistics.pstdev(get_numbers(text)))


@commands.register('pvariance', category='Statistics')
@string_filter
def pvariance(text):
    """
    Finds the population variance of a space-separated list of numbers.
    """
    return format_output(statistics.pvariance(get_numbers(text)))


@commands.register('stdev', category='Statistics')
@string_filter
def stdev(text):
    """
    Finds the standard deviation of a space-separated list of numbers.
    """
    return format_output(statistics.stdev(get_numbers(text)))


@commands.register('variance', category='Statistics')
@string_filter
def variance(text):
    """
    Finds the variance of a space-separated list of numbers.
    """
    return format_output(statistics.variance(get_numbers(text)))
