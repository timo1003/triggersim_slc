import sys
import os
from functools import partial
from icecube import icetray, dataclasses, lilliput, toprec
from icecube.icetray import I3Units
icetray.load('smallshower-filter', False)
from icecube.filterscripts.offlineL2 import level2_IceTop_globals
from icecube.filterscripts.offlineL2 import level2_Reconstruction_Muon
from icecube.filterscripts.offlineL2 import Globals

@icetray.traysegment
def IceTopPrefits(tray, name,
    Pulses                  = '',
    ShowerCOG               = level2_IceTop_globals.icetop_shower_cog,
    ShowerPlane             = level2_IceTop_globals.icetop_shower_plane,
    SmallShowerDecision     = level2_IceTop_globals.icetop_small_shower_decision,
    SmallShowerNStationName = level2_IceTop_globals.icetop_small_shower_nstation_name,
    If                      = lambda f: True):
    
    tray.AddModule('I3TopRecoCore', name + '_COG',
        DataReadout     = Pulses,
        ShowerCore      = ShowerCOG,
        NTanks          = 7,         # ! Use 7 largest pulses only
        Weighting_Power = 0.5,       # Default
        Verbose         = False,     # Default
        If              = If
        )
    
    tray.AddModule('I3TopRecoPlane', name + '_ShowerPlane',
        DataReadout     = Pulses,
        ShowerPlane     = ShowerPlane,
        EventHeaderName = 'I3EventHeader', # Default
        Trigger         = 3,               # Default
        Verbose         = False,           # Default
        If              = If
        )
    
    tray.AddModule('I3IcePickModule<I3SmallShowerFilter>', name + "_SmallShowerFilter",
        TopPulseKey        = Pulses,     
        DecisionName       = SmallShowerDecision,
        NStationResultName = SmallShowerNStationName,
        FilterGeometry     = 'IC86',                  # Current detector configuration
        CacheResults       = False,                   # Default
        DiscardEvents      = False,                   # Default
        InvertFrameOutput  = False,                   # Default
        NEventsToPick      = -1,                      # Default
        If                 = If
        )


@icetray.traysegment
def LaputopStandard(tray, name,
    Pulses      = '',
    Laputop     = level2_IceTop_globals.icetop_shower_laputop,
    ShowerCOG   = level2_IceTop_globals.icetop_shower_cog,
    ShowerPlane = level2_IceTop_globals.icetop_shower_plane,
    SnowFactor  = -1.0,                                        # No snow correction
    FixCore     = False,
    BadTanks    = level2_IceTop_globals.icetop_cluster_cleaning_excluded_tanks,
    If          = lambda f: True):
    '''
    This is the standard Laputop configuration from
    $I3_SRC/toprec/python/laputop_standard_traysegment.py
    '''
    ########## SERVICES FOR GULLIVER ##########

    ## The "simple lambda" snowservice
    tray.AddService("I3SimpleSnowAttenuationServiceFactory",name+"_SimpleSnow")(
        ("Lambda", SnowFactor)
        )
    
    ## This one is the standard one.
    tray.AddService('I3GulliverMinuitFactory', name + '_Minuit',
        Algorithm        = 'SIMPLEX', # Default
        FlatnessCheck    = True,      # Default
        MaxIterations    = 2500,
        MinuitStrategy   =    2,      # Default
        Tolerance        =    0.01,
        MinuitPrintLevel =   -2       # Default
        )
    
    ## The Seed service
    tray.AddService('I3LaputopSeedServiceFactory', name + '_ToprecSeed',
        InCore               = ShowerCOG,
        InPlane              = ShowerPlane,
        #SnowCorrectionFactor = SnowFactor,
        Beta                 = 2.6,         # ! first guess for Beta
        InputPulses          = Pulses       # ! this'll let it first-guess at S125 automatically
        )
    
    ## Step 1:
    tray.AddService('I3LaputopParametrizationServiceFactory', name + '_ToprecParam1',
        FixTrackDir       = True,
        FixCore           = FixCore,
        VertexStepSize    =   10.0 * I3Units.m, # ! The COG is very good for contained events, don't step too far
        LimitCoreBoxSize  =  200.0 * I3Units.m,
        CoreXYLimits      = 2000.0 * I3Units.m, # Default
        FixSize           = False,              # Default
        SStepSize         =    1.0,             # Default
        maxLogS125        =    8.0,             # Default is 6., be a bit safer, although should never happen to be this large
        IsBeta            = True,               # Default
        BetaStepSize      =    0.6,             # Default
        MinBeta           =    2.9,             # From toprec... 2nd iteration (DLP, using beta)
        MaxBeta           =    3.1
        )
    
    ## Step 2:
    tray.AddService('I3LaputopParametrizationServiceFactory', name + '_ToprecParam2',
        FixTrackDir       = False,              # Default
        FixCore           = FixCore,
        VertexStepSize    =    2.0 * I3Units.m,
        LimitCoreBoxSize  =   15.0 * I3Units.m,
        CoreXYLimits      = 2000.0 * I3Units.m, # Default
        FixSize           = False,              # Default
        SStepSize         =    0.045,
        maxLogS125        =    8.0,             # Default is 6., be a bit safer, although should never happen to be this large
        IsBeta            = True,               # Default
        BetaStepSize      =    0.15,
        MinBeta           =    2.0,             # From toprec... 3rd iteration (DLP, using beta)
        MaxBeta           =    4.0
        )
        
    ## Step 3:
    tray.AddService('I3LaputopParametrizationServiceFactory', name + '_ToprecParam3',
        FixTrackDir       = True,
        FixCore           = FixCore,
        VertexStepSize    =    1.0 * I3Units.m,
        LimitCoreBoxSize  =   45.0 * I3Units.m,
        CoreXYLimits      = 2000.0 * I3Units.m, # Default
        FixSize           = False,              # Default
        SStepSize         =    0.045,
        maxLogS125        =    8.0,             # Default
        IsBeta            = True,               # Default
        BetaStepSize      =    0.15,
        MinBeta           =    0.0,
        MaxBeta           =   10.0
        )
    
    tray.AddService('I3LaputopLikelihoodServiceFactory', name + '_ToprecLlh',
        DataReadout             = Pulses,
        BadTanks                = BadTanks,
        Curvature               = '',                # ! NO timing likelihood (at first; this will be overridden)
        DynamicCoreTreatment    = 5.0,              # Default (no I3Units here since the value is multiplied by I3Units.m in the module!)
        Ldf                     = 'dlp',             # Default
        MaxIntraStationTimeDiff = 80.0 * I3Units.ns, # ! Don't use time fluctuating tanks for timing fits, could really mess up the hard work
        SaturationLikelihood    = True,              # Default
        SoftwareThreshold       = -1.0,              # Default
        OldXYZ                  = False,
        SnowServiceName         =  name+"_SimpleSnow",
        Trigger                 = 5                  # Default
        )
    
    ################# GULLIVERIZED FITTER MODULE #######################
    
    # This module performs all three steps
    tray.AddModule('I3LaputopFitter', Laputop,
        Minimizer            = name + '_Minuit',
        SeedService          = name + '_ToprecSeed',
        NSteps               = 3,
        Parametrization1     = name + '_ToprecParam1',
        Parametrization2     = name + '_ToprecParam2',
        Parametrization3     = name + '_ToprecParam3',
        LogLikelihoodService = name + '_ToprecLlh',
        LdfFunctions         = ['dlp', 'dlp', 'dlp'],
        CurvFunctions        = ['', 'gausspar', 'gausspar'], # VERY IMPORTANT : use time Llh for step 3, but fix direction!
        StoragePolicy        = 'OnlyBestFit',                # Default
        If                   = If
        )


@icetray.traysegment
def LaputopSmallShower(tray, name,
    Pulses      = '',
    Laputop     = level2_IceTop_globals.icetop_small_shower_laputop,
    ShowerCOG   = level2_IceTop_globals.icetop_shower_cog,
    ShowerPlane = level2_IceTop_globals.icetop_shower_plane,
    SnowFactor  = -1.0,                                              # No snow correction
    FixCore     = False,
    FitSnow     = False,
    BadTanks    = level2_IceTop_globals.icetop_cluster_cleaning_excluded_tanks,
    If          = lambda f: True):
    '''
    This is the standard Laputop configuration for small showers from
    http://code.icecube.wisc.edu/svn/sandbox/IceTop-scripts/trunk/laputop_traysegments/laputop_smallshower_traysegment.py
    '''
    ########## SERVICES FOR GULLIVER ##########
    
    ## The "simple lambda" snowservice
    tray.AddService("I3SimpleSnowAttenuationServiceFactory",name+"_SimpleSnow")(
        ("Lambda", SnowFactor)
        )

    ## This one is the standard one.
    tray.AddService('I3GulliverMinuitFactory', name + '_Minuit',
        Algorithm        = 'SIMPLEX', # Default
        FlatnessCheck    = True,      # Default
        MaxIterations    = 2500,
        MinuitStrategy   =    2,      # Default
        Tolerance        =    0.01,
        MinuitPrintLevel =   -2       # Default
        )
    
    ## The Seed service
    tray.AddService('I3LaputopSeedServiceFactory', name + '_ToprecSeed',
        InCore               = ShowerCOG,
        InPlane              = ShowerPlane,
        #SnowCorrectionFactor = SnowFactor,
        Beta                 = 2.6,         # ! first guess for Beta
        InputPulses          = Pulses       # ! this'll let it first-guess at S125 automatically
        )
    
    ## Step 1:
    tray.AddService('I3LaputopParametrizationServiceFactory', name + '_ToprecParam1',
        FixTrackDir       = True,
        FixCore           = FixCore,
        VertexStepSize    =   20.0 * I3Units.m, # Default
        LimitCoreBoxSize  =  200.0 * I3Units.m,
        CoreXYLimits      = 2000.0 * I3Units.m, # Default
        FixSize           = False,              # Default
        SStepSize         =    1.0,             # Default
        maxLogS125        =    6.0,             # Default
        IsBeta            = True,               # Default
        BetaStepSize      =    0.6,             # Default
        MinBeta           =    1.5,             # Default
        MaxBeta           =    5.0              # Default
        )
    
    tray.AddService('I3LaputopLikelihoodServiceFactory', name + '_ToprecLlh',
        DataReadout             = Pulses,
        BadTanks                = BadTanks,
        Curvature               = '',    # ! NO timing likelihood (at first; this will be overridden)
        DynamicCoreTreatment    = 5.0,  # Default (no I3Units here since the value is multiplied by I3Units.m in the module!)
        Ldf                     = 'dlp', # Default
        MaxIntraStationTimeDiff = -1.0,  # Default
        SaturationLikelihood    = True,  # Default
        SoftwareThreshold       = -1.0,  # Default
        OldXYZ                  = False,
        SnowServiceName         =  name+"_SimpleSnow",
        Trigger                 = 3      # ! Reduce min number of stations
        ) 
    
    ################# GULLIVERIZED FITTER MODULE #######################
    
    ## This module performs the three steps
    tray.AddModule('I3LaputopFitter', Laputop,
        Minimizer            = name + '_Minuit',
        SeedService          = name + '_ToprecSeed',
        NSteps               = 1,
        Parametrization1     = name + '_ToprecParam1',
        LogLikelihoodService = name + '_ToprecLlh',
        LdfFunctions         = ['dlp'],
        CurvFunctions        = [''],                   # NO curvature or timing likelihood
        StoragePolicy        = 'OnlyBestFit',          # Default
        If                   = If
        )


@icetray.traysegment
def OfflineCoincMuonReco(tray, name,
    Pulses = '',
    If = lambda f: True,
    suffix = ''):
    
    tray.AddSegment(level2_Reconstruction_Muon.SPE, 'SPE' + suffix,
        Pulses = Pulses,
        N_iter = 2,
        If     = If,
        suffix = suffix
    )
    
    tray.AddSegment(level2_Reconstruction_Muon.MPE, 'MPE' + suffix,
        Pulses = Pulses,
        Seed   = 'SPEFit2',
        If     = If,
        suffix = suffix
        )


@icetray.traysegment
def ReconstructIceTop(tray, name,
                      Pulses = '',
                      CoincPulses = '',
                      If = lambda f: True):
    
    tray.AddSegment(IceTopPrefits, name + '_Prefits',
        Pulses = Pulses,
        If     = If
        )
    
    tray.AddSegment(LaputopStandard, name + '_LaputopStandard',
        Pulses = Pulses,
        If     = If
        )
    
    tray.AddSegment(LaputopSmallShower, name + '_LaputopSmallShower',
        Pulses = Pulses,
        If     = If
        )
    
    tray.AddSegment(OfflineCoincMuonReco, name + '_OfflineCoincMuonReco',
        Pulses = CoincPulses,
        If     = partial(Globals.icetop_wg_coinc_icetop),
        suffix = level2_IceTop_globals.coinc_name
        )

