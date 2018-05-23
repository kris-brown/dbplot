# Typing Modules
import typing as typ

#External Modules
import json,random
import sql                                                  # type: ignore
from sql           import As,Table,Join,Flavor,Literal      # type: ignore
from sql.operators import In,And,Or,Not,Concat,Mod,Like     # type: ignore
from sql.functions import Function,Substring,Round,Random   # type: ignore
from sql.aggregate import Count,Sum,Avg,Max,Min             # type: ignore

Flavor.set(Flavor(paramstyle='qmark')) # python-sql internal setting
################################################################################

#####################
# Auxillary Functions
#--------------------
def joiner_simple(first_table : sql.Table
                 ,dictionary  : dict
                 ) -> sql.Join:
    """
    Concisely express a join
    This function is needed because Mike's joiner breaks when your join condition
    is itself a list (i.e. joining on 2+ conditions)

    New format for specifying join type: dictionary value is a TUPLE (c,t)
    """
    output = first_table
    for t,c in dictionary.items():
        if isinstance(c,tuple):            c,typ = c
        else: typ = 'INNER'
        output=Join(output,t,condition=c,type_ = typ)
    return output

def joiner(first_table      : sql.Table
          ,subsequent_dict  : dict
          ,join_type        : str           = 'INNER'
          ) -> sql.Join:
    """
    Concisely express a join

    no longer supports 'subsequent_dict' being a list
    """
    output = first_table

    for t,c in subsequent_dict.items():
        if isinstance(c,list) and len(c)>1:
            output=Join(output,t,condition=c[0], type_ = c[1])
        else:
            output=Join(output,t,condition=c, type_ = join_type)
    return output

def join_joins(first_join   : typ.Any
              ,second_join  : typ.Any
              ,condition    : typ.Any
              ,join_type    : str       =  'INNER'
              ) -> typ.Any:
    """
    Typing was probably done completely wrong
    """
    from CataLog.misc.utilities import merge_dicts
    first_main_table, first_dictionary = unpack_joins(first_join)
    second_main_table, second_dictionary  = unpack_joins(second_join)
    new_condition = {second_main_table : [condition, join_type]}
    return joiner(first_main_table, [new_condition,first_dictionary, second_dictionary])  # type: ignore

def unpack_joins(joined_tables : typ.Any
                 ) -> typ.Any:
    """
    Turns a join statement into the input used to create it
    """
    from CataLog.misc.utilities import merge_dicts
    left        = joined_tables.left
    right       = joined_tables.right
    condition   = joined_tables.condition
    join_type   = joined_tables.type_
    if isinstance(left,Table) and isinstance(right,Table):
        return [left, {right:[condition, join_type]}]
    elif isinstance(left,Table):
        output = unpack_joins(right)
        output[1] = merge_dicts([output[1], {left: [condition, join_type]}])
        return output
    else:
        output = unpack_joins(left)
        output[1] = merge_dicts([output[1], {right: [condition, join_type]}])
        return output


def concat(*args : typ.Any) -> sql.operators.Concat:
    """
    Concat a list of objects
    """
    output = Concat(*args[-2:])
    for a in reversed(args[:-2]): output=Concat(a,output)
    return output

def AND(*args : typ.Any) -> sql.operators.And:
    args = list(filter(None,args)) # type: ignore
    if len(args)==0: return None
    return And(args)

def OR(*args : typ.Any) -> sql.operators.Or:
    # args = [a for a in args if a not in [None,[]]]  # type: ignore
    # if len(args)==0: return None
    return Or(args)
#############
# Definitions
#------------
class UDF(Function):         __slots__ = () ; _function = 'user_defined_function'
class ABS(Function):         __slots__ = () ; _function = 'abs'
class SQRT(Function):        __slots__ = (); _function = 'sqrt'
class SUBSTR(Function):      __slots__ = () ; _function = 'substr'
class IFNULL(Function):      __slots__ = () ; _function = 'ifnull'
class GROUPCONCAT(Function): __slots__ = () ; _function = 'group_concat'
class DISTINCT(Function):    __slots__ = () ; _function = 'Distinct'
class IIF(Function):         __slots__ = () ; _function = 'IIF'
class FLOAT(Function):         __slots__ = () ; _function = '1.0*'

#########
# Tables
#-------
atom         = Table('atom')
atoms        = Table('atoms')
cell         = Table('cell')
calc         = Table('calc')
job          = Table('job')
composition  = Table('composition')
element      = Table('element')
refstoich    = Table('refstoich')
refeng       = Table('refeng')


atom2       = Table('atom')
atoms2      = Table('atoms')
cell2       = Table('cell')
calc2       = Table('calc')
job2        = Table('job')
element2    = Table('element')
refstoich2  = Table('refstoich')
refeng2     = Table('refeng')

final_table_joins = {calc  : calc.id  == job.calc_id
                    ,atoms : atoms.id == job.finalatoms
                    ,cell  : cell.id  == atoms.cell_id}

finalatom_table_joins = {calc  : calc.id  == job.calc_id
                        ,atoms : atoms.id == job.finalatoms
                        ,cell  : cell.id  == atoms.cell_id
                        ,atom  : atom.atoms_id == job.finalatoms}


final_table      = joiner(job,final_table_joins)
final_atom_table = joiner(job,finalatom_table_joins)

#Parent Child Table
parent_job          = Table('job')
parent_atoms        = Table('atoms')
parent_cell         = Table('cell')
parent_calc         = Table('calc')


parent_child_table  = joiner(
                            joiner(
                                joiner(job
                                ,{parent_job          : [job.parent      == parent_job.storage_directory, 'LEFT']})
                                ,{calc                : [calc.id         == job.calc_id,                  'INNER']
                                ,atoms                : [atoms.id        == job.finalatoms,               'INNER']
                                ,cell                 : [cell.id         == atoms.cell_id,                'INNER']
                                ,parent_calc          : [parent_calc.id  == parent_job.calc_id,            'LEFT']
                                ,parent_atoms         : [parent_atoms.id == parent_job.finalatoms,         'LEFT']}
                                )
                            ,{parent_cell          : [parent_cell.id   == parent_atoms.cell_id, 'LEFT']}
                        )

def get_table_names(joined_tables : sql.Join) -> typ.List[str]:
    left = joined_tables.left
    right = joined_tables.right
    if isinstance(left,sql.Table) and isinstance(right,sql.Table):
        return [left._name, right._name]
    elif isinstance(left,sql.Table):
        return [left._name]+get_table_names(right)
    else:
        return get_table_names(left)+[right._name]

td = {'atom':atom,'atoms':atoms,'cell':cell,'calc':calc,'job':job # TABLE
     ,'refeng':refeng,'composition':composition}                                            # DICTIONARY

job2 = Table('job')
#################
# Join conditions
#---------------
atom__job           = atom.atoms_id == job.finalatoms
atom__atoms         = atom.atoms_id == atoms.id
atom__refstoich     = atom.number   == refstoich.reference_element
atom__element       = atom.number   == element.id

calc__job           = calc.id       == job.calc_id
calc__refeng        = calc.id       == refeng.calc_id

atoms__job          = atoms.id      == job.finalatoms
atoms__cell         = cell.id       == atoms.cell_id
atom__refeng        = atom.number   == refeng.element_id

atoms__composition  = atoms.id               == composition.atoms_id
composition__job    = composition.atoms_id   == job.finalatoms
composition__refeng = composition.element_id == refeng.element_id

init_or_finalatoms  = OR(job.finalatoms  == atoms.id, job.initatoms   == atoms.id)
init_or_finalatoms2 = OR(job.finalatoms  == atom.atoms_id
                        ,job.initatoms   == atom.atoms_id)

atom__composition   = AND(atom.atoms_id  == composition.atoms_id
                         ,atom.number    == composition.element_id)

###############
# Col shortcuts
# -------------
JOB         = job.id
DELETED     = job.deleted
USER        = job.user
JOBNAME     = job.job_name
TIMESTAMP   = job.timestamp
WORKDIR     = job.working_directory
STORDIR     = job.storage_directory
CALC_ID     = job.calc_id
INITATOMS   = job.initatoms
FINALATOMS  = job.finalatoms
####
JOBTYPE     = job.job_type
KPTDEN_X    = job.kptden_x
KPTDEN_Y    = job.kptden_y
KPTDEN_Z    = job.kptden_z
PARENT      = job.parent
BULKMODULUS = job.bulk_modulus
ADSORBATES  = job.adsorbates
STRJOB_EXACT = job.strjob_exact
STRJOB_GRAPH = job.strjob_graph

CHARGEMOL   = job.chargemol
GRAPH       = job.graph
FWID        = job.fwid
BLANK       = job.blank
RAWENG      = job.raw_energy
SURFENG     = job.surface_energy
RAWG        = job.raw_g
REFJOB      = job.refjob
EFORM       = job.eform
GFORM       = job.gform
EADS        = job.e_ads
GADS        = job.g_ads
VIBFREQS    = job.vib_freqs
####################

ATOM        = atom.id
IND         = atom.ind
NUMBER      = atom.number
X           = atom.x
Y           = atom.y
Z           = atom.z
CONSTRAINED = atom.constrained
MAGMOM      = atom.magmom
TAG         = atom.tag
ATOMSID     = atom.atoms_id
ADSORBATE   = atom.adsorbate
####
COORDNUM    = atom.coordination_number
Q4          = atom.q4
Q6          = atom.q6

####################
ATOMS       = atoms.id
CELLID      = atoms.cell_id
###
NATOMS      = atoms.natoms
NATOMS_CONSTRAINED = atoms.natoms_constrained
SYSTYPE     = atoms.system_type
POINTGROUP  = atoms.pointgroup
SPACEGROUP  = atoms.spacegroup
STRUCTURE   = atoms.structure
FACET       = atoms.facet
SURFACEAREA = atoms.surface_area
VOLUME      = atoms.volume
HAS_ADS     = atoms.has_ads
SYMSLAB     = atoms.sym_slab
ADS_NELEMS  = atoms.ads_nelems
NELEMS      = atoms.nelems
####################
CALC  = calc.id
DFTCODE = calc.dftcode
XC      = calc.xc
PW      = calc.pw
KPTS    = calc.kpts
FMAX    = calc.fmax
PSP     = calc.psp
ECONV   = calc.econv
XTOL    = calc.xtol
STRAIN  = calc.strain
DW      = calc.dw
SIGMA   = calc.sigma
NBANDS  = calc.nbands
MIXING  = calc.mixing
NMIX    = calc.nmix
GGA     = calc.gga
LUSE_VDW = calc.luse_vdw
ZAB_VDW  = calc.zab_vdw
NELMDL   = calc.nelmdl
GAMMA    = calc.gamma
DIPOL    = calc.dipol
ALGO     = calc.algo
IBRION   = calc.ibrion
PREC     = calc.prec
IONIC_STEPS = calc.ionic_steps
LREAL = calc.lreal
LVHAR = calc.lvhar
DIAG = calc.diag
SPINPOL = calc.spinpol
DIPOLE  = calc.dipole
MAXSTEP = calc.maxstep
DELTA  = calc.delta
MIXINGTYPE = calc.mixingtype
BONDED_INDS = calc.bonded_inds
ENERGY_CUTOFF = calc.energy_cut_off
STEP_SIZE = calc.step_size
SPRINGS = calc.springs
####################
CELL  = cell.id
AX    = cell.ax
AY    = cell.ay
AZ    = cell.az
BX    = cell.bx
BY    = cell.by
BZ    = cell.bz
CX    = cell.cx
CY    = cell.cy
CZ    = cell.cz
####################
#####
ELEMENT       = element.id
REFSPACEGROUP = element.reference_spacegroup
REFENG        = refeng.id
ALL_EREF      = refeng.all_eref
ALL_GREF      = refeng.all_gref
EREF          = refeng.eref
GREF          = refeng.gref
EATOM         = refeng.eatom
GATOM         = refeng.gatom
#############
REFSTOICH     = refstoich.id
REF_ELM       = refstoich.reference_element
COMPONENT_ELM = refstoich.component_element
COMPWEIGHT    = refstoich.component_weight
TOT_COMPS     = refstoich.total_components
########
COMPOSITION   = composition.id
HAS           = composition.has
CONST_HAS     = composition.const_has
COUNT         = composition.count
CONST_COUNT   = composition.const_count
ADS_COUNT     = composition.ads_count
FRAC          = composition.frac
CONST_FRAC    = composition.const_frac


######################
# Constraint shortcuts
# --------------------
JOB_     = lambda x: JOB   == x
ATOM_    = lambda x: ATOM  == x
ATOMS_   = lambda x: ATOMS == x
CALC_    = lambda x: CALC  == x

NUMBER_    = lambda x: NUMBER    == x

ADSORBATE_ = lambda x: ADSORBATE == x
ADSORBATES_ = lambda x: ADSORBATES == x
BARE_ = ADSORBATES_('[]') # type: ignore

FWID_    = lambda x: FWID == x
FWIDS_   = lambda xs: In(FWID,tuple(xs))

STRJOB_EXACT_ = lambda x: STRJOB_EXACT == x
STRJOB_GRAPH_ = lambda x: STRJOB_GRAPH == x
GRAPH_        = lambda x: GRAPH == x
STORDIR_      = lambda x: STORDIR == x
JOBNAME_      = lambda x: JOBNAME == x

USER_    = lambda x: USER == x
KSB_     = USER_('ksb')                                     # type: ignore
MSTATT_  = USER_('mstatt')                                  # type: ignore

def JOBTYPE_(x): return JOBTYPE == x                        # type: ignore
LATTICEOPT_ = JOBTYPE_('latticeopt')                        # type: ignore
BULKMOD_    = JOBTYPE_('bulkmod')                           # type: ignore
VIB_        = JOBTYPE_('vib')                               # type: ignore
VCRELAX_    = JOBTYPE_('vcrelax')                           # type: ignore
RELAX_      = JOBTYPE_('relax')                             # type: ignore
DOS_        = JOBTYPE_('dos')                               # type: ignore
NEB_        = JOBTYPE_('neb')                               # type: ignore
XCCONTRIBS_ = JOBTYPE_('xc')                                # type: ignore

RELAXORLAT_  = OR(LATTICEOPT_,VCRELAX_,RELAX_)

def NATOMS_(x): return NATOMS == x                          # type: ignore
def NATOMS_CONSTRAINED_(x): return NATOMS_CONSTRAINED == x  # type: ignore

PW_ = lambda x: PW==x                                       # type: ignore
def XC_(x): return XC == x                                  # type: ignore
PBE_ = XC_('PBE')                                           # type: ignore
RPBE_ = XC_('RPBE')                                         # type: ignore
BEEF_ = XC_('BEEF')                                         # type: ignore
MBEEF_ = XC_('mBEEF')                                       # type: ignore

def DFTCODE_(x): return DFTCODE==x                          # type: ignore
GPAW_ = DFTCODE_('gpaw')                                    # type: ignore
QE_ = DFTCODE_('quantumespresso')                           # type: ignore
VASP_ = DFTCODE_('vasp')                                    # type: ignore

def PSP_(x): return PSP == x                                # type: ignore
SG15_   = PSP_('sg15')                                      # type: ignore
GBRV_   = PSP_('gbrv15pbe')                                 # type: ignore
PAW_    = PSP_('paw')                                       # type: ignore
OLDPAW_ = PSP_('oldpaw')                                    # type: ignore

KPTS_    = lambda x: KPTS==x                                # type: ignore
KPTLOW_  = KPTDEN_X < 4
KPTHIGH_ = Not(KPTLOW_)

ECONV_ = lambda x: ECONV == x
MIXING_ = lambda x: MIXING == x
NMIX_   = lambda x: NMIX == x
FMAX_   = lambda x: FMAX == x
SPINPOL_ = lambda x: SPINPOL==x
PARENT_  = lambda x: PARENT == x

def STRUCTURE_(x): return STRUCTURE == x                    # type: ignore
HCP_     = STRUCTURE_('hexagonal')                          # type: ignore
FCC_     = STRUCTURE_('fcc')                                # type: ignore
BCC_     = STRUCTURE_('bcc')                                # type: ignore
DIAMOND_ = STRUCTURE_('diamond')                            # type: ignore

def SYSTYPE_(x): return SYSTYPE == x                        # type: ignore
SURFACE_     = SYSTYPE_('surface')                          # type: ignore
BULK_        = SYSTYPE_('bulk')                             # type: ignore
MOLECULE_    = SYSTYPE_('molecule')                         # type: ignore

def facet(x): return FACET == json.dumps(x)                 # type: ignore
F111_ = facet([1,1,1])                                      # type: ignore
F110_ = facet([1,1,0])                                      # type: ignore
F001_ = facet([0,0,1])                                      # type: ignore

cp = {FCC_:F111_, BCC_:F110_, HCP_:F001_}

CLOSEPACKED_ = Or([And([st,f]) for st,f in cp.items()])


relevent_atoms = [1,3,4,6,7,8,9,11,12,13,14,16,17] \
                    + list(range(19,36))+list(range(37,52))+[55,56]+list(range(72,80))

H2_ = REFJOB == 1
LI_ = REFJOB == 3
BE_ = REFJOB == 4
CO_ = REFJOB == 6
N2_ = REFJOB == 7
H2O_= REFJOB == 8
F2_ = REFJOB == 9
NA_ = REFJOB == 11
MG_ = REFJOB == 12
AL_ = REFJOB == 13
SI_ = REFJOB == 14
CL2_= REFJOB == 17
K_  = REFJOB == 19
CA_ = REFJOB == 20
SC_ = REFJOB == 21
TI_ = REFJOB == 22
V_  = REFJOB == 23
CR_ = REFJOB == 24
MN_ = REFJOB == 25
FE_ = REFJOB == 26
CO_ = REFJOB == 27
NI_ = REFJOB == 28
CU_ = REFJOB == 29
ZN_ = REFJOB == 30
GE_ = REFJOB == 32
BR2_= REFJOB == 35
RB_ = REFJOB == 37
SR_ = REFJOB == 38
Y_  = REFJOB == 39
ZR_ = REFJOB == 40
NB_ = REFJOB == 41
MO_ = REFJOB == 42
TC_ = REFJOB == 43
RU_ = REFJOB == 44
RH_ = REFJOB == 45
PD_ = REFJOB == 46
AG_ = REFJOB == 47
SN_ = REFJOB == 50
CS_ = REFJOB == 55
BA_ = REFJOB == 56
W_  = REFJOB == 74
RE_ = REFJOB == 75
OS_ = REFJOB == 76
IR_ = REFJOB == 77
PT_ = REFJOB == 78
AU_ = REFJOB == 79


###################
cell_arg = As(concat('[[',AX,',',AY,',',AZ,'],['
                         ,BX,',',BY,',',BZ,'],['
                         ,CX,',',CY,',',CZ,']]'),'cell')

atoms_args = [As(concat('[',GROUPCONCAT(NUMBER),']'),'numbers')             # numbers
              ,As(concat('[[',GROUPCONCAT(X),'],['
                          ,GROUPCONCAT(Y),'],['
                          ,GROUPCONCAT(Z),']]'),'posT')                     # positions (transpose)
              ,cell_arg # cell
              ,As(concat('[',GROUPCONCAT(MAGMOM),']'),'magmoms')            # magmoms
              ,As(concat('[',GROUPCONCAT(CONSTRAINED),']'),'constrained')]  # constrained


def RAND_(x : float) -> typ.Any:
    """Random fraction of data, chosen by Bool(id + <number> % <number>)"""
    x = round(x,2)
    r = random.randint(0,100000)
    assert 0 <= x <= 1

    if   x==1:         return '1'
    elif x==0:         return 'not 1'
    elif x < 0.5:   LOW = True
    else:
     x      = 1 - x
     LOW = False

    harmonic = map(lambda y: 1./y,range(1,105))

    error = float('inf')
    for i,h in enumerate(harmonic):
        diff = x-h
        if abs(diff)>error:
            if LOW: return Not(Mod(JOB+r,i))
            else:   return Mod(JOB+r,i)
        else: error = abs(diff)
    raise ValueError('Pick a more reasonable value for RAND than'+str(x))


##Misc Joins#
atoms_tables = joiner(atom,{atoms:atom__atoms,cell:atoms__cell})
