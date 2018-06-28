# Internal Modules
from dbplot.utils.misc    import Get,FnArgs
from dbplot.utils.plot    import err_lat_correction,eos_fit,avgNone,gMeanAbs
from dbplot.plotting.plot import BarPlot,LinePlot,HistPlot
#############################################################################

lp = LinePlot(query = "SELECT job_id,timestamp,user from job ORDER BY RAND() LIMIT 1000 "
             ,xFunc = Get('job_id')
             ,yFunc = Get('timestamp')
             ,lFunc = FnArgs(func = lambda x: x*2,args = ['user'])
             ,gFunc = Get('user')
             ,title = 'Trivial lineplot'
             ,xLab = 'Job_id'
             ,yLab = 'Timestamp')

bp = BarPlot(query = 'SELECT COUNT(1) as count,user from job GROUP BY user'
            ,xFunc = Get('count')
            ,lFunc = Get('user')
            ,gFunc = Get('user')
            ,title = 'Number of jobs submitted per user'
            ,xLab  = 'User')

hp = HistPlot(query = 'SELECT pw FROM relax_job JOIN calc USING (calc_id)'
             ,xFunc = FnArgs(int,args=['pw'])
             ,title = 'Distribution of PW cutoffs over all jobs'
             ,xLab = 'PW cutoff, eV')

count = BarPlot(query="""SELECT dftcode,xc,count(1) AS count
                         FROM relax_job JOIN calc USING (calc_id)
                         GROUP BY dftcode,xc"""
               ,xFunc  = Get('count')
               ,gFunc  = Get('dftcode')
               ,spFunc = Get('xc')
               ,title  = 'Number of DFT relaxations'
               ,yLab   = 'Count'
               ,xLab   = 'DFT code')

errLattice = BarPlot("""SELECT A.dftcode
                              ,C.a
                              ,S.spacegroup
                              ,S.n_atoms
                              ,SDE.value
                              ,P.name
                              ,A.xc
                        FROM finaltraj   AS F
                        JOIN struct      AS S USING (struct_id)
                        JOIN bulk        AS B USING (struct_id)
                        JOIN cell        AS C USING (cell_id)
                        JOIN job         AS J USING (job_id)
                        JOIN relax_job   AS R USING (job_id)
                        JOIN calc        AS A USING (calc_id)
                        JOIN species AS P USING (species_id)
                        JOIN struct_dataset AS SD
                        JOIN struct_dataset_element AS SDE USING (struct_dataset_id, species_id)
                        WHERE
                            A.pw = 500
                            AND SD.name='keld_solids'
                            AND SDE.property='lattice parameter'
                            AND S.n_atoms < 3 # primative cells only
                        GROUP BY A.dftcode,species_id """
                    ,xFunc  = FnArgs(err_lat_correction,['a','spacegroup','n_atoms','value'])
                    ,spFunc = Get('xc')
                    ,xLab   = 'DFT code'
                    ,yLab   = r'Error in lattice constant \AA'
                    ,aggFunc= gMeanAbs
                    )

hbonds = LinePlot("""SELECT COUNT(B.h_bond) AS hbonds,F.energy
                    FROM finaltraj AS F
                    JOIN chargemol_map AS M USING (job_id)
                    JOIN bond AS B ON M.charge_id=B.job_id
                    GROUP BY F.job_id """
                ,xFunc=Get('hbonds')
                ,yFunc=Get('energy')
                ,xLab = 'Hydrogen bonds'
                ,yLab = 'Energy, eV')


bulkmod = BarPlot("""SELECT GROUP_CONCAT(CONCAT('[',C.volume,',',T.energy,']'))  AS ve_pairs
                             ,GROUP_CONCAT(J.job_name) as job_names
                             ,R.calc_id
                             ,R.calc_other_id
                             ,P.name
                             ,SDE.value as bm_expt
                             ,CA.dftcode
                    FROM
                    traj as T
                    JOIN struct         AS S USING (struct_id)
                    JOIN species        AS P USING (species_id)
                    JOIN cell           AS C USING (cell_id)
                    JOIN job            AS J USING (job_id)
                    JOIN relax_job      AS R USING (job_id)
                    JOIN calc           AS CA USING (calc_id)
                    JOIN struct_dataset AS SD
                    JOIN struct_dataset_element AS SDE USING (struct_dataset_id, species_id)

                    WHERE T.final
                    AND C.volume > 0
                    AND SD.name='keld_solids'
                    AND SDE.property='bulk modulus'
                    AND CA.pw > 900
                    GROUP BY S.species_id,R.calc_id,R.calc_other_id
                    HAVING COUNT(1) > 5"""
                 ,xFunc   = FnArgs(lambda x,y: eos_fit(x)['bulkmod'] - float(y)
                                               if eos_fit(x)['bulkmod']
                                               else None
                                    ,['ve_pairs','bm_expt'])
                 ,gFunc   = Get('name')
                 ,spFunc   = Get('dftcode')
                 ,xLab    = 'Species'
                 ,aggFunc = avgNone)
