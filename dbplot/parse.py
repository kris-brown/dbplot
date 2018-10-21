# External Modules
from typing         import Any
from argparse       import ArgumentParser,Action
from distutils.util import strtobool

##########################################################################################

class StoreDictKeyPair(Action):
    """
    Usage:
     >>> python main.py --key_pairs 1=2 a=bbb c=4
    """
    def __init__(self, option_strings:str, dest:str, nargs:Any=None, **kwargs:Any)->None:
         self._nargs = nargs
         super().__init__(option_strings, dest, nargs=nargs, **kwargs)

    def __call__(self, parser:Any, namespace:Any, values:Any, option_string:Any=None)->None:
         my_dict = {}
         for kv in values:
             k,v = kv.split("=")
             my_dict[k] = v
         setattr(namespace, self.dest, my_dict)
##########################################################################################
# Command line parsing
parser = ArgumentParser(description  = 'Plot relations from a mysql DB'
                       ,allow_abbrev = True)

parser.add_argument('--db',
                    default = '',
                    type    = str,
                    help    = 'Path to JSON file with connection info')

parser.add_argument('--pltpth',
                    default = '',
                    type    = str,
                    help    = 'Path to JSON file specifying the plot to be made')

parser.add_argument('--binds',
                    default = '',
                    type    = str,
                    help    = 'Literal python code for binds if plot has a parameterized query')

parser.add_argument('--query',
                    default = '',
                    type    = str,
                    help    = 'How to gather information from DB prior to plotting')

parser.add_argument('--type',
                    default = '',
                    type    = str.lower,
                    help    = 'Either Line, Bar, or Hist')

parser.add_argument('--funcs',
                    default = [],
                    type    = str.split,
                    help    = 'Space-separated list of paths to python files '\
                              ' binding functions to names')

parser.add_argument("--args",
                    action  = StoreDictKeyPair,
                    nargs   = "+",
                    metavar = "KEY=VAL")
