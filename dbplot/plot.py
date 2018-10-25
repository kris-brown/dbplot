# External Modules
from typing      import (Type,Any,Tuple,List,Dict,TypeVar,Set,
                         Optional as O, Callable as C, Union as U)
from abc         import abstractmethod
from operator    import itemgetter
from collections import OrderedDict
from json        import load

# Internal Modules
from dbplot.db     import ConnectInfo as Conn,select_dict
from dbplot.misc   import FnArgs,Group,mapfst,mapsnd,avg,const,identity,joiner
from dbplot.style  import mkStyle

AX = Any

#############################################################################
class Plot(object):
    def __init__(self,**kwargs:Any) -> None:
        self.data = kwargs

    @property
    def kw(self)->Set[str]:
        '''List of valid keyword arguments'''
        return {'query','title','xlab','ylab','xcols','xfunc','lcols','lfunc','l'}

    def _init(self)->None:
        '''Init called at plotting time - child classes have additional implementations'''
        assert 'xcols' in self.data and 'query' in self.data

        self.query = self.data['query']
        self.title = self.data.get('title')
        self.xlab  = self.data.get('xlab')
        self.ylab  = self.data.get('ylab')

        # X func, handle defaults
        if not 'xfunc' in self.data:
            if isinstance(self.data['xcols'],str):
                xcols = self.data['xcols'].split()
            else:
                xcols = self.data['xcols']
            assert len(xcols) == 1
            self.data['xfunc'] = identity

        self.xFunc = FnArgs(self.data['xfunc'],self.data['xcols'])

        # Labeling of data points, handle defaults
        if 'lcols' not in self.data:
            self.lFunc = FnArgs(func=const(''),args=[])
        elif 'lfunc' not in self.data:
            self.lFunc = FnArgs(func=joiner,args=self.data['lcols'])
        else:
            self.lFunc = FnArgs(self.data['lfunc'],self.data['lcols'])

        # Grouping of data points
        if 'gcols' not in self.data:
            # no way to group if no columns provided
            self.gFunc  = FnArgs(func = const(1), args = [])
            self.glFunc = FnArgs(func = const('') ,args = [])
        else:
            gcols = self.data['gcols']

            if 'gfunc' not in self.data:
                self.gFunc = FnArgs(func = joiner, args = gcols)
            else:
                self.gFunc = FnArgs(func = self.data['gfunc'], args = gcols)

            glcols = self.data['glcols' if 'glcols' in self.data else 'gcols']

            if 'glfunc' not in self.data:
                self.glFunc =  FnArgs(func = joiner, args = glcols)
            else:
                self.glFunc = FnArgs(func = self.data['glfunc'], args = glcols)


    def plot(self, ax : AX, conn : Conn, binds : list = []) -> None:
        """
        Only 'exposed' function of a Plot, calls other methods in order
        """
        self._init()
        results = select_dict(conn, self.query, binds)
        self.groups = self._make_groups(results, self.gFunc, self.glFunc)

        for g in self.groups:
            self._draw(ax,g)

        self._set_labels(ax)
        if self._has_leg:
            self._set_legend(ax)


    def _set_labels(self, ax : AX) -> None:
        """
        Default label setting behavior is just x axis and title
        """
        ax.set_xlabel(self.xlab)
        ax.set_ylabel(self.ylab)
        ax.set_title(self.title)

    @staticmethod
    def _make_groups(inputs : List[Dict[str,Any]],
                     gFunc  : FnArgs,
                     glFunc : FnArgs
                    ) -> List[Group]:
        """
        Take a list of processed DB outputs and sort into groups

        The groups will become different lines/bars on the final plot
        """
        groups = {} # type: Dict[Any,Group]
        counter = 0
        for x in inputs:
            g = gFunc.apply(x)
            if g in groups:
                groups[g].add_elem(x)
            else:
                gl = glFunc.apply(x)
                groups[g] = Group(id=counter,label=gl,rep=g,elems=[x])
                counter+=1

        return list(groups.values())

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
        '''ugly GUI stuff'''
        handles, labels = ax.get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        leg = ax.legend()
        if leg: leg.set_draggable(True)

    @staticmethod
    def pltdict()->Dict[str,Type['Plot']]:
        '''Mapping each type of plot to a unique string'''
        d = {'line':LinePlot,'bar':BarPlot,'hist':HistPlot} # type: Dict[str,Type['Plot']]
        return d

    @classmethod
    def from_file(cls,pth:str)->'Plot':
        '''Creates a Line/Bar/Hist plot from a JSON file containing KW args'''
        # Parse JSON file
        with open(pth,'r') as f:
            dic = load(f)
        # Determine which __init__ method should be used
        typ     = dic.pop('type').lower()
        plotter = cls.pltdict()[typ]

        # Create Plot object
        return plotter(**dic)

    @property
    def _has_leg(self)->bool:
        return bool(self.data.get('gcols'))

################################################################################
class LinePlot(Plot):
    """
    Scatter or line plot - a relation between two numeric variables
    """
    def _init(self)->None:
        super()._init()

        assert 'ycols' in self.data

        # Y func, handle defaults
        if not 'yfunc' in self.data:
            if isinstance(self.data['ycols'],str):
                ycols = self.data['ycols'].split()
            else:
                ycols = self.data['ycols']
            assert len(ycols) == 1
            self.data['yfunc'] = identity

        self.yFunc   = FnArgs(self.data['yfunc'],self.data['ycols'])
        self.post    = self.data.get('post')
        self.count   = self.data.get('count') # NOT YET (RE)IMPLEMENTED
        self.scatter = self.data.get('scatter')

    def _draw(self, ax : AX, g : Group) -> None:
        """Make a query, process results, then draw the lines"""
        # do aggregations, postprocessing to modify 'g', eventually
        g.map(self._process_dict)
        self._add_line(ax,g)

    def _process_dict(self, d : dict) -> Tuple[float,float,str]:
        """
        Take a raw dictionary output from DB and make a new dictionary with:
            x,y (floats) and l (label)
        """

        return {'x' : self.xFunc.apply(d),
                'y' : self.yFunc.apply(d),
                'l' : self.lFunc.apply(d)}

        return output

    def _add_line(self,ax:AX,g:Group)->None:
        """
        Draw a line from a Group with (X,Y,LABEL) tuples as elements
        """
        leg,     xyl    = g.label,g.elems
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

        # SubGrouping of data points
        if 'spcols' not in self.data:
            # no way to subgroup if no columns provided
            self.spFunc = FnArgs(func = const(1), args = [])
            self.slFunc = FnArgs(func = const('') ,args = [])
        else:
            gcols = self.data['spcols']

            if 'gfunc' not in self.data:
                self.spFunc = FnArgs(func = joiner, args = gcols)
            else:
                self.spFunc = FnArgs(func = self.data['gfunc'], args = gcols)

            glcols = self.data['slcols' if 'slcols' in self.data else 'spcols']

            if 'slfunc' not in self.data:
                self.slFunc = FnArgs(func = joiner, args = glcols)
            else:
                self.slFunc = FnArgs(func = self.data['slfunc'], args = glcols)

        self.aggFunc = self.data.get('aggFunc',avg)
        self.seen = set() # used to avoid plotting the same legend entries multiple times
    @property
    def _has_leg(self)->bool:
        return bool(self.data.get('spcols'))

    def _process_dict(self,d:dict)->dict:
        return {'val': self.xFunc.apply(d)}

    def _draw(self, ax : AX, g : Group) -> None:
        ax.set_xticklabels(ax.get_xticklabels()+[g.label])

        if self.spFunc is None:
            color = mkStyle(g.rep).color
            val = self.aggFunc([x['val'] for x in g.elems])
            ax.bar(x      = g.id,
                   height = val,
                   width  = 1,
                   color  = color,
                   align  = 'edge')

        else:
            subgroups = self._make_groups(g.elems,self.spFunc,self.slFunc)
            n = len(subgroups)
            for i,sg in enumerate(subgroups):
                sg.map(self._process_dict) # convert dictionaries into floats
                color = mkStyle(sg.rep).color
                val   = self.aggFunc([x['val'] for x in sg.elems])
                agg   = len(sg.elems) # PRINT THIS TO SCREEN IF FLAG IS TRUE?

                ax.bar(x      = g.id + i/n,
                       height = val,
                       width  = 1/n,
                       color  = color,
                       label  = sg.label if sg.label not in self.seen else '',
                       align  = 'edge')

                self.seen.add(sg.label)
    def _set_labels(self,ax:AX)->None:
        super()._set_labels(ax)
        ax.set_ylabel(self.ylab)
        ax.set_xticks([x+0.5 for x in range(len(self.groups))])
        ax.set_xticklabels([x.label for x in self.groups])
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
        ax.hist(mapfst(g.elems),histtype='bar',label=g.label,bins=self.bins,
                color= color, density = self.norm)
