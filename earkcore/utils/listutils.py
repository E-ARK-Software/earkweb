from itertools import izip


def pairwise(iterable):
    """
    Helper function to iterate pairwise.
    :param iterable: values list
    :return: tuple
    """
    a = iter(iterable)
    return izip(a, a)
