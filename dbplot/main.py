# External Modules
from typing            import Any
from os                import environ,listdir
from os.path           import isdir,join,basename
from ast               import literal_eval
from plotly.offline    import plot # type: ignore
from jinja2            import Template
# Internal Modules
from dbplot.plot     import Plot
from dbplot.db       import ConnectInfo
from dbplot.parse    import parser
from dbplot.misc     import path_to_funcs

"""
CLI for visualizing data in a MySQL database
"""
################################################################################
fname = 'temp'

def main(args:dict)->None:

    # Get DB info
    #----------
    dbpth = environ['DB_JSON'] or args['db'] or '/Users/ksb/Documents/JSON/functionals.json'
    db    = ConnectInfo.from_file(dbpth)

    # Add functions into namespace from user-specified files
    #-------------------------------------------------------
    funcs = {}
    for fncpth in args['funcs']:
        fs = path_to_funcs(fncpth)
        funcs.update(fs)

    # Process binds
    #-------------------
    binds = literal_eval(args['binds']) if args['binds'] else []
    if not isinstance(binds,list):
        binds = [binds]

    # Create Plot object
    #-------------------
    pp = args['pltpth']
    filename = args['outpth'] or basename(pp).replace('.json','.html')
    if pp:
        if isdir(pp):
            ps = [Plot.from_file(join(pp,x)) for x in listdir(pp) if x[-4:]=='json']
        else:
            ps = [Plot.from_file(args['pltpth'])]
            for k,v in (args['args'] or {}).items():
                ps[0].data[k] = v
    else:
        assert args['type'], 'Did you forget to specify --pltpth?'
        plotter = Plot.pltdict()[args['type']]
        ps      = [plotter(query=args['query'], **args['args'])]

    if len(ps)>1:
        plot_urls = [plot(p.fig(conn=db, binds = binds, funcs = funcs),
                          filename='%s%d.html'%(filename,i),include_mathjax='cdn',auto_open = args['open']) for i,p in enumerate(ps)]
    else:
        plot_urls = plot(ps[0].fig(conn=db, binds = binds, funcs = funcs),
                          filename=filename,include_mathjax='cdn',auto_open = args['open'])


if __name__=='__main__':
    args = parser.parse_args()
    main(vars(args))
