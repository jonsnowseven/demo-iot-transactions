import time
import re

from functools import wraps
from collections import namedtuple

from flask import current_app, abort, request


def parse_args(parser):
    """
    Validates if request has the needed arguments and those arguments are correct
    If all ok, the various arguments are parsed and injected into the function

    If the validation fails, returns:
    status code 422 - Unprocessable Entity
    https://stackoverflow.com/questions/3050518/what-http-status-response-code-should-i-use-if-the-request-is-missing-a-required
    """

    def decorator(f):

        @wraps(f)
        def wrapper(*args, **kw):

            request_args = request.args

            request_is_valid = _check_boolean_conditions(parser.constraints, args=request_args)

            if not request_is_valid:
                abort(422)

            for arg in parser.arguments:

                try:
                    value = _parse_arg(arg, request_args)
                    if value:
                        kw[arg.name] = value
                except (ValueError, TypeError, AttributeError) as ex:
                    abort(422)

            return f(*args, **kw)

        return wrapper

    return decorator


def _parse_arg(arg, request_args):
    """
    Parse a single 'request argument'
    Arguments of type list are also accommodated

    Possible exceptions thrown should be handled by the calling function
    """
    if arg.name in request_args:
        return _cast_value(arg.type, request_args[arg.name])
    else:
        return None


def _cast_value(type, value):
    """Check if the incoming value can be casted to the intended type"""
    if isinstance(type, list):
        type_constructor = type[0]
        return [type_constructor(v) for v in value]
    else:
        return type(value)


def _check_boolean_conditions(conditions, args):
    return all(check(args=args) for check in conditions)



