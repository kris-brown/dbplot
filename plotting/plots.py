#External
from typing import List,Callable
import json,copy,functools

# Internal
from CataLog.misc.sql_utils            import *
from CataLog.plotting.plot_utils import *
from CataLog.plotting.plotter import Plot,LinePlot,identity
from CataLog.misc.utilities   import merge_dicts

################################################################################

def xyX(lst : tuple)->bool: return not (lst[0] is None or lst[1] is None)
def len2(xs:List[tuple])->bool: return 1 <  len(set(([x[0] for x in xs if xyX(x)])))

"""
###################################
# Summary of Options for parameters
# ---------------------------------

title/xLabel/yLabel - (All) -- anything you want
constraint          - (All) -- any valid SQL 'where' clause
___Cols             - (All) -- any space-separated list of columns in suncatdata.db
___Func             - (All) -- any function (with arity = # of cols in corresponding __Cols)
___LabelFunc        - (All) -- any function (a,...) -> String

aggFunc             - (Line/Barplot) -- any function [(a,...)]-> Float (with tuple arity corresponding to OUTPUT of yFunc)
postProcess         - (Lineplot) -- any function [(x,y,label)]->[(x,y,label)]

fitModel            - (Lineplot) -- {True,False}
normalize           -  (Histograms) -- {True,False}

#####################################
# Available Functions in plotFuncs.py
# -----------------------------------

### In general
* groupbyFuncs
    - num2metalStoich

* xFuncs
    - countH

* yFuncs
    - eFormPerMetalAtom

* labelFuncs
    - name2element

### For Bar Plots
* aggFuncs
    - avg
    - absavg
    - gMeanAbs
    - converged(yCols)

### For Line Plots
* PostProcessing
    - absdiff
    - deriv
    - derivabsdiff

"""

##################
# Helper Functions
# ----------------
def compose(*functions : List[Callable])->Callable:
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x) # type: ignore
def m(a:dict)->dict:
    try:
        b=a.pop('kwargs')
        return merge_dicts([a,b])
    except KeyError:
        return a

###########
# Bar Plots
# ---------

def count(constraint = []
        ,title       = 'Total Calculations'
        ,xLabel      = 'dftcode'
        ,yLabel      = 'Count'
        ,groupbyCols = [DFTCODE]
        ,splitbyCols = [XC]
        ,yCols       = [BLANK]
        ,aggFunc     = len
        ,**kwargs):  return BarPlot(**m(locals()))


def errorLatticeAt500(title       = 'Lattice Constant errors at PW=500eV'
                     ,xLabel      = 'DFT code'
                     ,constraint  = AND(LATTICEOPT_,PW_(500))
                     ,groupbyCols = [DFTCODE]
                     ,splitbyCols = [STRUCTURE]
                     ,yCols       = [JOBNAME,SQRT(AX*AX+AY*AY+AZ*AZ),STRUCTURE]
                     ,yFunc       = errA
                     ,yLabel      = r'Lattice error GMAE, $\AA$'
                     ,aggFunc     = gMeanAbs
                     ,**kwargs): return BarPlot(**m(locals()))


def errKPTLOW(constraint=AND(LATTICEOPT_,PW_(500)
             ,KPTLOW_) ,**kwargs):
    return errorLatticeAt500(**m(locals()))

def errKPTHIGH(constraint=AND(LATTICEOPT_
              ,PW_(500),KPTHIGH_) ,**kwargs):
    return errorLatticeAt500(**m(locals()))


def gMeanErrLat500(aggFunc=gMeanAbs
                  ,yLabel=r'GMAE, $\AA$'
                  ,**kwargs): return errorLatticeAt500(**m(locals()))


def surfEng( title          = 'Surface energies '
            ,xLabel         = 'Metal'
            ,constraint     = [SYMSLAB,KSB_]
            ,groupbyCols    = [JOBNAME]
            ,splitbyCols    = [DFTCODE,XC,PSP,PW]
            ,grouplabelFunc = name2element
            ,yCols          = [JOBNAME,SURFENG]
            ,yFunc          = errSE
            ,yLabel         = r'RMS Error, $eV/\AA^2$'
            ,aggFunc        = RMS
            ,**kwargs):       return BarPlot(**m(locals()))

def surfEng_highKPT(constraint = AND(RELAX_,SURFACE_,PW_(1500),KPTHIGH_),**kwargs): return surfEng(**m(locals()))

def surfEng_XC(groupbyCols=[XC],grouplabelFunc=identity,**kwargs):       return surfEng(**m(locals()))

def convExample(title           = 'Convergence of GPAW lattice constant error'
                ,xLabel         = 'Planewave cutoff, eV'
                ,constraint     = AND(GPAW_,LATTICEOPT_,BULK_,KPTLOW_)
                ,groupbyCols    = [JOBNAME]
                ,grouplabelFunc = name2element
                ,yCols          = [PW,JOBNAME,SQRT(AX*AX+AY*AY+AZ*AZ),STRUCTURE]
                ,yFunc          = lambda a,b,c,d:(a,errA(b,c,d))
                ,aggFunc        = converged('pw error_lattice_A',average=True)
                ,**kwargs): return BarPlot(**m(locals()))
def magmomFinal(
                title           = 'magmom'
                ,table          = final_atom_table
                ,xLabel         = 'XC'
                ,constraint     = AND(GPAW_,LATTICEOPT_,NI_)
                ,groupbyCols    = [XC]
                ,yCols          = [Sum(MAGMOM)]
                ,yFunc          = lambda x: sumJson('[%s]'%x)
                ,yLabel         = r'Magmom'
                ,splitbyCols    = [PSP]
                ,**kwargs): return BarPlot(**m(locals()))


def ni_err(title='Comparison of Magnetic Element Errors errors'
        ,groupbyCols  = [XC,PSP]
        ,splitbyCols   = [JOBNAME]
        ,constraint = AND(PW_(500),LATTICEOPT_,SPINPOL)
        ,yCols          = [Sum(MAGMOM)]
        ,yFunc          = sumJson
         ,yLabel      = r'Lattice error GMAE, $\AA$'
        ,**kwargs): return BarPlot(**m(locals()))

############
# Line Plots
#-----------

def jobsVsTime(
                title         = 'Jobs vs time'
                #,constraint   = RAND(0.05)
                ,xLabel       =    'Months'
                ,yLabel       =    '# of jobs'
                ,groupbyCols  =   [USER]
                ,xCols        = [TIMESTAMP]
                ,xFunc        = timestamp2months
                ,yCols        =    [TIMESTAMP,USER]
                ,yFunc        = jobsSinceTimestamp
                ,**kwargs): return LinePlot(**m(locals()))



def errLatVsPW(
                title         = 'Lattice constant error (GPAW) vs PW'
                ,xLabel       = 'Planewave cutoff, eV'
                ,yLabel       = r'Error in lattice constant, $\AA$'
                ,constraint   = AND(GPAW_,LATTICEOPT_)
                ,groupbyCols  = [JOBNAME]
                ,xCols        = [PW]
                ,yCols        = [JOBNAME,SQRT(AX*AX+AY*AY+AZ*AZ),STRUCTURE]
                ,yFunc        = errA
                ,grouplabelFunc = wrapper
                ,aggFunc      = avg
                ,**kwargs): return LinePlot(**m(locals()))

def errLatVsPWconv(postProcess=absdiff,**kwargs): return errLatVsPW(**m(locals()))

def errLatMagmom(constraint=AND(GPAW_,NI_,SG15_,KPTLOW_,LATTICEOPT_)
                ,groupbyCols= [MAGMOM,PSP,XC] #'magmoms psp xc'
                ,**kwargs): return errLatVsPW(**m(locals()))


def errLatVsPWAll(
                title         = 'Derivative of Convergence of Lattice constant error (GPAW) vs PW at low KPT density'
                ,xLabel       = 'Planewave cutoff, eV'
                ,yLabel       = r'$\frac{d |Error|}{d PW} , \AA / eV $'
                ,constraint   = AND(GPAW_,LATTICEOPT_,PAW_,KPTLOW_)
                ,groupbyCols  = [JOBNAME,PSP]#'job_name psp'
                ,xCols        = [PW]
                ,yCols        = [JOBNAME,SQRT(AX*AX+AY*AY+AZ*AZ),STRUCTURE]
                ,yFunc        = errA
                ,postProcess  = derivabsdiff
                ,aggFunc      = avg
                ,**kwargs): return LinePlot(**m(locals()))


def molecule(
                title         = 'Energy convergence vs PW for molecules'
                ,constraint   = AND(RELAX_,MOLECULE_)
                ,xLabel       = 'Planewave cutoff, eV'
                ,groupbyCols  = [JOBNAME,XC,DFTCODE]
                ,xCols        = [PW]
                ,yCols        = [RAWENG]
                ,yLabel       = r'$|\frac{dE}{dPW}$|'
                ,labelCols    = [FWID]
                ,fitModel     = True
                ,postProcess  = absdiff
                ,aggFunc      = avg
                ,**kwargs): return LinePlot(**m(locals()))

def hydride(
                title           = 'Energy of formation for hydrides, BEEF @ PW=500 eV'
                ,xLabel         = 'Hydrogen : Metal molar ratio'
                ,yLabel         = r'$E_{form}$ per metal atom, eV'
                ,constraint     = AND(BEEF_,QE_,BULK_,PW_(500),KSB_)
                ,join_dict      = {calc : calc__job
                                  ,atoms : atoms__job
                                  ,composition : (AND(composition.atoms_id   == FINALATOMS
                                                    ,composition.element_id == 1),'LEFT')}
                ,groupbyCols    = [JOBNAME]
                ,groupbyFunc    = lambda x: x[:2]
                ,grouplabelFunc = lambda x: x[:2]
                ,xCols          = [FLOAT(IFNULL(COUNT,0)) / (NATOMS - IFNULL(COUNT,0))]
                ,yCols          = [EFORM/(NATOMS - IFNULL(COUNT,0))]
                ,postProcess    = compose(min_y,min2)
                ,show_count     = False
                ,**kwargs): return LinePlot(**m(locals()))
"""
def hydride2(yFunc = eFormPerMetalAtom(-.7),**kwargs):return hydride(**m(locals()))

def pdh(constraint = AND(QE_,BULK_,PW_(500),KSB_,HAS_PD)
        ,legendCols=[BLANK],groupbyCols=[XC],groupbyFunc=None
        ,**kwargs): return hydride(**m(locals()))

def pdh2(yFunc = eFormPerMetalAtom(-.7),**kwargs):return pdh(**m(locals()))

def vibdeltaH(title='Effect of delta on vibration enthalpy/entropy'
                ,xCols=[DELTA]
                ,yCols= [GFORM]
                ,constraint=AND(H2_,VIB_)
                ,**kwargs): return LinePlot(**m(locals()))"""
############
# Histograms
# ---------
def pwDist(
                title           = 'Distribution of calculations'
                ,xLabel         = 'planewave cutoff, eV'
                ,xCols          = [PW]
                ,groupbyCols    = [XC]
                ,normalize      = False
                ,bins           = 20
                ,**kwargs):
    return HistPlot(**m(locals()))

def kptxDist(
                xLabel          = r'K point density in x direction, $\frac{K-points}{\AA^{-1}}$'
                ,constraint     = [QE_]
                ,xCols          = [KPTDEN_X]
                ,groupbyCols    = [SYSTYPE]
                ,normalize      = True
                ,bins           = 20
                ,**kwargs): return HistPlot(**m(locals()))
def kptyDist(xLabel=r'K point density in y direction, $\frac{K-points}{\AA^{-1}}$',xCols=[KPTDEN_Y],**kwargs): return kptxDist(**m(locals()))
def kptzDist(xLabel=r'K point density in z direction, $\frac{K-points}{\AA^{-1}}$',xCols=[KPTDEN_Z],**kwargs): return kptxDist(**m(locals()))


def q4Dist(
    xLabel='q4'
    ,constraint = AND(KSB_,LATTICEOPT_,BULK_,PW_(500),OR(FCC_,BCC_,HCP_,DIAMOND_))
    ,xCols      = [Q4]
    ,groupbyCols= [STRUCTURE]
    ,normalize  = True
    ,bins       = 20
    ,**kwargs): return HistPlot(**m(locals()))

def q6Dist(xLabel='q6',xFunc=[Q6],**kwargs): return q4Dist(**m(locals()))


def spaceGroupCrystal(
        constraint = AND(KSB_,LATTICEOPT_,PW_(500),OR(FCC_,BCC_,HCP_,DIAMOND_))
        ,xLabel= [SPACEGROUP]
        ,xCols=[SPACEGROUP]
        ,groupbyCols=[STRUCTURE]
        ,normalize = True
        ,**kwargs): return HistPlot(**m(locals()))

qDist = [q4Dist(),q6Dist()]
