from functools import reduce
from math import frexp
import psutil
import time
import os

byte_names = 'KMGTPEZY'


def bytes_for_humans(byte_count: int):
    # Get power of two directly from floating point exponent bits (mantissa)
    power_of_2 = frexp(byte_count)[1] - 1
    binary_multiple = power_of_2 // 10
    # If too big, represent in largest form
    if binary_multiple >= len(byte_names):
        binary_multiple = len(byte_names) - 1
    # Gets the magnitude of the most significant multiple of 1024
    impercise_magnitude = byte_count // (1 << (binary_multiple * 10))
    # If less than 1024B, just return number of bytes
    if binary_multiple == 0:
        return str(impercise_magnitude) + ' B'
    return str(impercise_magnitude) + ' ' \
        + byte_names[binary_multiple - 1] + 'B'


def lower_bound(sequence, bound=0):
    """
    Maps the given sequence such that the data points
    are greater than or equal to the bound.
    """
    return map(
        lambda point:
            point if point > bound
            else bound,
        sequence
    )


def power_range(start, stop=None, step=2):
    """
    Generates a sequence starting at start and multiplying
    consecutive numbers by step until stop is reached.
    """
    if stop is None:
        stop = start
        start = 1
    assert start > 0 and start < stop and step > 1
    while start < stop:
        yield start
        start *= step


def time_it(func):
    """
    Run a function and return the time it took to execute in seconds.
    """
    def timed_func(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time
    timed_func.__name__ = func.__name__
    return timed_func


def invert_array_of_dicts(array, keys):
    # TODO: streamline this
    result = {}
    for item in array:
        for key in keys:
            if key not in result:
                result[key] = []
            result[key].append(item[key])
    return result


def plot_dict(name_to_data_mapping, *args, **kwargs):
    """Creates a plot of the given data in any order."""
    return plot_tuple_array(name_to_data_mapping.items(), *args, **kwargs)


def scale_axes(axes, xscale: float=1, yscale: float=1):
    pos = axes.get_position()
    axes.set_position([pos.x0, pos.y0, pos.width * xscale,
                      pos.height * yscale])


def plot_tuple_array(axes, name_to_data_mapping, x_label, y_label,
                     custom_x_label=None, custom_y_label=None, y_mapping=None):
    """Creates a plot of the given data in the order it is given."""

    def plot_inner_arr(name, inverted_array):
        data = invert_array_of_dicts(inverted_array, inverted_array[0].keys())
        y_data = data[y_label]
        if y_mapping is not None:
            y_data = list(y_mapping(y_data))
        return axes.plot(data[x_label], y_data, label=name)[0]

    plots = list(map(
        lambda result_tuple: plot_inner_arr(*result_tuple),
        sorted(name_to_data_mapping.items())
    ))
    axes.set_xlabel(custom_x_label if custom_x_label is not None else x_label)
    axes.set_ylabel(custom_y_label if custom_y_label is not None else y_label)
    return plots


def memory_percent():
    current_process = psutil.Process(os.getpid())
    return current_process.memory_percent() + sum(
        map(
            psutil.Process.memory_percent,
            current_process.children(recursive=True)
        )
    )
