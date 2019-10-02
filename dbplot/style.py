# External Modules
from typing import Tuple,Optional

################################################################################
class Style(object):
    def __init__(self,style_tuple:Tuple[str,str,str])->None:
        self.line   = style_tuple[0]
        self.color  = style_tuple[1]
        self.marker = style_tuple[2]
################################################################################
styleDict = {
    'H': ('solid','black','o')       ,'Li': ('solid','purple','o')       ,'Be':('solid','mediumaquamarine','o')
    ,'B':('solid','pink','o')        ,'C':('dash','grey','o')          ,'N':('solid','blue','o')
    ,'O':('solid','red','o')         ,'F':('dot','forestgreen','o')    ,'Na':('dot','purple','o')
    ,'Mg':('solid','lightcoral','x') ,'Al':('solid','firebrick','o')     ,'Si':('solid','palevioletred','o')
    ,'P':('solid','orange','o')      ,'S':('solid','red','x')            ,'Cl':('dashdot','green','o')
    ,'K':('solid','purple','*')      ,'Ca':('solid','lightsalmon','o')   ,'Sc':('dot','grey','o')
    ,'Ti':('solid','grey','+')       ,'V':('dot','blue','o')           ,'Cr':('solid','cyan','o')
    ,'Mn':('dashdot','purple','x')    ,'Fe':('solid','darkred','o')       ,'Co':('solid','pink','x')
    ,'Ni':('dash','green','o')     ,'Cu':('dot','brown','o')         ,'Zn':('solid','indigo','x')
    ,'Ga':('solid','pink','o')       ,'Ge':('dash','lightblue','o')    ,'As':('solid','fuchsia','+')
    ,'Se':('solid','turquoise','o')  ,'Br':('solid','azure','o')         ,'Rb':('solid','black','o')
    ,'Sr':('solid','olive','o')      ,'Y':('solid','plum','o')           ,'Zr':('solid','palevioletred','o')
    ,'Nb':('solid','aqua','o')       ,'Mo':('solid','khaki','o')         ,'Tc':('solid','green','o')
    ,'Ru':('solid','lime','o')       ,'Rh':('solid','teal','o')          ,'Pd':('solid','grey','o')
    ,'Ag':('solid','silver','o')     ,'Cd':('solid','purple','o')        ,'In':('solid','blue','o')
    ,'Sn':('dashdot','green','o')     ,'Sb':('solid','red','o')           ,'Te':('solid','plum','o')
    ,'I':('solid','red','o')         ,'Cs':('solid','orange','o')        ,'Ba':('solid','tan','o')
    ,'Os':('solid','pink','o')       ,'Ir':('solid','green','o')         ,'Pt':('solid','blue','o')
    ,'Au':('solid','gold','o')       ,'Pb':('dot','brown','o')

    ,'H2':('solid','black','o')      ,'O2':('solid','red','o')           ,'N2':('solid','green','o')
    ,'F2':('solid','purple','o')     ,'Br2':('solid','brown','o')        ,'CH4':('solid','blue','o')
    ,'Cl2':('solid','pink','o')      ,'H2O':('dot','blue','x')         ,'CO2':('dot','brown','x')
    ,'CO':('dot','red','x')

    ,'mBEEF':('solid','black','o')   ,'PBE':('solid','red','o')          ,'BEEF':('solid','blue','o')
    ,'RPBE':('solid','green','o')

    ,'bulkmod':('solid','red','o') ,'relax':('solid','blue','o')         ,'latticeopt':('solid','black','o')
    ,'vib':('solid','green','o')   ,'vcrelax':('solid','purple','o')


    ,'hexagonal': ('solid','black','o') ,'fcc':('solid','red','o') ,'bcc':('solid','blue','o')
    ,'diamond':('solid','green','o')

    ,'sg15':('solid','black','o') ,'paw':('solid','red','o') ,'gbrv15pbe':('solid','blue','o')
    ,'H_PBE':('solid','black','o'),'H_LDA':('dot','black','o'),'O_PBE':('solid','red','o'),'O_LDA':('dot','red','o'),
    'N_PBE':('solid','blue','o'),'N_LDA':('dot','blue','o')
    ,'':('solid','red','o')}
################################################################################
# Helper functions
##################
def getStyle(key:str)->Optional[Style]:
    return Style(styleDict[key]) if key in styleDict.keys() else None

def str2int(lst:str)->int:
    return sum(set(map(ord,lst)))

################################################################################
# Main Exported Function
########################
def mkStyle(label : str)->Style:
    """
    Associate every legend label with a particular (consistent) line style
    """
    sty = getStyle(label)
    if sty:
        return sty
    else:
        filtered = str(label).split('_')[0].split('solid')[0] # strip label to its essentials
        sty = getStyle(filtered)
        if sty:
            return sty
        else: # last resort, a 'random' (but deterministic) label
            all_stys = list(styleDict.values())
            sty_ind  = str2int(str(label)) % len(styleDict)
            return Style(all_stys[sty_ind])



if __name__ == '__main__':
    import pdb; pdb.set_trace()
