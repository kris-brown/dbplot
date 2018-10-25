# External Modules
from typing     import Any
from os         import environ,listdir
from os.path    import isdir,join
from ast        import literal_eval

# Internal Modules
from dbplot import Plot,ConnectInfo,parser,path_to_funcs # type: ignore

"""
CLI for visualizing data in a MySQL database
"""
################################################################################

def main(args:dict)->None:

    # Get DB info
    #----------
    dbpth = args['db'] or environ['DB_JSON']
    db    = ConnectInfo.from_file(dbpth)

    # Add functions into namespace from user-specified files
    #-------------------------------------------------------
    for fncpth in args['funcs']:
        fs = path_to_funcs(fncpth)
        locals().update(fs)

    # Process binds
    #-------------------
    binds = literal_eval(args['binds']) if args['binds'] else []
    if not isinstance(binds,list):
        binds = [binds]

    # Create Plot object
    #-------------------
    pp = args['pltpth']
    if pp:
        if isdir(pp):
            ps = [Plot.from_file(join(pp,x)) for x in listdir(pp) if x[-4:]=='json']
        else:
            p = Plot.from_file(args['pltpth'])
            for k,v in (args['args'] or {}).items():
                p.data[k] = v
            ps = [p]
    else:
        plotter = Plot.pltdict()[args['type']]
        p = plotter(query=args['query'],**args['args'])
        ps = [p]

    # Make plots and show
    #-------------------
    import matplotlib                                # type: ignore
    matplotlib.use('Qt5Agg')
    from matplotlib.pyplot    import gca,subplots,show,figure   # type: ignore

    fig = figure()
    global curr
    curr = 0 # type: ignore

    def on_key(event:Any)->None:
        button = event.key
        kwargs = {'conn':db,'binds':binds}
        try:
            i = int(button)
            
            # Clear canvas and replot
            event.canvas.figure.clear()
            ps[i].plot(ax=event.canvas.figure.gca(),**kwargs) #type: ignore
            event.canvas.draw()

        except ValueError:
            d = {'right':1,'left':-1}

            if button in d:
                dx = d[button]
                global curr
                curr += dx                 #type: ignore
                currindex = curr % len(ps) #type: ignore

                # Clear canvas and replot
                event.canvas.figure.clear()
                ps[currindex].plot(ax=event.canvas.figure.gca(),**kwargs) #type: ignore
                event.canvas.draw()

    ps[0].plot(ax=gca(),conn=db,binds=binds) #type: ignore

    cid = fig.canvas.mpl_connect('key_press_event', on_key)

    show()

if __name__=='__main__':
    args = parser.parse_args()
    main(vars(args))
