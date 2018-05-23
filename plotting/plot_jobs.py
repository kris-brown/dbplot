# External modules
from warnings import filterwarnings
filterwarnings("ignore", message="No labelled objects")
from typing import List

import matplotlib   # type: ignore
matplotlib.use('Qt5Agg')
from matplotlib.pyplot    import subplots,Ax,show   # type: ignore

# Internal Modules
from plotting.plotter import Plot
from utils.db import ConnectInfo
from utils.misc import flatten
#############################################################################

###################################################################
# INPUT (just enter a list of plot dictionaries (from plotCommands)) #constraint,aggfunc,ycols,gbcols
#------------------------------------------------------------------

#defaultPlots = [count()]
db = ConnectInfo()
#############################################################################
#############################################################################

def axMaker(n:int)->List[Ax]:
    divs  = [i for i in range(1,n+1) if n%i==0]
    nrows = divs[len(divs)//2]
    ncols = n / nrows
    f,axs = subplots(nrows=nrows,ncols=ncols)
    f.subplots_adjust(hspace=n/4.)
    if   n == 1: return [axs]                                     # axs is singleton
    elif n <= 3: return axs                                       # axs is list
    else: return flatten(axs)                                  # axs is list of lists


#############################################################################
# Two ways of combining multiple plots. For one plot, they're identical
#############################################################################

def plot(*plots:Plot)->None:
    """
    Every plot placed into a separate subplot
    """
    #if plots == (): plots = defaultPlots
    axs = axMaker(len(plots))
    for i,p in enumerate(plots):
        p.plot(axs[i],db)
    show()

def overlay(*plots:Plot)->None:
    """
    Every plot is layed onto the previous
    Required if you want to generate multiple lines from the same data
    """
    #if plots == (): plots = defaultPlots
    f,ax = subplots(nrows=1,ncols=1)
    for p in plots: p.plot(ax,db)
    show()
