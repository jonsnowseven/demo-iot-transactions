import glob
from itertools import tee, filterfalse, chain


def read_all(pattern):
    return glob.glob(pattern)


def partition(pred, iterable):
    """
    Use a predicate to partition entries into false entries and true entries'
    e.g.:
    partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    """
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


def flatten(listOfLists):
    """
    Flatten one level of nesting
    Do nothing if the list is not nested, i.e. their elements are not iterable
    e.g.: [[A,A], [B,C]] => [A,A,B,C]
    """
    try:
        return chain.from_iterable(listOfLists)
    except TypeError:
        return listOfLists


def decreasing_variations(l):
    """
    Break the iterable 'l' into len(l) different incrementally smaller partitions
    ['The', 'Brown', 'Fox'] ==> ['The', 'Brown', 'Fox'], ['Brown', 'Fox'], ['Fox']
    """
    return (l[i:] for i in range(len(l)))


def first(iterable, condition=lambda x: True):
    """
    Returns the first item in the `iterable` that
    satisfies the `condition`.

    If the condition is not given, returns the first item of
    the iterable.

    Raises `StopIteration` if no item satysfing the condition is found.

    first( (1,2,3), condition=lambda x: x % 2 == 0)
    2
    first(range(3, 100))
    3
    first( () )
    Traceback (most recent call last):
    ...
    StopIteration
    """

    return next(x for x in iterable if condition(x))


def index_of_first(iterable, condition=lambda x: True):
    """
    Returns the first item in the `iterable` that
    satisfies the `condition`.

    If the condition is not given, returns the first item of
    the iterable.

    Raises `StopIteration` if no item satysfing the condition is found.

    first( (1,2,3), condition=lambda x: x % 2 == 0)
    2
    first(range(3, 100))
    3
    first( () )
    Traceback (most recent call last):
    ...
    StopIteration
    """

    return next(i for i, x in enumerate(iterable) if condition(x))


def without(d, key):
    """
    Return a copy of dictionary 'd' without one key
    """
    new_d = d.copy()
    new_d.pop(key)
    return new_d
