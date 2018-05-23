# External modules
import json
import scipy.stats.mstats as mstatt   # type: ignore
import numpy as np   # type: ignore

# Internal modules
import CataLog.datalog.db_utils as db
from CataLog.misc.utilities   import normalize_list
from CataLog.misc.print_parse import read_on_sher
from CataLog.misc.atoms       import (nonmetals,get_keld_data,make_atoms
                                     ,get_expt_surf_energy)

################################################################################
"""
Auxillary functions useful for manipulating data for plotting
"""
######################
# PostProcessing Funcs
# --------------------
def min2(xylns):
    """DON'T include a line if it has only one point"""
    return [] if len(set([x[0] for x in xylns])) < 2 else xylns

def min_y(xylns):
    """
    keep the data point with the minimum y value
    We can't do this with a simple aggFunc (min) because we would lose label information
    """
    output,xs  = [],[]
    for i in range(len(xylns)):
        x,y,l,n = xylns[i]
        if x not in xs:
            xs.append(x)
            output.append(xylns[i])
        elif y < output[-1][1]:
            output[-1]=xylns[i]

    return output

def absolute(xylns): return [(x,abs(y),l,n) for x,y,l,n in xylns]

def absdiff(xylns):
    """Take the last y datapoint of a line to be 0, all previous y values replaced with distance to final ('converged') value"""
    if len(set([x[0] for x in xylns])) < 2: return []
    xlist,ylist,llist,nlist =zip(*xylns)
    return zip(xlist,[abs(y - ylist[-1]) for y in ylist],llist,nlist)

def derivabsdiff(xylns): return deriv(absdiff(xylns)) #derivative of the above 'absdiff' curve

def deriv(xylns):
    if len(set([x[0] for x in xylns])) < 3: return []
    xlist,ylist,llist,nlist =zip(*xylns)
    dydx = dict(derivxy(xlist,ylist))
    return [(x,dydx[x],l,n) for x,y,l,n in xylns if x in dydx.keys()]

def derivxy(x,y):
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
    return zip(x[1:-1],dydx)


##############################################
# Groupby funcs (note input is always a tuple)
#---------------------------------------------
def num2metalstoich(numstr):
    """
    Use when groupbyCols = 'final.numbers'. Useful when grouping the hydrides of a metal
    """
    if numstr is None: return None
    num = json.loads(numstr)
    output =  tuple(normalize_list([n for n in num if n not in nonmetals]))

    return output

#########
# X funcs
#--------
def mol_frac_per_nonmetal(symb):
    """
    Use when groupbyCols = 'numbers'.
    """
    import ase.data   # type: ignore
    num = ase.data.chemical_symbols.index(symb)
    def count(numstr):
        if numstr is None: return None
        nums = json.loads(numstr)
        try:  return nums.count(num)/float(len([x for x in nums if x not in nonmetals]))
        except ZeroDivisionError: return None
    return count

def timestamp2months(ts): return (ts / float((3600*24*30))) -581.7

# #############################
# Y Funcs :: (a,b,c,...)->Float
# -----------------------------

def parseBOA(key):
    keyDict = {'cn':0,'q2':1,'q4':2,'q6':3}
    index = keyDict[key]
    def parse_boa(boajson):
        if boajson is None: return None
        return json.loads(boajson)[0][index]
    return parse_boa

def jobsSinceTimestamp(ts,user):
    return db.sqlexecute('SELECT COUNT (timestamp) from job where user=\'%s\' and timestamp <= %d'%(user,ts))[0][0]

def eFormPerMetalAtom(rhe=0):
    def f(eForm,numstr):
        if eForm is None: return None
        else:
            try:
                nums = json.loads(numstr)
                e  = eForm + rhe * nums.count(1)
                return e/len([x for x in nums if x not in nonmetals])
            except ZeroDivisionError: return None # diamond carbon
    return f
def sumJson(x): return abs(sum(json.loads(x))) if x is not None else None

def errA(job_name,lattice_parameter,structure_ksb):
    """Calculations done on primitive cells - need to convert to unit cell"""
    if job_name is None or structure_ksb is None: return None

    if    structure_ksb in ['hcp','hexagonal']:    multFactor = 1
    elif  structure_ksb == 'bcc':                 multFactor = 3**(0.5)/2.
    else:                                        multFactor = 2**(-0.5) #trigonal-shaped primitive cells

    exptA = get_keld_data(job_name,'lattice parameter')
    if exptA is None: return None

    return lattice_parameter - exptA * multFactor

def errBM(name,bm):
    exptBM = get_keld_data(name,'bulk modulus')
    return bm - exptBM

def errSE(job_name,surface_energy):
    if surface_energy is None or job_name is None: return None
    e = get_expt_surf_energy(job_name)
    if e is None: return None
    return surface_energy - e #eV/A^2

def bulkmodQuadfit(storage_directory):
    try:              return json.loads(read_on_sher(storage_directory+'result.json'))['bfit']
    except KeyError: pass

def getSpacegroup(n,c,p):
    import pymatgen.io.ase               as pmgase   # type: ignore
    import pymatgen.symmetry.analyzer as psa   # type: ignore

    pmg = pmgase.AseAtomsAdaptor().get_structure(make_atoms(n,c,p))
    return psa.SpacegroupAnalyzer(pmg).get_space_group_number()


# #########################################
# Label / Legend Funcs :: (a,...) -> String
# -----------------------------------------

def name2element(name):
    if name in [None,'']: return 'X'
    return name.split('_')[0].split('-')[0] # 'Li-bcc_1,1,0_3x3x4' -> 'Li'
def kptLowHigh(kptden): return 'kpt density '+('<' if kptden < 4 else '>')+r' 4 $\frac{Kpt}{\AA^{-1}}$'
def wrapper(*tup): return '_'.join([str(x) for x in tup])

##################################################
# Bar Aggregating Function [(a,b,c,...)] -> Float
#---------------------------------------------
def avg(x):      return sum(x)/len(x)
def absavg(x):   return sum(map(abs,x))/len(x)
def RMS(xs):      return (avg([x**2 for x in xs]))**(0.5)
def gMeanAbs(xs):
    preProcessed = [abs(x) for x in xs if x!=0]
    return mstatt.gmean(preProcessed)

def variance(xs): raise NotImplementedError


def converged(ycols,average=False):
    xcol,ycol = ycols.split()

    derivConvDict={'pw':
                    {'raw_energy':        (0.001,200)
                    ,'error_BM':        (100,200)
                    ,'error_lattice_A':    (0.001,300)}}
    dydxMax,xRange = derivConvDict[xcol][ycol]  # threshold for max |dy/dx| /// range (from last data point) over which |dy/dx| must be decreasing and beneath threshold

    def convergenceFunc(xys):

        #Uses three-point finite difference estimate of derivative: http://www.m-hikari.com/ijma/ijma-password-2009/ijma-password17-20-2009/bhadauriaIJMA17-20-2009.pdf
        #Tests whether or not yFunc derivative has a low magnitude and is decreasing over a certain range
        print('\t\t\tTesting for convergence between %s and %s'%(xcol,ycol))

        if average: xy = [(x,avg([yy for xx,yy in xys if x ==xx])) for x in sorted(dict(xys).keys())]
        if len(xy) < 5: print("\t\t\t\tNot enough data points"); return 0 # not converged

        def dydxTest(xdydxlist):
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
