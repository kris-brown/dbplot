from typing import Tuple

labelDict = {
    'H': ('-','black','o')      ,'Li': ('-','purple','o')         ,'Be':('-','mediumaquamarine','o')
    ,'B':('-','pink','o')        ,'C':('--','grey','o')           ,'N':('-','blue','o')
    ,'O':('-','red','o')         ,'F':(':','forestgreen','o')    ,'Na':(':','purple','o')
    ,'Mg':('-','lightcoral','x'),'Al':('-','firebrick','o')     ,'Si':('-','palevioletred','o')
    ,'P':('-','orange','o')     ,'S':('-','red','x')             ,'Cl':('-.','green','o')
    ,'K':('-','purple','*')     ,'Ca':('-','lightsalmon','o')     ,'Sc':(':','grey','o')
    ,'Ti':('-','grey','+')         ,'V':(':','blue','o')             ,'Cr':('-','cyan','o')
    ,'Mn':('-.','purple','x')     ,'Fe':('-','darkred','o')         ,'Co':('-','pink','x')
    ,'Ni':('--','green','o')     ,'Cu':(':','brown','o')         ,'Zn':('-','indigo','x')
    ,'Ga':('-','pink','o')         ,'Ge':('--','lightblue','o')     ,'As':('-','fuchsia','+')
    ,'Se':('-','turquoise','o') ,'Br':('-','azure','o')         ,'Rb':('-','black','o')
    ,'Sr':('-','olive','o')     ,'Y':('-','plum','o')             ,'Zr':('-','palevioletred','o')
    ,'Nb':('-','aqua','o')         ,'Mo':('-','khaki','o')         ,'Tc':('-','green','o')
    ,'Ru':('-','lime','o')         ,'Rh':('-','teal','o')             ,'Pd':('-','grey','o')
    ,'Ag':('-','silver','o')     ,'Cd':('-','purple','o')         ,'In':('-','blue','o')
    ,'Sn':('-.','green','o')     ,'Sb':('-','red','o')             ,'Te':('-','plum','o')
    ,'I':('-','red','o')         ,'Cs':('-','orange','o')         ,'Ba':('-','tan','o')
    ,'Os':('-','pink','o')         ,'Ir':('-','green','o')         ,'Pt':('-','blue','o')
    ,'Au':('-','gold','o')         ,'Pb':(':','brown','o')

    ,'H2':('-','black','o')        ,'O2':('-','red','o')             ,'N2':('-','green','o')
    ,'F2':('-','purple','o')     ,'Br2':('-','brown','o')        ,'CH4':('-','blue','o')
    ,'Cl2':('-','pink','o')        ,'H2O':(':','blue','x')            ,'CO2':(':','brown','x')
    ,'CO':(':','red','x')

    ,'mBEEF':('-','black','o') ,'PBE':('-','red','o') ,'BEEF':('-','blue','o')
    ,'RPBE':('-','green','o')

    ,'latticeopt':('-','black','o') ,'bulkmod':('-','red','o') ,'relax':('-','blue','o')
    ,'vib':('-','green','o') ,'vcrelax':('-','purple','o')


    ,'hexagonal': ('-','black','o') ,'fcc':('-','red','o') ,'bcc':('-','blue','o') ,'diamond':('-','green','o')

    ,'sg15':('-','black','o') ,'paw':('-','red','o') ,'gbrv15pbe':('-','blue','o')

    ,'':('-','red','o')}

def str2int(lst:str)->int:
    return sum(set(map(ord,lst)))

def label2Line(label : str)->Tuple[str,str,str]:
    """
    Associate every legend label with a particular (consistent) line style
    """
    if label in labelDict.keys():
        return labelDict[label]               # first check if we can directly get result
    else:
        filtered = str(label).split('_')[0].split('-')[0] # strip label to its essentials
        if filtered in labelDict.keys():
            return labelDict[filtered]
        else: # last resort, a 'random' (but deterministic) label
            print('\t\t\t\tassigning random style to label: ',label)
            all_labs = list(labelDict.values())
            lab_ind  = str2int(str(label)) % len(labelDict)
            return all_labs[lab_ind]

def label2Color(label:str)->str:
    return label2Line(label)[1]
