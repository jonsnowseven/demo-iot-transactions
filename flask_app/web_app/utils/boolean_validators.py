from functools import reduce, partial


def _exists(A, **kw):
    return A in kw['args']


def exists(A):
    return partial(_exists, A)


def _xor(*args, **kw):
    return reduce(lambda x, y: (x in kw['args']) ^ (y in kw['args']), args)


def xor(*args):
    return partial(_xor, *args)


