from types import ModuleType
from typing import List
import matplotlib   # type: ignore
matplotlib.use('Qt5Agg')
from matplotlib.pyplot    import subplots,show,figure   # type: ignore

import dbplot.plotting.plots as plots
from dbplot.utils.db      import ConnectInfo
from dbplot.plotting.plot import Plot
################################################################################
rdb = ConnectInfo(host   = 'g-suncat-suncatdata.sudb.stanford.edu'
                 ,port   = 3306
                 ,user   = 'gsuncatsuncatd'
                 ,passwd = 'BCe8HzyXCA-ekD!!'
                 ,db     = 'g_suncat_suncatdata')

db = ConnectInfo()

def dict_from_module(module:ModuleType)->List[Plot]:
    ps = []
    for setting in dir(module):
        val = getattr(module, setting)
        if isinstance(val,Plot):
            ps.append(val)
    return ps



def main()->None:
    print('Running Plots.py')
    f,ax = subplots(nrows=1,ncols=1)
    ps   = dict_from_module(plots)

    global curr_pos # type: int
    curr_pos = 0

    def key_event(e):
        global curr_pos # type: int

        if e.key == "right":
            curr_pos = curr_pos + 1
        elif e.key == "left":
            curr_pos = curr_pos - 1
        else:
            return None
        curr_pos = curr_pos % len(ps)

        ax.cla()
        ps[curr_pos].plot(ax,rdb)
        f.canvas.draw()


    #fig = figure()
    f.canvas.mpl_connect('key_press_event', key_event)
    ax = f.add_subplot(111)
    ps[curr_pos].plot(ax,rdb) # initialize plot
    show()

if __name__=='__main__':
    main()
