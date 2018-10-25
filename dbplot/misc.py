# External Modules
from typing  import TypeVar,List,Callable as C,Optional as O,Any,Dict,Union as U
from inspect import getfullargspec,isfunction,getsourcefile,getmembers
from importlib.util import spec_from_file_location,module_from_spec

Fn = U[str,C]

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

def const(x:Any)->Any: return lambda : x
def joiner(*args:Any)->str: return '_'.join(map(str,args))

def mapfst(xs:List[tuple])->List[Any]:  return [x[0] for x in xs]
def mapsnd(xs:List[tuple])->List[Any]:  return [x[1] for x in xs]
def avg(x:list)->float:                 return sum(map(float,x))/len(x)

def path_to_funcs(pth : str) -> Dict[str,C]:
    """
    Assumes we have files with one sole function in them
    """
    spec = spec_from_file_location('random',pth)
    if spec.loader is None:
        raise ValueError(pth)
    else:
        mod  = module_from_spec(spec)
        spec.loader.exec_module(mod)

    def check(o : C) -> bool:
        return isfunction(o) and getsourcefile(o)==pth

    funcs = [o for o in getmembers(mod) if check(o[1])]
    return dict(funcs)

################################################################################
def mkFunc(x:O[Fn])->C:
    """
    Take something (either a function or a string) and eval it if it's a string
    """
    functype = type(identity) # the type of function
    if x is None:
        return identity
    elif isinstance(x,functype):
        return x
    elif isinstance(x,str):
        f = eval(x)
        assert isinstance(f,functype)
        return f
    else:
        raise ValueError

class FnArgs(object):
    """
    A function equipped with a list of argnames which can be used to grab values
    from a namespace (dictionary).

    By default:
        - the function will be the identity function (Expecting one argument)
        - the args will be the argument names defined in the function.
    """
    def __init__(self, func : U[str,C], args : U[str,List[str]]) -> None:
        if isinstance(func,str): func = mkFunc(func)
        if isinstance(args,str): args = args.split()
        self.func = func
        self.args = args

    def apply(self,d : dict)->Any:
        args = [d[arg] for arg in self.args]
        return self.func(*args)

################################################################################
class Group(object):
    """
    Intermediate datatype useful for plotting.
    Just a labeled container with a representative.
    """
    def __init__(self,  id : int, label : str, rep : Any, elems : List) -> None:
        self.id = id; self.label = label; self.rep = rep; self.elems = elems

    def __str__(self)->str:
        return self.label+' (%d elements)'%len(self.elems)

    def __len__(self)->int:
        return len(self.elems)

    def apply(self,f:C)->None:
        """modify elements with a function"""
        self.elems = f(self.elems)

    def map(self,f:C)->None:
        """modify elements individually by mapping a function"""
        self.elems = [f(e) for e in self.elems]

    def add_elem(self,x:Any)->None:
        self.elems.append(x)
