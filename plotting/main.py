# External Modules
import matplotlib   # type: ignore
matplotlib.use('Qt5Agg')
from matplotlib.pyplot    import subplots,show   # type: ignore
from os import environ
from json import load

# Internal Modules
from dbplot.plotting.plots import *
from dbplot.utils.db      import ConnectInfo

"""
Plot a specific plot from dbplot.plotting.plots
"""
################################################################################
with open(environ['DB_JSON'],'r') as f:
    db = ConnectInfo(**load(f))

def main()->None:
    print('Running Plots.py')
    f,ax = subplots(nrows=1,ncols=1)
    bulkmod.plot(ax,db)
    show()

if __name__=='__main__':
    main()
