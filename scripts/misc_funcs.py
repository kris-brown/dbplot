# External modules
from typing import List,Tuple,Optional as O,Callable as C
import json
import scipy.stats.mstats as mstatt   # type: ignore
import numpy as np   # type: ignore
from math import log 

################################################################################
"""
Auxillary functions useful for manipulating data for plotting


TO DO: USE NUMPY.GRADIENT FOR DERIVATIVES?

>>> x
[1, 2, 5, 10, 11]
>>> y
[1, 8, 20, 40, 44]
>>> y = [4,8,20,40,44]
>>> gradient(y)/gradient(x)
array([4., 4., 4., 4., 4.])

"""
######################
# PostProcessing Funcs
# --------------------
def min2(xylns:List[tuple])->List[tuple]:
    """
    DON'T include a line if it has only one point
    """
    return [] if len(set([x[0] for x in xylns])) < 2 else xylns

def min_y(xylns:List[tuple])->List[tuple]:
    """
    keep the data point with the minimum y value
    We can't do this with a simple aggFunc (min) because we would lose label information
    """
    output,xs  = [],[] # type: List[tuple],List[float]
    for i in range(len(xylns)):
        x,y,l,n = xylns[i]
        if x not in xs:
            xs.append(x)
            output.append(xylns[i])
        elif y < output[-1][1]:
            output[-1]=xylns[i]

    return output

def absolute(xylns:List[tuple])->List[tuple]:
    return [(x,abs(y),l,n) for x,y,l,n in xylns]

def absdiff(xylns:List[tuple])->List[tuple]:
    """
    Take the last y datapoint of a line to be 0, all previous y values replaced with distance to final ('converged') value
    """
    if len(set([x[0] for x in xylns])) < 2: return []
    xlist,ylist,llist,nlist =zip(*xylns)
    return list(zip(xlist,[abs(y - ylist[-1]) for y in ylist],llist,nlist))

def derivabsdiff(xylns:List[tuple])->List[tuple]:
    return deriv(absdiff(xylns)) #derivative of the above 'absdiff' curve

def deriv(xylns:List[tuple])->List[tuple]:
    if len(set([x[0] for x in xylns])) < 3: return []
    xlist,ylist,llist,nlist =zip(*xylns)
    dydx = dict(derivxy(xlist,ylist))
    return [(x,dydx[x],l,n) for x,y,l,n in xylns if x in dydx.keys()]

def derivxy(x:List[float],y:List[float])->List[Tuple[float,float]]:
    """
    Converts x and y vectors (length N) to a pair of X and dYdX vectors (length N-2)
    Uses three-point finite difference estimate of derivative: http://www.m-hikari.com/ijma/ijma-password-2009/ijma-password17-20-2009/bhadauriaIJMA17-20-2009.pdf
    """
    dydx = []
    if len(x) != len(set(x)): raise ValueError("EQ constraint poorly chosen for derivative: multiple y values per x value:"+str(zip(x,y))) ; return 0

    for i in range(1,len(x)-1): #all values except for first and last
        h1,h2= float(x[i]-x[i-1]), float(x[i+1]-x[i])
        sumH, diffH, prodH, quotH = h1+h2, h1-h2, h1*h2, h1/h2
        f0,     f1,     f2           = y[i-1], y[i], y[i+1]
        dydx.append(quotH/sumH*f2 - 1./(sumH*quotH)*f0 - diffH/(prodH)*f1)
    return list(zip(x[1:-1],dydx))


##############################################
# Groupby funcs (note input is always a tuple)
#---------------------------------------------


def timestamp2months(ts:int)->float:
    return (ts / float((3600*24*30))) -581.7



def sumJson(x:str)->float:
    return abs(sum(json.loads(x))) if x is not None else None


# #########################################
# Label / Legend Funcs :: (a,...) -> String
# -----------------------------------------

def name2element(name:str)->str:
    if name in [None,'']: return 'X'
    return name.split('_')[0].split('-')[0] # 'Li-bcc_1,1,0_3x3x4' -> 'Li'
def kptLowHigh(kptden:float)->str:
    return 'kpt density '+('<' if kptden < 4 else '>')+r' 4 $\frac{Kpt}{\AA^{-1}}$'
def wrapper(*tup:Tuple)->str:
    return '_'.join([str(x) for x in tup])

##################################################
# Bar Aggregating Function [(a,b,c,...)] -> Float
#---------------------------------------------
def avg(xs:list)->float:
    return sum(xs)/len(xs)
def avgNone(xs:list)->float:
    xs_ = [x for x in xs if x is not None]
    return sum(xs_)/len(xs_)
def absavg(xs:list)->float:
    return float(sum(map(abs,xs)))/len(xs)
def RMS(xs:list)->float:
    return (avg([x**2 for x in xs]))**(0.5)
def gMeanAbs(xs:list)->float:
    preProcessed = [abs(x) for x in xs if x!=0]
    return mstatt.gmean(preProcessed)

def variance(xs:list)->float:
    raise NotImplementedError


def converged(ycols:str,average:bool=False)->C:
    xcol,ycol = ycols.split()

    derivConvDict={'pw':
                    {'raw_energy':        (0.001,200)
                    ,'error_BM':        (100,200)
                    ,'error_lattice_A':    (0.001,300)}}
    dydxMax,xRange = derivConvDict[xcol][ycol]  # threshold for max |dy/dx| /// range (from last data point) over which |dy/dx| must be decreasing and beneath threshold

    def convergenceFunc(xys:list)->float:

        #Uses three-point finite difference estimate of derivative: http://www.m-hikari.com/ijma/ijma-password-2009/ijma-password17-20-2009/bhadauriaIJMA17-20-2009.pdf
        #Tests whether or not yFunc derivative has a low magnitude and is decreasing over a certain range
        print('\t\t\tTesting for convergence between %s and %s'%(xcol,ycol))

        if average: xy = [(x,avg([yy for xx,yy in xys if x ==xx])) for x in sorted(dict(xys).keys())]
        if len(xy) < 5: print("\t\t\t\tNot enough data points"); return 0 # not converged

        def dydxTest(xdydxlist:list)->bool:
            for x,dydx in xdydxlist:
                above = -dydxMax <= dydx
                below = dydx <= dydxMax/10.     # allow *tiny* positive derivatives in case line is basically flat
                if not above or not below: return False
            return True

        xs,ys = zip(*xy)
        xmax = xs[-2]

        xdydxs = derivxy(xs,ys)

        for i,(x,dydx) in enumerate(xdydxs):
            if dydxTest(xdydxs[i:]): return x if xmax-x >= xRange else 0
        print('\t\t\t\t\tDerivative not below threshold (%s-%s) within range (%s-%s)'%(-dydxMax,0.0001,xmax-xRange,xmax))
        return 0
    return convergenceFunc
