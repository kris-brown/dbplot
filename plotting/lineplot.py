from typing import Callable,Any,Tuple,List,Optional,Dict,TypeVar,TYPE_CHECKING
from inspect import getargspec

from abc import abstractmethod

import matplotlib   # type: ignore
matplotlib.use('Qt5Agg')
from matplotlib.pyplot    import subplots,Axes,show   # type: ignore
from operator import itemgetter
from collections import OrderedDict
from dbplot.utils.db import ConnectInfo,select_dict
from dbplot.plotting.label import label2Line
###############################################################################
A = TypeVar('A')
B = TypeVar('B')
def identity(x:A)->A: return x
def mapfst(xs:List[tuple])->List[Any]:  return [x[0] for x in xs]
def mapsnd(xs:List[tuple])->List[Any]:  return [x[1] for x in xs]

#############################################################################
class FnArgs(object):
    """
    A function equipped with a list of argnames which can be used to grab values
    from a namespace (dictionary).
    By default
        the function will be the identity function (Expecting one argument)
        the args will be the literal argument names defined in the function.
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
        args = {arg: d.get(arg) for arg in self.args}
        return self.func(*args.values())
###############################################################################
class Group(object):
    """
    Intermediate datatype useful for plotting. Just a labeled container.
    """
    def __init__(self
                ,id         : int
                ,label      : str
                ,identifier : Any
                ,elements   : List
                ) -> None:
        self.id         = id
        self.label      = label
        self.identifier = identifier
        self.elements   = elements
    def __str__(self)->str:
        return self.label+'\n'.join(map(str,self.elements))
    def __len__(self)->int:
        return len(self.elements)
    def apply(self,f:Callable)->None:
        """modify elements with a function"""
        self.elements = f(self.elements)
    def add_elem(self,x:Any)->None:
        self.elements.append(x)
#############################################################################
class Plot(object):
    def __init__(self
                ,query   : str
                ,xFunc   : FnArgs
                ,lFunc   : Optional[FnArgs]
                ,gFunc   : Optional[FnArgs]                 = None
                ,glFunc  : Optional[FnArgs]                 = None
                ,title   : str                              = ''
                ,xLab    : str                              = ''
                ) -> None:
        if glFunc is None: glFunc = gFunc
        self.query   = query
        self.xFunc   = xFunc
        self.lFunc   = lFunc
        self.gFunc   = lFunc
        self.glFunc  = glFunc
        self.title   = title
        self.xLab    = xLab

    def plot(self
            ,ax    : Axes
            ,conn  : ConnectInfo
            ,binds : list        = []
            ) -> None:
        """
        Only 'exposed' function of a Plot, calls other methods in order
        """
        results      = select_dict(conn,self.query,binds)
        groupdata    = [self._groupdata(d)    for d in results]
        processed    = [self._process_dict(d) for d in results]
        grouped      = self._make_groups(groupdata,processed)
        for g in grouped:
            self._draw(ax,g)

        self._set_labels(ax)
        self._set_legend(ax)

    def _groupdata(self,d:dict)->Tuple[Any,str]:
        return  ((1  if self.gFunc  is None else self.gFunc.apply(d)
                ,''  if self.glFunc is None else self.glFunc.apply(d)))


    def _set_labels(self,ax:Axes)->None:
        """
        Default label setting behavior is just x axis and title (can be super'd)
        """
        ax.set_xlabel(self.xLab)
        ax.set_title(self.title)

    def _make_groups(self
                    ,groupdata : List[Tuple[A,str]]
                    ,inputs    : List[B]
                    ) -> List[Group]:
        """
        Take a list of processed DB outputs and use the group information to
        partition it according to the group identifier (4th tuple element)

        The groups will become different lines on the final plot
        """
        groups = [] # type: List[Group]
        counter = 0
        for (x,(g,gl)) in zip(inputs,groupdata):
            group = [grup for grup in groups if grup.identifier==g]
            if group:
                group[0].add_elem(x)
            else:
                groups.append(Group(counter,gl,g,[x]))
                counter+=1
        return groups

    @abstractmethod
    def _draw(self,ax:Axes,g:Group)->None:
        """
        Fill out the plot in some way - different implementation for each subclass
        """
        return

    @abstractmethod
    def _process_dict(self,d:Dict)->Any:
        """
        Take a DB output dict and make a pair: <SOMETHING>,(group ID, group label)
        """
        return

    @staticmethod
    def _set_legend(ax:Axes)->None:
        """ignore this...please"""
        try:
            handles, labels = ax.get_legend_handles_labels()
            hl = sorted(zip(handles, labels),key=itemgetter(1))
            handles2, labels2 = zip(*hl)
            ax.legend(handles2, labels2) #sort
            by_label = OrderedDict(zip(ax.get_legend_handles_labels())) # type: ignore
            legend = ax.legend(by_label.values(), by_label.keys()) # remove dups
            legend.draggable()
        except (AttributeError,ValueError) as e: print(e)
################################################################################
class LinePlot(Plot):
    def __init__(self
                ,query   : str
                ,xFunc   : FnArgs
                ,yFunc   : FnArgs
                ,lFunc   : Optional[FnArgs]
                ,gFunc   : Optional[FnArgs]                 = None
                ,glFunc  : Optional[FnArgs]                 = None
                #,aggFunc : Optional[FnArgs]                 = None
                ,post    : Optional[Callable[[list],list]]  = None
                ,title   : str                              = ''
                ,xLab    : str                              = ''
                ,yLab    : str                              = ''
                ,count   : bool                             = True
                ,scatter : bool                             = False
                ) -> None:
        super().__init__(query,xFunc,lFunc,gFunc,glFunc,title,xLab)

        self.yFunc   = yFunc
        self.yLab    = yLab
        self.post    = post
        self.count   = count
        self.scatter = scatter
        #self.aggFunc = aggFunc

    def _set_labels(self,ax:Axes)->None:
        super()._set_labels(ax)
        ax.set_ylabel(self.yLab)

    def _draw(self
            ,ax    : Axes
            ,g     : Group
            ) -> None:
        """Make a query, process results, then draw the lines"""
        # do aggregations, postprocessing to modify 'g', eventually
        self._add_line(ax,g)


    def _process_dict(self,d:dict)->Tuple[float,float,str]:
        """
        Take a raw dictionary output from DB and make an output tuple:
            - x,y (floats)
            - l (label)
            - g (group identifier)
            - gl (group label)
        """
        return ((self.xFunc.apply(d)
               ,self.yFunc.apply(d)
               ,'' if self.lFunc  is None else self.lFunc.apply(d)))

    def _add_line(self,ax:Axes,g:Group)->None:
        """
        Draw a line from a Group with (X,Y,LABEL) tuples as elements
        """
        leg,     xyl   = g.label,g.elements
        handles, labels = ax.get_legend_handles_labels()

        if len(xyl)>0:
            ls,c,m = label2Line(leg)                                                  # get line style based on legend name
            linestyle = ' ' if self.scatter else ls

            ax.plot(mapfst(xyl),mapsnd(xyl),linestyle=linestyle
                     ,color=c,marker=m,label=leg) # add line
            for (x,y,l) in xyl:
                ax.text(x,y,l,size=9                              # add data labels
                    ,horizontalalignment='center',verticalalignment='bottom')
                # if self.count: ax.text(x,y,"(%d)"%n,size=6,horizontalalignment='center',verticalalignment='top')
################################################################################
class BarPlot(Plot):
    def __init__(self
                ,query   : str
                ,xFunc   : FnArgs
                ,lFunc   : Optional[FnArgs]
                ,gFunc   : Optional[FnArgs]                 = None
                ,glFunc  : Optional[FnArgs]                 = None
                ,title   : str                              = ''
                ,xLab    : str                              = ''
                ,spFunc  : Optional[FnArgs]                 = None
                ,slFunc  : Optional[FnArgs]                 = None
                ) -> None:
        super().__init__(query,xFunc,lFunc,gFunc,glFunc,title,xLab)
        self.spFunc = spFunc
        self.slFunc = slFunc

    def _process_dict(self,d:Dict)->Tuple[float,str]:
        return ((self.xFunc.apply(d)
               ,'' if self.lFunc is None else self.lFunc.apply(d)))

    def _draw(self,ax:Axes,g:Group)->None:
        color = label2Line(g.label)[1]
        for val,lab in g.elements:
            ax.bar(g.id,val,width=1,color=color,label=lab,align='center')


class HistPlot(Plot):
    def __init__(self
                ,query   : str
                ,xFunc   : FnArgs
                ,lFunc   : Optional[FnArgs] = None
                ,gFunc   : Optional[FnArgs] = None
                ,glFunc  : Optional[FnArgs] = None
                ,title   : str              = ''
                ,xLab    : str              = ''
                ,bins    : int              = 10
                ,norm    : bool             = False
                ) -> None:
        super().__init__(query,xFunc,lFunc,gFunc,glFunc,title,xLab)
        self.bins = bins
        self.norm = norm

    def _process_dict(self,d:Dict)->Tuple[float,str]:
        return ((self.xFunc.apply(d)
               ,'' if self.lFunc is None else self.lFunc.apply(d)))
    def _draw(self,ax:Axes,g:Group)->None:
        color = label2Line(g.label)[1]
        ax.hist(mapfst(g.elements),histtype='bar',label=g.label,bins=self.bins
               ,color= color, density = self.norm)

################################################################################
################################################################################
################################################################################
lp = LinePlot(query = "SELECT job_id,timestamp,user from job"
             ,xFunc = FnArgs(args = ['job_id'])
             ,yFunc = FnArgs(args = ['timestamp'])
             ,lFunc = FnArgs(func = lambda x: x*2,args = ['user'])
             ,gFunc = FnArgs(args = ['user'])
             ,title = 'LinePlot'
             ,xLab = 'Job_id'
             ,yLab = 'Timestamp'
             )
bp = BarPlot(query = 'SELECT COUNT(1) as count,user from job GROUP BY user'
            ,xFunc = FnArgs(args=['count'])
            ,lFunc = FnArgs(args=['user'])
            ,gFunc = FnArgs(args=['user'])
            ,title = 'Barplot Example'
            ,xLab  = 'User')

hp = HistPlot(query = 'SELECT pw FROM relax_job JOIN calc USING (calc_id)'
             ,xFunc = FnArgs(int,args=['pw'])
             ,title = 'TestHistPlot'
             ,xLab = 'PW cutoff, eV')
################################################################################
rdb = ConnectInfo(host   = 'g-suncat-suncatdata.sudb.stanford.edu'
                    ,port   = 3306
                    ,user   = 'gsuncatsuncatd'
                    ,passwd = 'BCe8HzyXCA-ekD!!'
                    ,db     = 'g_suncat_suncatdata')
if __name__=='__main__':
    db = ConnectInfo()
    f,ax = subplots(nrows=1,ncols=1)
    f.subplots_adjust(hspace=1/4.)
    hp.plot(ax,rdb)
    show()
