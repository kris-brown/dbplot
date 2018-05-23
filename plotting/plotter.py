
#External modules
from typing import Any,List,Callable,Optional,Dict,Tuple,TYPE_CHECKING
from scipy import stats   # type: ignore
import numpy as np   # type: ignore
import random,sys,operator,collections
from abc import abstractmethod
if TYPE_CHECKING:
    from matplotlib.pyplot  import Ax   # type: ignore

# Internal modules
from utils.db import ConnectInfo,Query
from utils.misc import flatten
from utils.sql import *
from utils.plot import wrapper
from plotting.label import label2Line
# import CataLog.utils.db as db
#
# from CataLog.misc.sql_utils            import *
# from CataLog.plotting.plot_utils import avg,wrapper
# from CataLog.plotting.label      import label2Line
# from CataLog.misc.utilities      import flatten

################################################################################

"""
Definition of LinePlot, BarPlot, and HistPlot objects
"""

###################
# Helpful functions
# -----------------
def identity(x : Any) -> Any: return  x
def id2(x:Any,y:Any)->Any: return (x,y)
def id3(x:Any,y:Any,z:Any)->Any: return (x,y,z)
def id4(a:Any,b:Any,c:Any,d:Any)->Any: return  (a,b,c,d)
def id5(a:Any,b:Any,c:Any,d:Any,e:Any)->Any: return  (a,b,c,d,e)
idDict = {1:identity,2:id2,3:id3,4:id4,5:id5} # type: Dict[int,Callable]

fst      = lambda x: x[0]
headTail = lambda x: (x[0],x[1:])
def mapfst(xs:List[tuple])->List[Any]:  return [x[0] for x in xs]
def mapsnd(xs:List[tuple])->List[Any]:  return [x[1] for x in xs]


###################
# Main plot classes
#------------------

class Group(object):
    def __init__(self
                ,label    : str
                ,elements : List[tuple]
                ) -> None:
        self.label = label
        self.elements = elements
    def __str__(self)->str:
        return self.label+'\n'.join(map(str,self.elements))
    def __len__(self)->int: return len(self.elements)
    def apply(self,f:Callable)->None:
        """modify elements with a function"""
        self.elements = f(self.elements)


class Plot(object):

    def plot(self,ax:Ax,db:ConnectInfo,binds:List)->None:
        ax.set_xlabel(self.xLabel)
        ax.set_title(self.title)
        self._draw(ax,db,binds)
        self._set_legend(ax)

    @abstractmethod
    def _draw(self,ax:Ax,db:ConnectInfo,binds:List)->None:
        return

    def _set_legend(self,ax:Ax)->None:
        try:
            handles, labels = ax.get_legend_handles_labels()
            hl = sorted(zip(handles, labels),key=operator.itemgetter(1))
            handles2, labels2 = zip(*hl)
            ax.legend(handles2, labels2) #sort
            handles, labels = ax.get_legend_handles_labels()
            by_label = collections.OrderedDict(zip(labels, handles))
            legend = ax.legend(by_label.values(), by_label.keys()) # remove dups
            legend.draggable()
        except (AttributeError,ValueError) as e: print(e)

    def _group(self,db:ConnectInfo)->List[Group]:
        """
        Applies groupbyfunc to partition some query output.
        The first ng elements are used as input to the groupbyfunc.
        Returns list of Group objects.
        """

        print('Querying to get jobs and groupings...')
        q_results    = self.query.query(db)
        print('\tSplitting output into groups...')
        group_dict ,label_dict  = {}, {}
        for q_result in q_results:
            group = self.groupbyFunc(*q_result[:self.ng])     # first ng arguments are for purpose of grouping
            label = self.grouplabelFunc(*q_result[:self.ng])  # get label of this equivalence class
            rest  = q_result[self.ng:]                        # other results from query
            label_dict[group] = label
            try: group_dict[group].append(rest)          # add results to correct list
            except KeyError: group_dict[group] = [rest]  # add new category
        #print group_dict
        return [Group(label_dict[g],elems) for g,elems in group_dict.items()]

class LinePlot(Plot):
    def __init__(self
                ,groupbyCols        : List                              = [XC]
                ,xCols              : List                              = [PW]
                ,yCols              : List                              = [RAWENG]
                ,join_dict          : Dict                              = final_table_joins
                ,query_groupby      : Optional[List]                    = None
                ,constraint         : List                              = []
                ,labelCols          : List                              = [BLANK]
                ,xFunc              : Callable                          = identity
                ,yFunc              : Callable                          = identity
                ,postProcess        : Callable[[List[Tuple[float,float,str,int]]]
                                               ,List[Tuple[float,float,str,int]]]   = identity
                ,labelFunc          : Callable[[tuple],str]             = wrapper
                ,grouplabelFunc     : Callable[[tuple],str]             = wrapper
                ,title              : str                               = ''
                ,xLabel             : str                               = ''
                ,yLabel             : str                               = ''
                ,fitModel           : bool                              = False
                ,aggFunc            : Optional[Callable[[list],list]]   = None
                ,scatter            : bool                              = False
                ,show_count         : bool                              = True
                ,verbose            : bool                              = True
                ) -> None:

        self.title           = title
        self.xLabel          = xLabel
        self.yLabel          = yLabel
        self.xFunc           = xFunc
        self.yFunc           = yFunc
        self.postProcess     = postProcess
        self.labelFunc       = labelFunc
        self.grouplabelFunc  = grouplabelFunc

        self.fitModel    = fitModel
        self.aggFunc     = aggFunc
        self.scatter     = scatter
        self.verbose     = verbose
        self.show_count  = show_count

        table = joiner_simple(job,join_dict)
        self.query = Query(cols = groupbyCols+xCols+yCols+labelCols
                             ,constraints = constraint
                             ,table = table
                             ,group=query_groupby)

        self.n           = (len(xCols),len(yCols))
        self.ng          = len(groupbyCols)

    def _draw(self,ax:Ax,db:ConnectInfo)->None:
        groups = self._group(db)
        print('Number of groups: ',len(groups))

        for g in groups:
            g.apply(self._extract) #convert remaining args to (x,y,l) triples
            g.apply(self._process) #aggregate, sort, postprocess into (x,y,l,n) tuples
            self._addLine(ax,g)
            #if self.fitModel and len(l_xyl[1])>0:    self._fit(ax,l_xyl)

    def _extract(self,group_elems:List[tuple])->List[Tuple[int,int,str]]:
        nx,ny   = self.n

        def xTract(xyl : tuple)->Optional[Tuple[int,int,str]]:
            x = self.xFunc(*(xyl[:nx]))         # first nx tuple elements are inputs for xFunc
            y = self.yFunc(*(xyl[nx:nx+ny]))    # next  ny tuple elements are inputs for yFunc
            l = self.labelFunc(*(xyl[nx+ny:]))  # remaining elements are for labelFunc
            if l is None: l = ''
            if x is not None and y is not None:
                return (x,y,l)
            else:
                return None
        return [z for z in map(xTract,group_elems) if z is not None]

    def _process(self,xyls : List[Tuple[float,float,str]]
                ) -> List[Tuple[float,float,str,int]]:
        """
        Input: a list of (x,y,l) triples that are associated with a Group
        Output: ordered, possibly aggregated, post-processed list of (x,y,l,n) quadruples
                 where n represents multiplicity of aggregated values per data point
        """

        # if self.aggFunc is not None:
        #     xs = sorted(list(set(mapfst(xyls))))
        #
        #     xyl_in,x_to_y,x_to_l,x_to_g = [],{},{},{}
        #     for x in xs:
        #         n = len([x0 for (x0,y0,l0) in xyls if x0 == x])
        #         y = self.aggFunc([y0 for (x0,y0,l0) in xyls if x0 == x])
        #         l = [l0 for (x0,y0,l0) in xyls if x0==x][0] # default to take first label
        #         xyl_in.append((x,y,l,n))
        # else:
        xyl_in  = sorted([(x0,y0,l0,1) for (x0,y0,l0) in xyls]) # sort by x's

        xyl_out = self.postProcess(xyl_in) # postprocess (take derivatives, etc.)
        return xyl_out

    def _addLine(self
                ,ax    : Ax
                ,group : Group
                ) -> None:
        leg,     xyln   = group.label,group.elements
        handles, labels = ax.get_legend_handles_labels()

        if len(xyln)>0:
            if self.verbose:
                print('\tadding line for %s'%leg)
            ls,c,m = label2Line(leg)                                                  # get line style based on legend name
            linestyle = ' ' if self.scatter else ls

            ax.plot(mapfst(xyln),mapsnd(xyln),linestyle=linestyle
                     ,color=c,marker=m,label=leg) # add line
            for (x,y,l,n) in xyln:
                ax.text(x,y,l,size=9                              # add data labels
                    ,horizontalalignment='center',verticalalignment='bottom')
                if self.show_count:
                    ax.text(x,y,"(%d)"%n,size=6                             # add aggregate count
                        ,horizontalalignment='center',verticalalignment='top')
    #
    # def _fit(self,ax,l_xyl):
    #     xs,ys,leg = mapfst(l_xyl[1]),mapsnd(l_xyl[1]),l_xyl[0]
    #     if self.verbose: print('\tfitting %s to line'%leg)
    #     slope, intercept, r_value, p_value, std_err  = stats.linregress(xs,ys)
    #     abline_values = [slope * i + intercept for i in xs]
    #     if self.verbose: print('\t\tFit %s to line with slope %6.3e and intercept %6.3e (R2=%.2f)'%(leg,slope,intercept,r_value))
    #     ls,c,m = label2Line(leg)                                                  # get line style based on legend name
    #     # Plot the best fit line over the actual values
    #     ax.plot(xs, abline_values,linestyle=ls,color=c,marker=m,markersize=1,linewidth=0.5)
#
#
# #######################################################################################
# #######################################################################################
#
# class BarPlot(Plot):
#     def __init__(self,constraint,yCols,groupbyCols,splitbyCols=[BLANK]   #  all jobs have equal blank value
#                 ,table=final_table,verbose=True,atoms_table=False
#                 ,groupbyFunc=None,      splitbyFunc=None, yFunc=identity, aggFunc = avg
#                 ,grouplabelFunc=wrapper, splitlabelFunc=wrapper,title='',xLabel='',yLabel=''):
#
#         #self.reproduce   =  "BarPlot(%s)"%self._reproduce(locals())
#
#         if groupbyFunc    is None: groupbyFunc    = idDict[len(groupbyCols)]# identity function for tuple of the correct length (max 5)
#         if splitbyFunc    is None: splitbyFunc    = idDict[len(splitbyCols)]
#         if atoms_table: table,group=final_table,None
#         else:           table,group=final_atom_table,atom.atoms_id
#
#
#         self.title       = title                # String
#         self.xLabel      = xLabel               # String
#         self.yLabel      = yLabel               # String
#
#         self.groupbyFunc    = groupbyFunc       # Eq c => (a,b,...) -> c -- test for equality that aggregates jobs
#         self.splitbyFunc    = splitbyFunc       # Eq c => (a,b,...) -> c -- test for equality that aggregates jobs
#         self.grouplabelFunc = grouplabelFunc    # (a,b,...) -> String
#         self.splitlabelFunc = splitlabelFunc    # (a,b,...) -> Sring
#         self.yFunc          = yFunc             # (a,b,...)->Float
#         self.aggFunc        = aggFunc           # [Float]->Float
#         self.verbose        = verbose           # Bool
#         self.show_count     = True              # Bool
#
#         self.query = db.Query(groupbyCols+splitbyCols+yCols,constraint,table,group=group)
#
#         self.ng    = len(groupbyCols)
#         self.ns    = len(splitbyCols)
#
#     def _draw(self,ax,db_path):
#
#         groups = self._group(db_path)
#         for g in groups: g.apply(self._split) #split the args of group elements into subgroups
#
#         self.num_groups = len(groups)
#         self.num_splits = max([len(g.elements) for g in groups])
#
#         if self.verbose:
#             print('\tNumber of groups: %d' % self.num_groups)
#             print('\tTotal possible bars per group: %d' % self.num_splits)
#
#         self._setXticks(ax,groups)
#         self._make_bars(ax,groups)
#
#     def _make_bars(self,ax,groups):
#         handles,labels=ax.get_legend_handles_labels() #get existing legend item handles and labels
#
#         for i,g in enumerate(groups):
#             for j,s in enumerate(g.elements):
#                 n     = len(s)                                              # number of elements in this group+split
#                 y     = self.aggFunc(s.elements)                            # compress information to one number
#                 color = label2Line(s.label)[1]
#                 pos   = i*(self.num_splits+1) + j + 0.5                     # every bar width 1, 1 space between groups
#                 label = s.label if s.label not in labels else '_nolegend_' # forbid repeat elements in legend
#                 ax.bar(pos,y,width=1,color=color,label=label)
#                 if self.show_count: ax.text(pos,y,"(%d)"%n,fontsize=8  # show how many DB hits were aggregated
#                     ,horizontalalignment='center',verticalalignment='bottom')
#
#     def _split(self,group_elems):
#         split_dict = {}
#         for group_elem in group_elems:
#             splt  = self.splitbyFunc(*group_elem[:self.ns])     # first sg arguments are for purpose of splitting the group
#             label = self.splitlabelFunc(*group_elem[:self.ns])  # get label of this equivalence class
#             val   = self.yFunc(*group_elem[self.ns:])           # remaining elements used for height of bar
#             if val is not None:
#                 try: split_dict[splt].append(val)          # add results to correct list
#                 except KeyError: split_dict[splt] = [val]  # add new category
#
#         return [Group(lab,vals) for lab,vals in split_dict.items()] #replace tuple with a list of Groups
#
#     def _setXticks(self,ax,groups):
#         ts = np.arange(self.num_groups)*(self.num_splits+1) # allocate space for each group
#         ax.set_xticks(ts + ((self.num_splits)/2.))        # shift ticks to center of group interval
#         ax.set_xticklabels([x.label for x in groups])
#         for t in ts: ax.axvline(t,color='k',ls='--',lw=0.5)
#
#
# #######################################################################################
# #######################################################################################
#
# class HistPlot(Plot):
#     def __init__(self,xCols,groupbyCols,constraint=[]
#                 ,groupbyFunc=None,xFunc=identity,grouplabelFunc=wrapper,verbose=True
#                 ,title='',xLabel='',bins='auto',normalize=False,table=db.final_table):
#
#         if groupbyFunc    is None: groupbyFunc    = idDict[len(groupbyCols)]# identity function for tuple of the correct length (max 5)
#
#
#         self.title           = title               # String
#         self.xLabel          = xLabel              # String
#
#         self.groupbyFunc     = groupbyFunc         # Eq c => (a,b,...) -> c -- test for equality that aggregates jobs
#         self.grouplabelFunc  = grouplabelFunc      # (a,b,...) -> String
#         self.xFunc           = xFunc               # (a,b,...)->Float
#         self.bins            = bins                # Integer
#         self.normalize       = normalize           # Bool
#         self.yLabel          = 'Frequency' if self.normalize else 'Count'
#         self.verbose        = verbose
#
#         self.query          = db.Query(groupbyCols+xCols,constraint,table)
#         self.ng             = len(groupbyCols)
#
#     def _draw(self,ax,db_path):
#         gs =  self._group(db_path)
#         groupLabels = [g.label for g in gs]
#         list_ys = [map(lambda x: self.xFunc(*x),g.elements) for g in gs]
#         numGroups = len(gs)
#         print('\tNumber of groups: ',numGroups)
#
#         ax.hist(list_ys,histtype='bar',label=groupLabels,bins=self.bins,normed= self.normalize) #stacked=True?
#


#######
#Graveyard
#---------
"""def _reproduce(self,localvars): return None
        def process(kv):  #Convert dictionary of namespace into command-line input to recreate object
            k,v = kv
            if isinstance(v,str):                             v = "'%s'"%(v.replace("'","\\'").replace('\n',' '))
            elif isinstance(v,list) and isinstance(v[0],str): v = "'%s'"%' '.join(v)
            elif hasattr(v,'__call__'):                       v = v.__name__
            else:                                             v = str(v)
            return "%s=%s"%(k,v)
        del localvars['self']
        processed_args =  ','.join(map(process,localvars.items()))
        return processed_args
    """
