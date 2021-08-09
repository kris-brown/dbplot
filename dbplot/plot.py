# External Modules
from typing      import (Type,Any,Tuple,List,Dict,TypeVar,Set,
                         Optional as O, Callable as C, Union as U)
from abc         import abstractmethod
from operator    import itemgetter
from collections import OrderedDict

from plotly.graph_objs import Figure,Layout # type: ignore

# Internal Modules
from dbplot.db     import ConnectInfo as Conn,select_dict
from dbplot.misc   import FnArgs,Group,mapfst,mapsnd,avg,const,identity,joiner,mkFunc, load
from dbplot.style  import mkStyle
#############################################################################


class Plot(object):
    '''
    High level representation of a plotly plot, requiring a DB connection
    '''

    #------------#
    # Overloaded #
    #------------#

    def __init__(self, **kwargs : Any) -> None:
        err = 'Unsupported keys: %s'
        bad = set(kwargs) - self.kw
        assert not bad, err % bad
        self.data = kwargs

    def __str__(self)->str:
        return str(self.data)

    __repr__ = __str__

    def __getitem__(self, key : str) -> Any:
        return self.data.get(key)

    def __setitem__(self, key : str, item : Any) -> Any:
        self.data[key] = item

    def __contains__(self, item : str) -> bool:
        return item in self.data

    #---------------#
    # 'Exposed API' #
    #---------------#

    def fig(self, conn : Conn, binds : list, funcs : dict) -> Figure:
        '''Make a plotly figure'''
        self._groups(conn,binds,funcs)
        return Figure(data=self._data(),layout=self._layout())

    @abstractmethod
    def csv(self, pth : str) -> None:
        '''Write plot data to a csv'''
        raise NotImplementedError
    #------------------#
    # Abstract methods #
    #------------------#

    @abstractmethod
    def _layout(self) -> dict:
        frame = self['frame'] and self['frame'].lower()[0]=='t'
        square = self['square'] and self['square'].lower()[0]=='t'
        titlefont = dict(family='Times New Roman', size=60)
        font = dict(family='Times New Roman', size=25)
        if square: width, height = 800,600
        else: width, height = None, None
        if frame:
            return Layout(title = dict(text=self['title'],xref='paper'),margin=dict(l = 100,t=80),titlefont=titlefont,font = font,width = width, height = height,
                        xaxis = dict(title = self['xlab'],tickprefix=" ", titlefont = titlefont,tickfont = font,mirror = True,ticks='outside',showline=True,linewidth=4),
                        yaxis = dict(title = self['ylab'],tickprefix=" ", titlefont = titlefont,tickfont = font, mirror = True,ticks='outside',showline=True,linewidth=4),
                        legend=dict(y=0.5,x=1.02,xanchor='left',yanchor='middle',orientation="v",bgcolor='rgba(0,0,0,0)'))
        else:
            return Layout(title = self['title'], width = width, height = height,font=dict(family='Courier New, monospace', size=30),
                        xaxis = dict(title = self['xlab']),
                        yaxis = dict(title = self['ylab']))


    @abstractmethod
    def _init(self, funcs : Dict[str,C]) -> None:
        '''Init called at plotting time - child classes have additional implementations'''

        assert 'xcols' in self and 'query' in self

        locals().update(funcs)

        # X func, handle defaults
        if not 'xfunc' in self:
            if isinstance(self['xcols'],str):
                xcols = self['xcols'].split()
            else:
                xcols = self['xcols']
            assert len(xcols) == 1
            self['xfunc'] = identity

        self.xFunc = FnArgs(func = self['xfunc'], args = self['xcols'], funcs = funcs)

        # Labeling of data points, handle defaults (meaningless for HIST)
        if 'lcols' not in self:
            self.lFunc = FnArgs(func=const(''),args=[], funcs = funcs)
        elif 'lfunc' not in self:
            self.lFunc = FnArgs(func=joiner,args=self['lcols'],funcs=funcs)
        else:
            self.lFunc = FnArgs(self['lfunc'],self['lcols'],funcs=funcs)

        # Grouping of data points
        if 'gcols' not in self:
            # no way to group if no columns provided
            self.gFunc  = FnArgs(func = const(1), args = [], funcs = funcs)
            self.glFunc = FnArgs(func = const('') ,args = [], funcs = funcs)
        else:
            gcols = self['gcols']

            if 'gfunc' not in self:
                self.gFunc = FnArgs(func = joiner, args = gcols, funcs = funcs)
            else:
                self.gFunc = FnArgs(func = self['gfunc'], args = gcols, funcs = funcs)

            glcols = self['glcols' if 'glcols' in self else 'gcols']

            if 'glfunc' not in self:
                self.glFunc =  FnArgs(func = joiner, args = glcols, funcs = funcs)
            else:
                self.glFunc = FnArgs(func = self['glfunc'], args = glcols, funcs = funcs)


    @abstractmethod
    def _draw(self, g : Group) -> dict:
        """
        Fill out the plot in some way - different implementation for each subclass
        """
        raise NotImplementedError

    @abstractmethod
    def _process_group_dict(self,d:Dict)->Any:
        """
        Take a DB output dict and make a pair: <SOMETHING>,(group ID, group label)
        """
        return d

    @property
    @abstractmethod
    def kw(self) -> Set[str]:
        '''List of valid keyword arguments'''
        return {'query','title','xlab','frame','square',
                'xcols','xfunc','lcols','lfunc','gcols','gfunc'}

    #------------------------#
    # Static / Class methods #
    #------------------------#
    @staticmethod
    def pltdict()->Dict[str,Type['Plot']]:
        '''Mapping each type of plot to a unique string'''
        d = {'line':LinePlot,'bar':BarPlot,'hist':HistPlot} # type: Dict[str,Type['Plot']]
        return d

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
            g = gFunc(x)
            if g in groups:
                groups[g].add_elem(x)
            else:
                gl = glFunc(x)
                groups[g] = Group(id=counter,label=gl,rep=g,elems=[x])
                counter+=1

        return list(groups.values())

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

    #------------#
    # Properties #
    #------------#

    @property
    def _has_leg(self)->bool:
        return bool(self['gcols'])

    @property
    def opacity(self) -> float:
        return max(0.1,1-len(self.groups)/10)

    #-------------------#
    # Support functions #
    #-------------------#
    def _groups(self, conn : Conn, binds : list = [], funcs : Dict[str,C] = {}) -> None:
        """
        Populates: self.groups
        """
        self._init(funcs)
        assert self['query']
        results = conn.select_dict(self['query'], binds)
        self.groups = self._make_groups(results, self.gFunc, self.glFunc)

    def _data(self) -> list:
        ''' This seems to be a general enough implementation'''
        # for g in self.groups:

        return [self._draw(g.map(self._process_group_dict)) for g in self.groups]

################################################################################
class LinePlot(Plot):
    """
    Scatter or line plot - a relation between two numeric variables
    """
    def _init(self, funcs : Dict[str,C])->None:
        super()._init(funcs)

        assert 'ycols' in self, 'LinePlot requires ycols to be specified'

        # Y func, handle defaults
        if not 'yfunc' in self:
            if isinstance(self['ycols'],str):
                ycols = self['ycols'].split()
            else:
                ycols = self['ycols']
            assert len(ycols) == 1
            self['yfunc'] = identity

        self.yFunc = FnArgs(func = self['yfunc'], args = self['ycols'], funcs = funcs)

    def csv(self, pth : str) -> None:
        '''Write plot data to a csv'''
        raise NotImplementedError

    @property
    def kw(self)->Set[str]:
        return super().kw | {'ylab','ycols','yfunc','scatter'}

    def _draw(self, g : Group) -> dict:
        """process query results, then draw the lines"""
        # do aggregations, postprocessing to modify 'g', eventually
        g.sort(key=lambda x: x['x'])
        return self._add_line(g)

    def _process_group_dict(self, d : dict) -> dict:
        """
        Take a raw dictionary output from DB and make a new dictionary with:
            x,y (floats) and l (label)
        """

        return dict(x = self.xFunc(d),
                    y = self.yFunc(d),
                    l = self.lFunc(d))

    def _add_line(self, g : Group) -> dict:
        """
        Draw a line from a Group with (X,Y,LABEL) tuples as elements
        """

        leg, xyl = g.label, g.elems

        sty  = mkStyle(leg)    # get line style based on legend name
        scatr= self['scatter'] and self['scatter'][0].lower()=='t'
        mode = 'markers' if scatr else 'lines+markers'
        return dict(x       = g['x'],
                    y       = g['y'],
                    text    = g['l'],
                    mode    = mode,
                    name    = g.label,
                    marker  = dict(opacity = self.opacity,
                                   color   = sty.color),
                    line    = dict(color   = sty.color,
                                   dash    = sty.line,
                                   shape   = 'spline'))

    def _layout(self)->dict:
        return super()._layout()

################################################################################
class BarPlot(Plot):
    """
    Bar plots - relation between a real-valued variable and a categorical one
    """

    def _init(self, funcs : Dict[str,C])->None:
        super()._init(funcs)

        # SubGrouping of data points
        if 'spcols' not in self:
            # no way to subgroup if no columns provided
            self.spFunc = FnArgs(func = const(1), args = [], funcs = funcs)
            self.slFunc = FnArgs(func = const('') ,args = [], funcs = funcs)
        else:
            gcols = self['spcols']

            if 'gfunc' not in self:
                self.spFunc = FnArgs(func = joiner, args = gcols, funcs = funcs)
            else:
                self.spFunc = FnArgs(func = self['gfunc'], args = gcols, funcs = funcs)

            glcols = self['slcols' if 'slcols' in self else 'spcols']

            if 'slfunc' not in self:
                self.slFunc = FnArgs(func = joiner, args = glcols, funcs = funcs)
            else:
                self.slFunc = FnArgs(func = self['slfunc'], args = glcols, funcs = funcs)

        self.aggFunc = avg # tell typechecker that this is the real type

        if self['aggfunc']:
            self.aggFunc = mkFunc(self['aggfunc'],funcs)  # type: ignore

        self.seen = set() # type: set ### used to avoid plotting the same legend entries multiple times

    def csv(self, pth : str) -> None:
        '''Write plot data to a csv'''
        raise NotImplementedError

    def _process_group_dict(self, d : dict)->dict:
        return d # do nothing

    def _process_subgroup_dict(self,d:dict)->dict:
        return dict(val = self.xFunc(d), l = self.lFunc(d))

    def _draw(self, g : Group) -> dict:

        color = mkStyle(g.rep).color

        subgroups_ = self._make_groups(g.elems,self.spFunc,self.slFunc)
        subgroups  = [sg.map(self._process_subgroup_dict) for sg in subgroups_]


        vals = [self.aggFunc(sg['val']) for sg in subgroups]
        color = mkStyle(g.rep).color

        return dict(type = 'bar',
                    name = g.label,
                    x    = [sg.label for sg in subgroups],
                    y    = vals,
                    )#marker = dict(color=color))

    def _layout(self)->dict:
        return Layout(super()._layout(),
                      barmode = 'group')

    @property
    def _has_leg(self)->bool:
        return bool(self['spcols'])

    @property
    def kw(self)->Set[str]:
        return super().kw | {'aggfunc','spcols','spfunc','ylab'}


################################################################################

class HistPlot(Plot):
    """
    Make a histogram. Extra keywords are:
        - bins :: int
        - norm :: bool (whether or not to normalize histogram such that sum of all bars is 1)
    """

    def _init(self, funcs : Dict[str,C]) -> None:
        assert 'lcols' not in self, "Cannot label data points of a histogram"
        super()._init(funcs)
        self.bins = self['bins'] or 10
        self.norm = self['norm'] or False

    def csv(self, pth : str) -> None:
        '''Write plot data to a csv'''
        raise NotImplementedError

    @property
    def kw(self) -> Set[str]:
        return super().kw | {'bins', 'norm'}

    def _process_dict(self, d : Dict) -> dict:
        return dict(x = self.xFunc(d))

    def _draw(self, g : Group) -> dict:
        color = mkStyle(g.label).color

        start, end = min(g['x']), max(g['x'])

        return dict(type     = 'histogram',
                    x        = g['x'],
                    xbins    = dict(start = start,
                                    end   = end,
                                    size  = 10000000),
                    histnorm = 'probability' if self.norm else None,
                    marker   = {'color':color},
                    opacity  = self.opacity,
                    name     = g.label)

    def _layout(self)->dict:
        return super()._layout()
