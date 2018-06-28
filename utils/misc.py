from typing  import TypeVar,List,Callable,Optional,Any
from inspect import getargspec
################################################################################
A = TypeVar('A')
B = TypeVar('B')
###############
def identity(x:A)->A: return x

def flatten(lol : List[List[A]]) -> List[A]:
    """
    Convert list of lists to a single list via concatenation
    """
    return [item for sublist in lol for item in sublist]


################################################################################
class FnArgs(object):
    """
    A function equipped with a list of argnames which can be used to grab values
    from a namespace (dictionary).

    By default:
        - the function will be the identity function (Expecting one argument)
        - the args will be the argument names defined in the function.
    """
    def __init__(self
                ,func : Callable             = identity
                ,args : Optional[List[str]]  = None
                ) -> None:
        if args is None:
            args = getargspec(func)[0] # discard *args and **kwargs?
        self.func = func
        self.args = args

    def apply(self,d : dict)->Any:
        args = [d.get(arg) for arg in self.args]
        return self.func(*args)

def Get(x : str) -> FnArgs:
    return FnArgs(args=[x])
################################################################################
