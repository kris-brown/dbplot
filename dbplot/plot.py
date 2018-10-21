# External Modules
from typing      import (Type,Any,Tuple,List,Dict,TypeVar,
                         Optional as O, Callable as C, Union as U)
from abc         import abstractmethod
from operator    import itemgetter
from collections import OrderedDict
from json        import load

# Internal Modules
from dbplot.db     import ConnectInfo,select_dict
from dbplot.misc   import FnArgs,A,B,Group,mapfst,mapsnd,avg
from dbplot.style  import mkStyle

AX = Any
Fn = U[str,C] # a Python function (or a string needed to be 'eval'ed)

#############################################################################
class Plot(object):
    def __init__(self,**kwargs:Any) -> None:

        if 'glcols' not in kwargs:
            kwargs['glcols'] = kwargs.get('gcols')
        if 'glfunc' not in kwargs:
            kwargs['glfunc'] = kwargs.get('gfunc')
        self.data = kwargs


    def _init(self)->None:
        self.query   = self.data.get('query')
        self.title   = self.data.get('title')
        self.xlab    = self.data.get('xlab')
        self.ylab    = self.data.get('ylab')

        self.xFunc   = FnArgs.fromFuncStr(self.data.get('xfunc'),self.data.get('xcols'))
        self.lFunc   = FnArgs.fromFuncStr(self.data.get('lfunc'),self.data.get('lcols'))
        self.gFunc   = FnArgs.fromFuncStr(self.data.get('gfunc'),self.data.get('gcols'))
        self.glFunc  = FnArgs.fromFuncStr(self.data.get('glfunc'),self.data.get('glcols'))

    def plot(self,
             ax    : AX,
             conn  : ConnectInfo,
             binds : O[list]        = None
            ) -> None:
        """
        Only 'exposed' function of a Plot, calls other methods in order
        """
        self._init()
        assert self.query
        binds        = binds or []
        results      = select_dict(conn,self.query,binds)
        groupdata    = [self._groupdata(d)    for d in results]
        processed    = [self._process_dict(d) for d in results]


        self.groups  = self._make_groups(processed,groupdata)
        for g in self.groups:
            self._draw(ax,g)

        self._set_labels(ax)
        self._set_legend(ax)

    def _groupdata(self,d:dict)->Tuple[Any,str]:

        return  ((1  if self.gFunc  is None else self.gFunc.apply(d),
                 ''  if self.glFunc is None else self.glFunc.apply(d)))


    def _set_labels(self, ax : AX) -> None:
        """
        Default label setting behavior is just x axis and title (can be super'd)
        """
        ax.set_xlabel(self.xlab)
        ax.set_ylabel(self.ylab)
        ax.set_title(self.title)

    @staticmethod
    def _make_groups(inputs    : List[B],
                     groupdata : List[Tuple[A,str]]
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
    def _draw(self, ax : AX, g : Group) -> None:
        """
        Fill out the plot in some way - different implementation for each subclass
        """
        raise NotImplementedError

    @abstractmethod
    def _process_dict(self,d:Dict)->Any:
        """
        Take a DB output dict and make a pair: <SOMETHING>,(group ID, group label)
        """
        raise NotImplementedError

    @staticmethod
    def _set_legend(ax:AX)->None:
        handles, labels = ax.get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())


    @staticmethod
    def pltdict()->Dict[str,Type['Plot']]:
        d = {'line':LinePlot,'bar':BarPlot,'hist':HistPlot} # type: Dict[str,Type['Plot']]
        return d

    @classmethod
    def from_file(cls,pth:str)->'Plot':

        with open(pth,'r') as f:
            dic = load(f)

        typ = dic.pop('type')
        plotter = cls.pltdict()[typ]
        return plotter(**dic)



################################################################################
class LinePlot(Plot):
    """
    Scatter or line plot - a relation between two numeric variables
    """
    def _init(self)->None:
        super()._init()
        self.yFunc   = FnArgs.fromFuncStr(self.data.get('yfunc'),self.data.get('ycols'))
        self.post    = self.data.get('post')
        self.count   = self.data.get('count')
        self.scatter = self.data.get('scatter')

    def _draw(self, ax : AX, g : Group) -> None:
        """Make a query, process results, then draw the lines"""
        # do aggregations, postprocessing to modify 'g', eventually
        self._add_line(ax,g)

    def _process_dict(self, d : dict) -> Tuple[float,float,str]:
        """
        Take a raw dictionary output from DB and make an output tuple:
            - x,y (floats)
            - l (label)
            - g (group identifier)
            - gl (group label)
        """
        assert self.xFunc and self.yFunc

        output = ((self.xFunc.apply(d),
                  self.yFunc.apply(d),
                  '' if self.lFunc  is None else self.lFunc.apply(d)))

        return output

    def _add_line(self,ax:AX,g:Group)->None:
        """
        Draw a line from a Group with (X,Y,LABEL) tuples as elements
        """
        leg,     xyl    = g.label,g.elements
        handles, labels = ax.get_legend_handles_labels()

        if len(xyl)>0:
            sty  = mkStyle(leg)    # get line style based on legend name
            line = ' ' if self.scatter else sty.line

            ax.plot(mapfst(xyl),mapsnd(xyl),linestyle=line
                     ,color=sty.color,marker=sty.marker,label=leg) # add line
            for (x,y,l) in xyl:
                ax.text(x,y,l,size=9                              # add data labels
                    ,horizontalalignment='center',verticalalignment='bottom')

################################################################################
class BarPlot(Plot):
    """
    Bar plots - relation between a real-valued variable and a categorical one
    """

    def _init(self)->None:
        super()._init()
        self.spFunc  = FnArgs.fromFuncStr(self.data.get('spfunc'),self.data.get('spcols'))
        self.slFunc  = FnArgs.fromFuncStr(self.data.get('slfunc'),self.data.get('slcols'))
        self.aggFunc = self.data.get('aggFunc',avg)

    def _process_dict(self,d:Dict)->Tuple[Tuple[float,str],Tuple[Any,str]]:
        assert self.xFunc
        return ((self.xFunc.apply(d)
               ,'' if self.lFunc is None else self.lFunc.apply(d))
               ,(1  if self.spFunc  is None else self.spFunc.apply(d)
                       ,''  if self.slFunc is None else self.slFunc.apply(d)))

    def _draw(self,ax:AX,g:Group)->None:
        ax.set_xticklabels(ax.get_xticklabels()+[g.identifier])

        if self.spFunc is None:
            color = mkStyle(g.identifier).color
            val = self.aggFunc([x[0] for x in mapfst(g.elements)])
            ax.bar(x      = g.id,
                   height = val,
                   width  = 1,
                   color  = color,
                   align  = 'edge')

        else:
            subgroups = self._make_groups(*zip(*g.elements))
            n = len(subgroups)
            for i,sg in enumerate(subgroups):
                color = mkStyle(sg.identifier).color
                val   = self.aggFunc(mapfst(sg.elements))
                agg   = len(sg.elements) # PRINT THIS TO SCREEN IF FLAG IS TRUE?
                ax.bar(x      = g.id + i/n,
                       height = val,
                       width  = 1/n,
                       color  = color,
                       label  = sg.identifier,
                       align  = 'edge')

    def _set_labels(self,ax:AX)->None:
        super()._set_labels(ax)
        ax.set_ylabel(self.ylab)
        ax.set_xticks([x+0.5 for x in range(len(self.groups))])
        ax.set_xticklabels([x.identifier for x in self.groups])
        [ax.axvline(i,linestyle='--') for i in range(1,len(self.groups))]

################################################################################

class HistPlot(Plot):
    """
    Make a histogram. Extra keywords are:
        - bins :: int
        - norm :: bool (whether or not to normalize histogram such that sum of all bars is 1)
    """

    def _init(self)->None:
        super()._init()
        self.bins = self.data.get('bins',10)
        self.norm = self.data.get('norm',False)

    def _process_dict(self,d:Dict)->Tuple[float,str]:
        assert self.xFunc
        return ((self.xFunc.apply(d),
                '' if self.lFunc is None else self.lFunc.apply(d)))

    def _draw(self,ax:AX,g:Group)->None:
        color = mkStyle(g.label).color
        ax.hist(mapfst(g.elements),histtype='bar',label=g.label,bins=self.bins,
                color= color, density = self.norm)
