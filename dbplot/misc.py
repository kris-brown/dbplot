# External Modules
from typing  import TypeVar,List,Callable as C,Optional as O,Any,Dict,Union as U, TextIO
from inspect import getfullargspec,isfunction,getsourcefile,getmembers,isbuiltin
from importlib.util import spec_from_file_location,module_from_spec
import json
'''
Miscellaneous helper classes
'''
################################################################################
Fn = U[str,C]
A = TypeVar('A')
################################################################################

# ######################
# # Json decoder for multiline items
# # --------------------

def load(f : TextIO)->dict:
    json_contents = f.read()
    json_contents = json_contents.replace('\r',' ').replace('\n',' ')
    return json.loads(json_contents)

################################################################################
def identity(x : A) -> A: return x

def flatten(lol : List[List[A]]) -> List[A]:
    """
    Convert list of lists to a single list via concatenation
    """
    return [item for sublist in lol for item in sublist]

def const(x:Any) -> Any:      return lambda : x
def joiner(*args:Any) -> str: return '_'.join(map(str,args))

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
        return isfunction(o) or isbuiltin(o)

    funcs = [o for o in getmembers(mod) if check(o[1])]
    return dict(funcs)

################################################################################
def mkFunc(x : O[Fn], funcs : Dict[str,C]) -> C:
    """
    Take something (either a function or a string) and eval it if it's a string
    """
    functype = (type(len),type(identity)) # the type of functions or builtins
    if x is None:
        return identity
    elif isinstance(x,functype):
        return x
    elif isinstance(x,str):
        locals().update(funcs)
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
    def __init__(self, func : U[str,C], args : U[str,List[str]], funcs : Dict[str,C]) -> None:
        if isinstance(func,str): func = mkFunc(func,funcs)
        if isinstance(args,str): args = args.split()
        self.func = func
        self.args = args

    def apply(self,d : dict)->Any:
        args = [d[arg] for arg in self.args]
        return self.func(*args)

    def __call__(self, d : dict) -> Any:
        return self.apply(d)

################################################################################
class Group(object):
    """
    Intermediate datatype useful for plotting.
    Just a labeled container with a representative element.
    """
    def __init__(self,  id : int, label : str, rep : Any, elems : List) -> None:
        self.id = id; self.label = label; self.rep = rep; self.elems = elems

    def __str__(self)->str:
        s = 's' if len(self.elems)!=1 else '' # plurals . . .
        return self.label+' (%d element%s)'%(len(self.elems),s)

    def __len__(self)->int:
        return len(self.elems)

    def __getitem__(self,key:str)->list:
        '''Assume each elem is a dictionary with str keys'''
        return [e[key] for e in self.elems]

    def apply(self,f:C)->'Group':
        """modify elements with a function"""
        self.elems = f(self.elems)
        return self

    def map(self,f:C)->'Group':
        """modify elements individually by mapping a function"""
        self.elems = [f(e) for e in self.elems]
        return self

    def add_elem(self,x:Any)->None:
        self.elems.append(x)

    def sort(self,key:C=str)->'Group':
        self.elems = sorted(self.elems,key=key)
        return self
