import matplotlib   # type: ignore
matplotlib.use('Qt5Agg')
from matplotlib.pyplot    import subplots,show   # type: ignore

from dbplot.plotting.plots import *
from dbplot.utils.db      import ConnectInfo
################################################################################
rdb = ConnectInfo(host   = 'g-suncat-suncatdata.sudb.stanford.edu'
                 ,port   = 3306
                 ,user   = 'gsuncatsuncatd'
                 ,passwd = 'BCe8HzyXCA-ekD!!'
                 ,db     = 'g_suncat_suncatdata')

db = ConnectInfo()

def main()->None:
    print('Running Plots.py')
    f,ax = subplots(nrows=1,ncols=1)
    errLattice.plot(ax,rdb)
    show()

if __name__=='__main__':
    main()
