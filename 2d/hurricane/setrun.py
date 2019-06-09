#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import
from __future__ import print_function

#ensure# encoding: utf-8
"""
Setup a run for a simple hurricane but with multiple layers.

"""

import os
import datetime

import numpy

import clawpack.geoclaw.data
import clawpack.geoclaw.topotools as tt
import clawpack.geoclaw.units as units
from clawpack.geoclaw.surge.storm import Storm

# Initial ramp up time for hurricane
RAMP_UP_TIME = 12 * 60**2

def days2seconds(days):
    return days * 24 * 60**2

#------------------------------
def setrun(claw_pkg='geoclaw'):
#------------------------------

    """
    Define the parameters used for running Clawpack.

    INPUT:
        claw_pkg expected to be "geoclaw" for this setrun.

    OUTPUT:
        rundata - object of class ClawRunData

    """

    from clawpack.clawutil import data

    assert claw_pkg.lower() == 'geoclaw',  "Expected claw_pkg = 'geoclaw'"

    num_dim = 2
    rundata = data.ClawRunData(claw_pkg, num_dim)

    #------------------------------------------------------------------
    # Standard Clawpack parameters to be written to claw.data:
    #   (or to amr2ez.data for AMR)
    #------------------------------------------------------------------
    clawdata = rundata.clawdata  # initialized when rundata instantiated

    # Set single grid parameters first.
    # See below for AMR parameters.


    # ---------------
    # Spatial domain:
    # ---------------

    # Number of space dimensions:
    clawdata.num_dim = num_dim

    # Lower and upper edge of computational domain:
    clawdata.lower[0] = -200e3      # west boundary (m)
    clawdata.upper[0] = 500e3       # east boundary (m)

    clawdata.lower[1] = -300e3      # south boundary (m)
    clawdata.upper[1] = 300e3       # north boundary (m)



    # Number of grid cells: Coarsest grid
    clawdata.num_cells[0] = 70 
    clawdata.num_cells[1] = 60

    # ---------------
    # Size of system:
    # ---------------

    # Number of equations in the system:
    clawdata.num_eqn = 6

    # Number of auxiliary variables in the aux array (initialized in setaux)
    # Bathy, storm fields, multilayer
    clawdata.num_aux = 1 + 3 + 2

    # Index of aux array corresponding to capacity function, if there is one:
    clawdata.capa_index = 0
    
    # -------------
    # Initial time:
    # -------------

    clawdata.t0 = -RAMP_UP_TIME


    # Restart from checkpoint file of a previous run?
    # Note: If restarting, you must also change the Makefile to set:
    #    RESTART = True
    # If restarting, t0 above should be from original run, and the
    # restart_file 'fort.chkNNNNN' specified below should be in 
    # the OUTDIR indicated in Makefile.

    clawdata.restart = False               # True to restart from prior results
    clawdata.restart_file = 'fort.chk00036'  # File to use for restart data

    # -------------
    # Output times:
    #--------------

    # Specify at what times the results should be written to fort.q files.
    # Note that the time integration stops after the final output time.
    # The solution at initial time t0 is always written in addition.

    clawdata.output_style = 1

    if clawdata.output_style==1:
        # Output nout frames at equally spaced times up to tfinal:
        clawdata.tfinal = days2seconds(3)
        recurrence = 4
        clawdata.num_output_times = int((clawdata.tfinal - clawdata.t0) *
                                        recurrence / (60**2 * 24))

        clawdata.output_t0 = True  # output at initial (or restart) time?

    elif clawdata.output_style == 2:
        # Specify a list of output times.
        clawdata.output_times = [0.5, 1.0]

    elif clawdata.output_style == 3:
        # Output every iout timesteps with a total of ntot time steps:
        clawdata.output_step_interval = 1
        clawdata.total_steps = 10
        clawdata.output_t0 = True
        

    clawdata.output_format = 'binary'      # 'ascii' or 'binary' 

    clawdata.output_q_components = 'all'   # need all
    clawdata.output_aux_components = 'all'  # eta=h+B is in q
    clawdata.output_aux_onlyonce = False    # output aux arrays each frame



    # ---------------------------------------------------
    # Verbosity of messages to screen during integration:
    # ---------------------------------------------------

    # The current t, dt, and cfl will be printed every time step
    # at AMR levels <= verbosity.  Set verbosity = 0 for no printing.
    #   (E.g. verbosity == 2 means print only on levels 1 and 2.)
    clawdata.verbosity = 1



    # --------------
    # Time stepping:
    # --------------

    # if dt_variable==1: variable time steps used based on cfl_desired,
    # if dt_variable==0: fixed time steps dt = dt_initial will always be used.
    clawdata.dt_variable = True

    # Initial time step for variable dt.
    # If dt_variable==0 then dt=dt_initial for all steps:
    clawdata.dt_initial = 1.0

    # Max time step to be allowed if variable dt used:
    clawdata.dt_max = 1e+99

    # Desired Courant number if variable dt used, and max to allow without
    # retaking step with a smaller dt:
    clawdata.cfl_desired = 0.75
    clawdata.cfl_max = 1.0
    # clawdata.cfl_desired = 0.45
    # clawdata.cfl_max = 0.5

    # Maximum number of time steps to allow between output times:
    clawdata.steps_max = 5000




    # ------------------
    # Method to be used:
    # ------------------

    # Order of accuracy:  1 => Godunov,  2 => Lax-Wendroff plus limiters
    clawdata.order = 1
    
    # Use dimensional splitting? (not yet available for AMR)
    #  0 or 'unsplit' or none'  ==> Unsplit
    #  1 or 'increment'         ==> corner transport of waves
    #  2 or 'all'               ==> corner transport of 2nd order corrections too
    clawdata.dimensional_split = "unsplit"
    
    # For unsplit method, transverse_waves can be 
    #  0 or 'none'      ==> donor cell (only normal solver used)
    #  1 or 'increment' ==> corner transport of waves
    #  2 or 'all'       ==> corner transport of 2nd order corrections too
    clawdata.transverse_waves = 2

    # Number of waves in the Riemann solution:
    clawdata.num_waves = 6
    
    # List of limiters to use for each wave family:  
    # Required:  len(limiter) == num_waves
    # Some options:
    #   0 or 'none'     ==> no limiter (Lax-Wendroff)
    #   1 or 'minmod'   ==> minmod
    #   2 or 'superbee' ==> superbee
    #   3 or 'mc'       ==> MC limiter
    #   4 or 'vanleer'  ==> van Leer
    clawdata.limiter = ['mc', 'mc', 'mc', 'mc', 'mc', 'mc']

    clawdata.use_fwaves = True    # True ==> use f-wave version of algorithms
    
    # Source terms splitting:
    #   src_split == 0 or 'none'    ==> no source term (src routine never called)
    #   src_split == 1 or 'godunov' ==> Godunov (1st order) splitting used, 
    #   src_split == 2 or 'strang'  ==> Strang (2nd order) splitting used,  not recommended.
    clawdata.source_split = 'godunov'


    # --------------------
    # Boundary conditions:
    # --------------------

    # Number of ghost cells (usually 2)
    clawdata.num_ghost = 2

    # Choice of BCs at xlower and xupper:
    #   0 => user specified (must modify bcN.f to use this option)
    #   1 => extrapolation (non-reflecting outflow)
    #   2 => periodic (must specify this at both boundaries)
    #   3 => solid wall for systems where q(2) is normal velocity

    clawdata.bc_lower[0] = 'extrap'
    clawdata.bc_upper[0] = 'extrap'

    clawdata.bc_lower[1] = 'extrap'
    clawdata.bc_upper[1] = 'extrap'



    # --------------
    # Checkpointing:
    # --------------

    # Specify when checkpoint files should be created that can be
    # used to restart a computation.

    clawdata.checkpt_style = 0

    if clawdata.checkpt_style == 0:
        # Do not checkpoint at all
        pass

    elif clawdata.checkpt_style == 1:
        # Checkpoint only at tfinal.
        pass

    elif clawdata.checkpt_style == 2:
        # Specify a list of checkpoint times.  
        clawdata.checkpt_times = [0.1,0.15]

    elif clawdata.checkpt_style == 3:
        # Checkpoint every checkpt_interval timesteps (on Level 1)
        # and at the final time.
        clawdata.checkpt_interval = 5


    # ---------------
    # AMR parameters:
    # ---------------
    amrdata = rundata.amrdata

    # max number of refinement levels:
    amrdata.amr_levels_max = 1

    # List of refinement ratios at each level (length at least mxnest-1)
    amrdata.refinement_ratios_x = [2,6]
    amrdata.refinement_ratios_y = [2,6]
    amrdata.refinement_ratios_t = [2,6]


    # Specify type of each aux variable in amrdata.auxtype.
    # This must be a list of length maux, each element of which is one of:
    #   'center',  'capacity', 'xleft', or 'yleft'  (see documentation).

    amrdata.aux_type = ['center', 'center', 'center', 'center', 'center', 
                        'center', 'center']


    # Flag using refinement routine flag2refine rather than richardson error
    amrdata.flag_richardson = False    # use Richardson?
    amrdata.flag2refine = True

    # steps to take on each level L between regriddings of level L+1:
    amrdata.regrid_interval = 3

    # width of buffer zone around flagged points:
    # (typically the same as regrid_interval so waves don't escape):
    amrdata.regrid_buffer_width  = 2

    # clustering alg. cutoff for (# flagged pts) / (total # of cells refined)
    # (closer to 1.0 => more small grids may be needed to cover flagged cells)
    amrdata.clustering_cutoff = 0.700000

    # print info about each regridding up to this level:
    amrdata.verbosity_regrid = 0  

    #  ----- For developers ----- 
    # Toggle debugging print statements:
    amrdata.dprint = False      # print domain flags
    amrdata.eprint = False      # print err est flags
    amrdata.edebug = False      # even more err est flags
    amrdata.gprint = False      # grid bisection/clustering
    amrdata.nprint = False      # proper nesting output
    amrdata.pprint = False      # proj. of tagged points
    amrdata.rprint = False      # print regridding summary
    amrdata.sprint = False      # space/memory output
    amrdata.tprint = True       # time step reporting each level
    amrdata.uprint = False      # update/upbnd reporting
    
    # More AMR parameters can be set -- see the defaults in pyclaw/data.py

    # ---------------
    # Regions:
    # ---------------
    rundata.regiondata.regions = []
    # to specify regions of refinement append lines of the form
    #  [minlevel,maxlevel,t1,t2,x1,x2,y1,y2]

    # ---------------
    # Gauges:
    # ---------------
    rundata.gaugedata.gauges = []
    # for gauges append lines of the form  [gaugeno, x, y, t1, t2]
    # num_gauges = 21
    # for n in xrange(0, num_gauges):
    #     # Turn towards beach ~ 100 m water
    #     x = 455e3 
    #     # Start 25 km inside of primary domain
    #     y = 550e3 / (num_gauges + 1) * (n + 1) + -275e3
    #     rundata.gaugedata.gauges.append([n + 1, x, y, 0.0, 1e10])

    #------------------------------------------------------------------
    # GeoClaw specific parameters:
    #------------------------------------------------------------------
    rundata = setgeo(rundata)

    return rundata
    # end of function setrun
    # ----------------------


#-------------------
def setgeo(rundata):
#-------------------
    """
    Set GeoClaw specific runtime parameters.
    For documentation see ....
    """

    try:
        geo_data = rundata.geo_data
    except:
        print("*** Error, this rundata has no geo_data attribute")
        raise AttributeError("Missing geo_data attribute")

    # == Physics ==
    geo_data.gravity = 9.81
    geo_data.coordinate_system = 1
    geo_data.earth_radius = 6367.5e3
    geo_data.rho = [1025.0 * 0.9, 1025.0]
    geo_data.rho_air = 1.15
    geo_data.ambient_pressure = 101.3e3

    # == Forcing Options
    geo_data.coriolis_forcing = True
    geo_data.theta_0 = 25.0 # Beta-plane approximation center
    geo_data.friction_forcing = True
    geo_data.friction_depth = 1e10

    # == Algorithm and Initial Conditions ==
    geo_data.sea_level = 0.0
    geo_data.dry_tolerance = 1.e-2

    # Refinement settings
    refine_data = rundata.refinement_data
    refine_data.wave_tolerance = 1.0
    refine_data.speed_tolerance = [1.0, 2.0, 3.0, 4.0]
    refine_data.deep_depth = 300.0
    refine_data.max_level_deep = 4
    refine_data.variable_dt_refinement_ratios = True

    # == settopo.data values ==
    topo_data = rundata.topo_data
    # for topography, append lines of the form
    #    [topotype, minlevel, maxlevel, t1, t2, fname]
    topo_data.topofiles.append([2, 1, 5, -RAMP_UP_TIME, 1e10, 'topo.tt2'])
    
    # == setdtopo.data values ==
    dtopo_data = rundata.dtopo_data
    # for moving topography, append lines of the form :   (<= 1 allowed for now!)
    #   [topotype, minlevel,maxlevel,fname]

    # ================
    #  Set Surge Data
    # ================
    data = rundata.surge_data

    # Source term controls
    data.wind_forcing = True
    data.drag_law = 1
    data.pressure_forcing = True

    data.wind_index = 2
    data.pressure_index = 4

    data.display_landfall_time = True

    # AMR parameters, m/s and m respectively
    data.wind_refine = [20.0, 40.0, 60.0]
    data.R_refine = [60.0e3, 40e3, 20e3]

    # Storm parameters - Parameterized storm (Holland 1980)
    data.storm_specification_type = 'holland80'  # (type 1)
    data.storm_file = os.path.expandvars(os.path.join(os.getcwd(),
                                         'fake.storm'))

    # Contruct storm
    forward_velocity = units.convert(20, 'km/h', 'm/s')
    theta = 0.0 * numpy.pi / 180.0 # degrees from horizontal to radians

    my_storm = Storm()
    
    # Take seconds and time period of 30 minutes and turn them into datatimes
    t_ref = datetime.datetime.now()
    t_sec = numpy.arange(-RAMP_UP_TIME, rundata.clawdata.tfinal, 30.0 * 60.0)
    my_storm.t = [t_ref + datetime.timedelta(seconds=t) for t in t_sec]

    ramp_func = lambda t: (t + (2 * RAMP_UP_TIME)) * (t < 0) / (2 * RAMP_UP_TIME) \
                          + numpy.ones(t_sec.shape) * (t >= 0)

    my_storm.time_offset = t_ref
    my_storm.eye_location = numpy.empty((t_sec.shape[0], 2))
    my_storm.eye_location[:, 0] = forward_velocity * t_sec * numpy.cos(theta)
    my_storm.eye_location[:, 1] = forward_velocity * t_sec * numpy.sin(theta)
    my_storm.max_wind_speed = units.convert(56, 'knots', 'm/s') * ramp_func(t_sec)
    my_storm.central_pressure = units.convert(1024, "mbar", "Pa")  \
                                - (units.convert(1024, "mbar", "Pa")  \
                                   - units.convert(950, 'mbar', 'Pa'))  \
                                       * ramp_func(t_sec)
    my_storm.max_wind_radius = [units.convert(8, 'km', 'm')] * t_sec.shape[0]
    my_storm.storm_radius = [units.convert(100, 'km', 'm')] * t_sec.shape[0]

    my_storm.write(data.storm_file, file_format="geoclaw")
    
    # ======================
    #  Multi-layer settings
    # ======================
    data = rundata.multilayer_data

    # Physics parameters
    data.num_layers = 2
    data.eta = [0.0, -300.0]
    
    # Algorithm parameters
    data.eigen_method = 2
    data.inundation_method = 2
    data.richardson_tolerance = 1e10
    data.wave_tolerance = [0.1, 0.5]
    data.layer_index = 1


    # =======================
    #  Set Variable Friction
    # =======================
    data = rundata.friction_data

    # Variable friction
    data.variable_friction = False
    data.friction_index = 1

    return rundata
    # end of function setgeo
    # ----------------------


def write_topo_file(run_data, out_file, **kwargs):

    # Make topography
    topo = tt.Topography()
    topo.x = numpy.linspace(run_data.clawdata.lower[0], 
                            run_data.clawdata.upper[0], 
                            run_data.clawdata.num_cells[0] + 8)
    topo.y = numpy.linspace(run_data.clawdata.lower[1], 
                            run_data.clawdata.upper[1], 
                            run_data.clawdata.num_cells[1] + 8)

    # Create bathymetry profile
    beach_slope = 0.05
    basin_depth = -3000
    shelf_depth = -200
    x0 = 350e3
    x1 = 450e3
    x2 = 480e3
    topo_profile = [(run_data.clawdata.lower[0], basin_depth),
                    (x0, basin_depth), (x1, shelf_depth), (x2, shelf_depth),
                    (run_data.clawdata.upper[0], 
                            beach_slope * (run_data.clawdata.upper[0] - x2) 
                            + shelf_depth)]
    topo.topo_func = tt.create_topo_func(topo_profile)
    topo.write(out_file)

    return topo


if __name__ == '__main__':
    # Set up run-time parameters and write all data files.
    import sys
    if len(sys.argv) == 2:
        rundata = setrun(sys.argv[1])
    else:
        rundata = setrun()

    rundata.write()

    topo = write_topo_file(rundata, 'topo.tt2')
