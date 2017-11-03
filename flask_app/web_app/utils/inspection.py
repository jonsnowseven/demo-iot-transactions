import inspect
import re


def class_init_fields(_class):
    """
    Inspect the variable names of the constructor method and return a tuple
    'self' comes included

    e.g:
    Class A
        def __init__(self, var1, var):
            pass

    inspect_class_init_fields(A) => ('self', 'var1', 'var2')
    """
    signature = inspect.signature(_class)
    arguments_names = [arg for arg in signature.parameters]
    return arguments_names


def inspect_class_name(_class):
    """
    Inspect the class name and if it is in the form '<entity>Repository<client>', returns the <entity> and the <client>.

    e.g:
    Class ARepositoryPSQL
        pass

    inspect.class_name(A) => "A", "PSQL"
    """
    match = re.match(r"^(?P<entity>\w+)Repository(?P<client>[A-Z]+)$", _class.__name__)
    if match:
        return match.group("entity"), match.group("client")
