from collections import namedtuple

from web_app.utils.boolean_validators import exists

Parameter = namedtuple('Parameter', 'name type required')
Parameter.__new__.__defaults__ = (None,) * len(Parameter._fields)


class RequestParser:
    """
    This class holds the validation/parsing logic to apply to a parameters of a HTTP request
    We can specify the name of each parameter, its required type, and we can also specify constraints
    for each argument

    'add_argument' adds a new argument to be parsed at each request, if the flag 'required' is set to 'True'
     a new constraint is created

    'add_constraint' adds a constraint to be assessed at the validation phase
    """

    def __init__(self):
        self.arguments = []
        self.constraints = []

    @staticmethod
    def withParameters(*args):
        request_parser = RequestParser()
        request_parser.add_arguments(*args)
        return request_parser

    def add_argument(self, name, type, required='False'):
        self.arguments.append(Parameter(name, type, required))
        if required:
            self.constraints.append(exists(name))

    def add_arguments(self, *args):
        parameters = list(args)
        self.constraints += [exists(par.name) for par in parameters if par.required]
        self.arguments += parameters

    def add_constraint(self, callable):
        self.constraints.append(callable)
