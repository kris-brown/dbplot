from typing import Callable,Any,Tuple,List,Optional,Dict,TypeVar,TYPE_CHECKING
if TYPE_CHECKING:
    from matplotlib.pyplot    import Axes # type: ignore

from abc import abstractmethod

from operator import itemgetter
from collections import OrderedDict

from dbplot.utils.db        import ConnectInfo,select_dict
from dbplot.utils.misc      import FnArgs,A,B
from dbplot.plotting.style  import mkStyle
###############################################################################
def mapfst(xs:List[tuple])->List[Any]:  return [x[0] for x in xs]
def mapsnd(xs:List[tuple])->List[Any]:  return [x[1] for x in xs]
def avg(x:list)->float:                 return sum(map(float,x))/len(x)

#############################################################################
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
                ,lFunc   : Optional[FnArgs]                 = None
                ,gFunc   : Optional[FnArgs]                 = None
                ,glFunc  : Optional[FnArgs]                 = None
                ,title   : str                              = ''
                ,xLab    : str                              = ''
                ,yLab    : str                              = ''
                ) -> None:
        if glFunc is None: glFunc = gFunc
        self.query   = query
        self.xFunc   = xFunc
        self.lFunc   = lFunc
        self.gFunc   = gFunc
        self.glFunc  = glFunc
        self.title   = title
        self.xLab    = xLab
        self.yLab    = yLab

    def plot(self
            ,ax    : 'Axes'
            ,conn  : ConnectInfo
            ,binds : list        = []
            ) -> None:
        """
        Only 'exposed' function of a Plot, calls other methods in order
        """
        results      = select_dict(conn,self.query,binds)
        groupdata    = [self._groupdata(d)    for d in results]
        processed    = [self._process_dict(d) for d in results]
        self.groups  = self._make_groups(processed,groupdata)
        for g in self.groups:
            self._draw(ax,g)

        self._set_labels(ax)
        self._set_legend(ax)

    def _groupdata(self,d:dict)->Tuple[Any,str]:
        return  ((1  if self.gFunc  is None else self.gFunc.apply(d)
                ,''  if self.glFunc is None else self.glFunc.apply(d)))


    def _set_labels(self,ax:'Axes')->None:
        """
        Default label setting behavior is just x axis and title (can be super'd)
        """
        ax.set_xlabel(self.xLab)
        ax.set_ylabel(self.yLab)
        ax.set_title(self.title)

    @staticmethod
    def _make_groups(inputs    : List[B]
                    ,groupdata : List[Tuple[A,str]]
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
    def _draw(self,ax:'Axes',g:Group)->None:
        """
        Fill out the plot in some way - different implementation for each subclass
        """
        pass

    @abstractmethod
    def _process_dict(self,d:Dict)->Any:
        """
        Take a DB output dict and make a pair: <SOMETHING>,(group ID, group label)
        """
        return

    @staticmethod
    def _set_legend(ax:'Axes')->None:
        """ignore this...please"""
        handles, labels = ax.get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())

        # try:
        #     handles, labels = ax.get_legend_handles_labels()
        #     hl = sorted(zip(handles, labels),key=itemgetter(1))
        #     handles2, labels2 = zip(*hl)
        #     ax.legend(handles2, labels2) #sort
        #     by_label = OrderedDict(zip(ax.get_legend_handles_labels())) # type: ignore
        #     legend = ax.legend(by_label.values(), by_label.keys()) # remove dups
        #     legend.draggable()
        # except (AttributeError,ValueError) as e: print(e)
################################################################################
class LinePlot(Plot):
    def __init__(self
                ,query   : str
                ,xFunc   : FnArgs
                ,yFunc   : FnArgs
                ,lFunc   : Optional[FnArgs]                 = None
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
        super().__init__(query=query,xFunc=xFunc,lFunc=lFunc,gFunc=gFunc
                        ,glFunc=glFunc,title=title,xLab=xLab,yLab=yLab)

        self.yFunc   = yFunc
        self.post    = post
        self.count   = count
        self.scatter = scatter
        #self.aggFunc = aggFunc

    def _draw(self
            ,ax    : 'Axes'
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

    def _add_line(self,ax:'Axes',g:Group)->None:
        """
        Draw a line from a Group with (X,Y,LABEL) tuples as elements
        """
        leg,     xyl    = g.label,g.elements
        handles, labels = ax.get_legend_handles_labels()

        if len(xyl)>0:
            sty  = mkStyle(leg)                                                  # get line style based on legend name
            line = ' ' if self.scatter else sty.line

            ax.plot(mapfst(xyl),mapsnd(xyl),linestyle=line
                     ,color=sty.color,marker=sty.marker,label=leg) # add line
            for (x,y,l) in xyl:
                ax.text(x,y,l,size=9                              # add data labels
                    ,horizontalalignment='center',verticalalignment='bottom')
                # if self.count: ax.text(x,y,"(%d)"%n,size=6,horizontalalignment='center',verticalalignment='top')
################################################################################
class BarPlot(Plot):
    """

    """
    def __init__(self
                ,query   : str
                ,xFunc   : FnArgs
                ,lFunc   : Optional[FnArgs]                 = None
                ,gFunc   : Optional[FnArgs]                 = None
                ,glFunc  : Optional[FnArgs]                 = None
                ,title   : str                              = ''
                ,xLab    : str                              = ''
                ,yLab    : str                              = ''
                ,spFunc  : Optional[FnArgs]                 = None
                ,slFunc  : Optional[FnArgs]                 = None
                ,aggFunc : Callable[[List[float]],float]    = avg # how to get a real number from a set of reals
                ) -> None:

        super().__init__(query  = query, xFunc=xFunc,lFunc=lFunc,gFunc=gFunc
                        ,glFunc = glFunc,title=title,xLab=xLab,yLab=yLab)
        self.spFunc  = spFunc
        self.slFunc  = slFunc
        self.aggFunc = aggFunc

    def _process_dict(self,d:Dict)->Tuple[Tuple[float,str],Tuple[Any,str]]:
        return ((self.xFunc.apply(d)
               ,'' if self.lFunc is None else self.lFunc.apply(d))
               ,(1  if self.spFunc  is None else self.spFunc.apply(d)
                       ,''  if self.slFunc is None else self.slFunc.apply(d)))

    def _draw(self,ax:'Axes',g:Group)->None:
        ax.set_xticklabels(ax.get_xticklabels()+[g.identifier])

        if self.spFunc is None:
            color = mkStyle(g.identifier).color
            val = self.aggFunc([x[0] for x in mapfst(g.elements)])
            ax.bar(x      = g.id
                  ,height = val
                  ,width  = 1
                  ,color  = color
                  ,align  = 'edge')

        else:
            subgroups = self._make_groups(*zip(*g.elements))
            n = len(subgroups)
            for i,sg in enumerate(subgroups):
                color = mkStyle(sg.identifier).color
                val   = self.aggFunc(mapfst(sg.elements))
                agg   = len(sg.elements) # PRINT THIS TO SCREEN IF FLAG IS TRUE?
                ax.bar(x      = g.id + i/n
                      ,height = val
                      ,width  = 1/n
                      ,color  = color
                      ,label  = sg.identifier
                      ,align  = 'edge')

    def _set_labels(self,ax:'Axes')->None:
        super()._set_labels(ax)
        ax.set_ylabel(self.yLab)
        ax.set_xticks([x+0.5 for x in range(len(self.groups))])
        ax.set_xticklabels([x.identifier for x in self.groups])
        [ax.axvline(i,linestyle='--') for i in range(1,len(self.groups))]
################################################################################
class HistPlot(Plot):
    """

    """
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
        super().__init__(query=query,xFunc=xFunc,lFunc=lFunc,gFunc=gFunc
                        ,glFunc=glFunc,title=title,xLab=xLab)
        self.bins = bins
        self.norm = norm

    def _process_dict(self,d:Dict)->Tuple[float,str]:
        return ((self.xFunc.apply(d)
               ,'' if self.lFunc is None else self.lFunc.apply(d)))
    def _draw(self,ax:'Axes',g:Group)->None:
        color = mkStyle(g.label).color
        ax.hist(mapfst(g.elements),histtype='bar',label=g.label,bins=self.bins
               ,color= color, density = self.norm)
