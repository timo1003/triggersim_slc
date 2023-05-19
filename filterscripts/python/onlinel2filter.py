import copy

import copy
from icecube import icetray, dataclasses
from icecube.filterscripts import filter_globals



class PulseMaskShortcutter(icetray.I3ConditionalModule):
    '''
    Create a copy of a pulse mask, pointing directly to a specific source,
    leaving out all the intermediate masks.  This module loops through the mask
    sources for the given PulseMaskName until a non-mask source is reached,
    then it creates a copy of the PulseMaskName pointing directly to the
    non-mask source, without intermediate steps, put into the frame as
    ShortcutName.  Alternatively, one can name a desired source with
    OrigSourceName.
    '''
    def __init__(self, context):
        icetray.I3ConditionalModule.__init__(self, context)
        self.AddParameter("PulseMaskName",  "Name of the I3RecoPulseSeriesMapMask to create a shortcut for", "")
        self.AddParameter("ShortcutName",   "Name of the shortcut to put into the frame", "")
        self.AddParameter("OrigSourceName", "Name of the desired source the shortcut should point to. Scans for first non-mask source if not set.", "")
        self.AddOutBox("OutBox")

    def Configure(self):
        self.pulseMaskName  = self.GetParameter("PulseMaskName")
        self.shortcutName   = self.GetParameter("ShortcutName")
        self.origSourceName = self.GetParameter("OrigSourceName")

    def DAQ(self, frame):
        self.PushFrame(frame)

    def Physics(self, frame):
        mask = frame[self.pulseMaskName]
        sourceName = mask.source
        shortcutMask = None

        if frame.Has(self.origSourceName) and (sourceName == self.origSourceName):
            # Pulse mask is already shortcut. Put copy of it into the frame.
            shortcutMask = mask
        else:
            if frame.Has(self.origSourceName):
                # Desired pulse mask source is in frame.
                sourceName = self.origSourceName
            else:
                # Loop until root source of pulse mask stack is found.
                sourceMask = frame[sourceName]
                while type(sourceMask) == dataclasses.I3RecoPulseSeriesMapMask:
                    sourceName = sourceMask.source
                    sourceMask = frame[sourceName]
            # Found original source pulses, now create shortcut.
            shortcutMask = dataclasses.I3RecoPulseSeriesMapMask(frame, sourceName, mask.apply(frame))

        # Store shortcut pulse mask in frame.
        frame.Put(self.shortcutName, shortcutMask)
        self.PushFrame(frame)

    def Finish(self):
        return True



@icetray.traysegment
def SplineMPEParaboloid(tray, name, pulses='CleanedMuonPulses', MinimizerName="Minuit", If = lambda f: True):
    """
    Perform advanced error estimation using the Paraboloid fit.
    """
    from icecube.icetray import I3Units
    from icecube import paraboloid
    icetray.load("paraboloid", False)

    if (name+'_SplineMPESeed') not in tray.tray_info.factory_configs:
        tray.AddService("I3BasicSeedServiceFactory", name+"_SplineMPESeed",
                FirstGuesses =                 [ name+"_SplineMPE" ],
                ChargeFraction =               0.9,                # Default
                FixedEnergy =                  float("nan"),       # Default
                MaxMeanTimeResidual =          1000.0*I3Units.ns,  # Default
                NChEnergyGuessPolynomial =     [],                 # Default
                SpeedPolice =                  True,               # Default
                AddAlternatives =              "None",             # Default
                OnlyAlternatives =             False,              # Default
                )

    tray.AddService("I3BasicSeedServiceFactory", name+"_GridpointVertexCorrection",
            InputReadout =                 pulses,
            FirstGuesses =                 [ name+"_SplineMPE" ],    # This is the best available fit that succeeded
            TimeShiftType =                "TFirst",                 # ! Use TFirst for vertex correction
            ChargeFraction =               0.9,                      # Default
            FixedEnergy =                  float( "nan" ),           # Default
            MaxMeanTimeResidual =          1000.0*I3Units.ns,        # Default
            NChEnergyGuessPolynomial =     [],                       # Default
            SpeedPolice =                  True,                     # Default
            AddAlternatives =              "None",                   # Default
            AltTimeShiftType =             "TFirst",                 # Default
            OnlyAlternatives =             False                     # Default
            )

    tray.AddModule( "I3ParaboloidFitter", name+"_SplineMPE_Paraboloid",
            SeedService =                   name+"_SplineMPESeed",  # seed service from above
            LogLikelihood =                 name+"_SplineMPESplineMPEllh",   # likelihood service has been installed earlier
            MaxMissingGridPoints =          1,                      # ! Allow 1 missfit grid point
            VertexStepSize =                5.0 * I3Units.m,        # ! Use small vertex size
            ZenithReach =                   2.0 * I3Units.degree,   # ! Small reach for icecube
            AzimuthReach =                  2.0 * I3Units.degree,   # ! Small reach for icecube
            GridpointVertexCorrection =     name+"_GridpointVertexCorrection", # ! Name of vertex correction service
            Minimizer =                     MinimizerName,        # minimizer service has been installed earlier
            NumberOfSamplingPoints =        8,                      # Default
            NumberOfSteps =                 3,                      # Default
            MCTruthName =                   "",                     # Default
            OutputName =                    name+"_SplineMPE_Paraboloid", # ! Name of the resulting frame object
            If = If
            )



@icetray.traysegment
def SplineMPEBootstrapping(tray, name, pulses='CleanedMuonPulses', ParametrizationName="Para", MinimizerName="Minuit", If = lambda f: True):
    """
    Perform advanced error estimation using the bootstrapping technique.
    The pulses are resampled 6 times and the 50% containment radius is calculated from the subsequent fits.
    """
    from icecube.icetray import I3Units
    from icecube import gulliver_bootstrap

    if (name+'_SplineMPESeed') not in tray.tray_info.factory_configs:
        tray.AddService("I3BasicSeedServiceFactory", name+"_SplineMPESeed",
                FirstGuesses =                 [ name+"_SplineMPE" ],
                ChargeFraction =               0.9,                # Default
                FixedEnergy =                  float("nan"),       # Default
                MaxMeanTimeResidual =          1000.0*I3Units.ns,  # Default
                NChEnergyGuessPolynomial =     [],                 # Default
                SpeedPolice =                  True,               # Default
                AddAlternatives =              "None",             # Default
                OnlyAlternatives =             False,              # Default
                )

    tray.AddService("I3GSLRandomServiceFactory", "I3RandomServiceBS",
                    InstallServiceAs="I3RandomServiceBS")

    tray.AddService("BootstrappingLikelihoodServiceFactory", name+"_BootstrapLLH",
            Pulses            = pulses,
            Bootstrapping     = gulliver_bootstrap.BootstrapOption.Multinomial,
            Iterations        = 6,
            WrappedLikelihood = name+"_SplineMPESplineMPEllh",
            RandomService     = "I3RandomServiceBS"
            )

    tray.AddService("BootStrappingSeedServiceFactory", name+"_BootstrapSeed",
            WrappedSeed             = name+"_SplineMPESeed",
            BootstrappingLikelihood = name+"_BootstrapLLH"
            )

    tray.AddModule("I3SimpleFitter", name+"_SplineMPE_Bootstrap",
            SeedService       = name+"_BootstrapSeed",
            Parametrization   = ParametrizationName,
            LogLikelihood     = name+"_BootstrapLLH",
            Minimizer         = MinimizerName,
            StoragePolicy     = "AllFitsAndFitParams",
            OutputName        = name+"_SplineMPE_Bootstrap",
            If = If
            )

    tray.AddModule("BootstrapSeedTweak", name+"_Bootstrap_TweakSeeds",
            BootstrappedRecos = name+"_SplineMPE_BootstrapVect",
            ContainmentLevel  = 0.5,
            AngularError      = name+"_SplineMPE_Bootstrap_Angular",
            If = If,
            )



@icetray.traysegment
def OnlineL2Filter(tray, name, pulses=filter_globals.CleanedMuonPulses,
                   linefit_name = filter_globals.muon_linefit,
                   llhfit_name  = filter_globals.muon_llhfit,
                   SplineRecoAmplitudeTable=None, SplineRecoTimingTable=None,
                   PathToCramerRaoTable=None, forceOnlineL2BadDOMList=None,
                   If = lambda f: True):

    from math import cos, radians
    import os.path

    from icecube.icetray import I3Units
    from icecube import filterscripts
    from icecube import linefit, gulliver, gulliver_modules, lilliput, spline_reco
    from icecube import bayesian_priors
    from icecube import cramer_rao
    from icecube import mue, truncated_energy
    from icecube.common_variables import direct_hits, hit_multiplicity, hit_statistics, track_characteristics
    import icecube.lilliput.segments

    if SplineRecoAmplitudeTable is None or SplineRecoTimingTable is None:
        raise Exception('SplineRecoAmplitudeTable or SplineRecoTimingTable is None')

    # set path to Cramer-Rao tables
    if (PathToCramerRaoTable is None):
        domain = filter_globals.getDomain()
        if (domain == filter_globals.Domain.SPS) or (domain == filter_globals.Domain.SPTS):
            PathToCramerRaoTable = '/usr/local/pnf/jeb/cramer-rao/resources/data/'
        else:
            PathToCramerRaoTable = os.path.expandvars("$I3_BUILD/cramer-rao/resources/data/")


    def DoBasicReco(frame):
        '''
        Which events should get the basic OnlineL2 recos? (e.g. SPE2it, MPE)
        '''
        passed_Muon = False
        if frame.Has(filter_globals.MuonFilter):
            passed_Muon = frame[filter_globals.MuonFilter].value

        passed_HESE = False
        if frame.Has(filter_globals.HESEFilter):
            passed_HESE = frame[filter_globals.HESEFilter].value        

        # TODO: Add EHE or HighQ Filter as well?

        return (passed_Muon or passed_HESE)


    def DoCut(frame):
        '''
        Which events are the input to the OnlineL2 filter?
        '''
        if frame.Has(filter_globals.MuonFilter):
            return frame[filter_globals.MuonFilter].value
        return False


    def DoAdvancedReco(frame):
        '''
        Which events should get the avanced OnlineL2 recos? (e.g. SplineMPE)
        '''
        passed_L2 = False
        if frame.Has(filter_globals.OnlineL2Filter):
            passed_L2 = frame[filter_globals.OnlineL2Filter].value

        passed_HESE = False
        if frame.Has(filter_globals.HESEFilter):
            passed_HESE = frame[filter_globals.HESEFilter].value        

        # TODO: Add EHE or HighQ Filter as well?

        return (passed_L2 or passed_HESE) and EventHasGoodTrack(frame)


    def FindBestTrack(frame, tracks, output):
        '''
        Store first succesful fit from a given list of tracks under a new name.
        '''
        for track in tracks:
            if frame[track].fit_status == dataclasses.I3Particle.OK:
                frame[output] = frame[track]
                frame[output+'_Name'] = dataclasses.I3String(track)
                if frame.Has(track+'FitParams'):
                    frame[output+'FitParams'] = frame[track+'FitParams']
                return True
        # when we end up here, all fits failed
        return True


    def EventHasGoodTrack(frame, fitname=name+'_BestFit'):
        '''
        Test whether a track fit has has converged.
        '''
        if frame.Has(fitname):
            return (frame[fitname].fit_status == 0)

        return False


    def EventHasUpgoingTrack(frame, fitname=name+'_BestFit'):
        '''
        Test whether there is a good, upgoing track.
        '''
        minZenith = 80.  * I3Units.degree
        maxZenith = 180. * I3Units.degree
        if EventHasGoodTrack(frame, fitname):
            zenith = frame[fitname].dir.zenith
            return (minZenith <= zenith) and (zenith <= maxZenith)

        return False


    def SelectOnlyIceCubePulses(frame, pulses):
        '''
        Create a masked pulsemap which contains only IceCube DOMs.
        '''
        mask = dataclasses.I3RecoPulseSeriesMapMask(frame, pulses,
               lambda om, idx, pulse: om.string <= 78)
        frame[pulses+'IC'] = mask
        return True


    # direct hits definitions (default IceCube direct hits definitions: A, B, C, D)
    dh_defs = direct_hits.get_default_definitions()
    # append 'non-standard' time window E
    if 'E' not in [ dh_def.name for dh_def in dh_defs ]:
        dh_defs.append(direct_hits.I3DirectHitsDefinition("E", -15., 250.))



    #########################################################
    # Begin calculating input variables for OnlineL2 filter #
    #########################################################


    ###############################
    # Perform SPE2it and MPE fits #
    ###############################

    # iterative SPE reco; seeded with single SPE LLH fit
    tray.AddSegment(lilliput.segments.I3IterativePandelFitter, name+'_SPE2itFit',
            pulses       = pulses,
            n_iterations = 2,
            seeds        = [ llhfit_name ],
            domllh       = 'SPE1st',
            tstype       = 'TFirst',
            fitname      = name+'_SPE2itFit',
            If = lambda f: If(f) and DoBasicReco(f) )   

    # seed MPE with SPE2it
    tray.AddSegment(lilliput.segments.I3SinglePandelFitter, name+'_MPEFit',
            pulses       = pulses,
            domllh       = 'MPE',
            seeds        = [ name+'_SPE2itFit' ],
            tstype       = 'TNone', # OnlineL2_16: TNone, OfflineL2: unset (=TFirst)
            fitname      = name+'_MPEFit',
            If = lambda f: If(f) and DoBasicReco(f) )

    # Find best track so far
    tray.Add(FindBestTrack,
             tracks = [ name+'_MPEFit', name+'_SPE2itFit', llhfit_name, linefit_name ],
             output = name+'_BestFit',
             If = lambda f: If(f) and DoBasicReco(f) )

    # Calculate track parameters for best track
    tray.AddSegment(direct_hits.I3DirectHitsCalculatorSegment, name+'_BestFit_DirectHits',
        DirectHitsDefinitionSeries       = dh_defs,
        PulseSeriesMapName               = pulses,
        ParticleName                     = name+'_BestFit',
        OutputI3DirectHitsValuesBaseName = name+'_BestFit_DirectHits',
        BookIt                           = True,
        If = lambda f: If(f) and DoBasicReco(f) )


    # Calculate basic event parameters with all pulses
    tray.AddSegment(hit_multiplicity.I3HitMultiplicityCalculatorSegment, name+'_HitMultiplicityValues',
            PulseSeriesMapName                = pulses,
            OutputI3HitMultiplicityValuesName = name+'_HitMultiplicityValues',
            BookIt                            = True,
            If = lambda f: If(f) and DoBasicReco(f) )

    tray.AddSegment(hit_statistics.I3HitStatisticsCalculatorSegment, name+'_HitStatisticsValues',
            PulseSeriesMapName              = pulses,
            OutputI3HitStatisticsValuesName = name+'_HitStatisticsValues',
            BookIt                          = True,
            If = lambda f: If(f) and DoBasicReco(f) )


    #######################
    # Apply OnlineL2 cuts #
    #######################

    tray.AddModule("I3FilterModule<I3OnlineL2Filter_13>", name+"_OnlineL2Filter2013",
        # input variable names:
        PriParticleKey        = name+'_BestFit',
        DirectHitValues       = name+'_BestFit_DirectHitsC',
        HitMultiplicityValues = name+'_HitMultiplicityValues',
        HitStatisticsValues   = name+'_HitStatisticsValues',
        LLHFitParamsKey       = llhfit_name+'FitParams',
        # cut zones:
        CosZenithZone1 = [-1., cos(radians(82.))],
        CosZenithZone2 = [cos(radians(82.)), cos(radians(66.))],
        CosZenithZone3 = [cos(radians(66.)), 1.],
        # cut values:
        LDirCZone1 = 160.,
        NDirCZone1 = 9,
        PLogLParamZone1 = 4.5,
        PLogLZone1 = 8.3,
        QTotZone1 = 2.7,
        QTotSlopeZone2 = 3.3,
        QTotInterceptZone2 = 1.05 + 0.08,
        PLogLParamZone2 = 4.5,
        PLogLZone2 = 8.3,
        QTotOrCutZone2 = 2.5,
        QTotKinkZone3 = 0.5,
        QTotSlopeZone3 = 0.6,
        QTotInterceptZone3 = 2.4 + 0.13,
        PLogLParamZone3 = 4.5,
        PLogLZone3 = 10.5,
        QTotOrCutZone3 = 3.,
        DiscardEvents = False,
        DecisionName = filter_globals.OnlineL2Filter,
        If = lambda f: If(f) and DoCut(f)
        )


    ##########################
    # Advanced reco's follow #
    ##########################


    #############################################
    # Store pulse mask for pulses used by recos #
    #############################################

    tray.AddModule(PulseMaskShortcutter, name + "_PulseMaskShortcutter",
            PulseMaskName  = pulses,
            ShortcutName   = name+"_"+pulses,
            OrigSourceName = "I3SuperDST",
            If = lambda f: If(f) and DoAdvancedReco(f) )


    #################################
    # Cramer-Rao for BestFit so far #
    #################################

    tray.AddModule("CramerRao", name+'_BestFit_CramerRao',
            InputResponse = pulses,
            InputTrack    = name+'_BestFit',
            OutputResult  = name+'_BestFit_CramerRao',
            AllHits       = True,
            DoubleOutput  = True,
            PathToTable   = PathToCramerRaoTable,
            z_dependent_scatter = True,
            If = lambda f: If(f) and DoAdvancedReco(f) )


    #######################################################
    # Set up basic minimizer and parametrization services #
    #######################################################

    minimizer_name   = lilliput.segments.add_minuit_simplex_minimizer_service(tray)
    para_name        = lilliput.segments.add_simple_track_parametrization_service(tray)

    ####################
    # Bayesian LLH Fit #
    ####################

    # Bayesian weight for downgoing muons
    tray.AddService("I3PowExpZenithWeightServiceFactory", name+"_ZenithWeight",
            Amplitude = 2.49655e-07,                  # Default
            CosZenithRange = [ -1., 1. ],             # Default (zenith range is restricted later in the fitter) 
            DefaultWeight = 1.383896526736738e-87,    # Default
            ExponentFactor = 0.778393,                # Default
            FlipTrack = False,                        # Default
            PenaltySlope = -1000.,                    # Default (penalty is not used, zenith bounds are fixed)
            PenaltyValue = -200.,                     # Default
            Power = 1.67721 )                         # Default

    tray.AddService('I3GulliverMinuitFactory', name+'_BayesMinuit',
            Algorithm     = 'SIMPLEX', # Default
            MaxIterations = 1000,      # Default
            Tolerance     = 0.01 )     # ! be quick, as this is only for bkg rejection, not used in the analysis

    llh_spe1st_name  = lilliput.segments.add_pandel_likelihood_service(tray, pulses, "SPE1st")

    tray.AddService("I3EventLogLikelihoodCombinerFactory", name+"_ZenithWeightPandel",
            InputLogLikelihoods = [ llh_spe1st_name, name+"_ZenithWeight" ] )

    bayesian_seed_name = lilliput.segments.add_seed_service(tray,
            pulses = pulses,
            seeds  = [ name+'_BestFit' ],
            tstype = 'TFirst' )

    tray.AddModule("I3IterativeFitter", name+'_BayesianFit',
            RandomService   = 'SOBOL',
            NIterations     = 2,                          # ! only do two iterations
            CosZenithRange  = [ 0., 1. ],                 # ! force downgoing track
            SeedService     = bayesian_seed_name,
            Parametrization = para_name,
            LogLikelihood   = name+'_ZenithWeightPandel',
            Minimizer       = name+'_BayesMinuit',
            OutputName      = name+'_BayesianFit',
            If = lambda f: If(f) and DoAdvancedReco(f) and EventHasUpgoingTrack(f) )


    ##############
    # Split Fits #
    ##############

    tray.AddModule("I3ResponseMapSplitter", name+"_TWCleanSplitTime",
            InputPulseMap =      "FirstPulseMuonPulses" , # ! Use timewindow cleaned pulses and only the first Pulses
            InputTrackName =     "" ,                       # Default, split by average pulse time
            MinimumNch =         2 ,                        # Default
            DoTRes =             False ,                    # Default
            MinTRes =            0.0 ,                      # Default
            MaxTRes =            1000.0 ,                   # Default
            DoBrightSt =         False ,                    # Default
            MaxDBrightSt =       150.0 ,                    # Default
            If = lambda f: If(f) and DoAdvancedReco(f) )

    tray.AddModule("I3ResponseMapSplitter", name+"_TWCleanSplitGeo",
            InputPulseMap =     "FirstPulseMuonPulses",    # ! Use timewindow cleaned pulses and only the first Pulses
            InputTrackName =    name+"_BestFit",           # This is the best available fit that succeeded
            MinimumNch =        2 ,                        # Default
            DoTRes =            False ,                    # Default
            MinTRes =           0.0 ,                      # Default
            MaxTRes =           1000.0 ,                   # Default
            DoBrightSt =        False ,                    # Default
            MaxDBrightSt =      150.0 ,                    # Default
            If = lambda f: If(f) and DoAdvancedReco(f) )

    for i in [ 1, 2 ]:
        for splittype in [ 'Time', 'Geo' ]:
            split_pulse_name   = name+'_TWCleanSplit%s%i'      % (splittype, i)
            split_linefit_name = name+'_Split%s%i_Linefit'     % (splittype, i)
            split_spe2it_name  = name+'_Split%s%i_SPE2itFit'   % (splittype, i)
            split_bayes_name   = name+'_Split%s%i_BayesianFit' % (splittype, i)

            # Linefit
            tray.AddSegment(linefit.simple, split_linefit_name,
                            inputResponse = split_pulse_name,
                            fitName       = split_linefit_name,
                            If = lambda f: If(f) and DoAdvancedReco(f) )

            # 2-iteration SPE Fit
            split_linefit_seed = lilliput.segments.add_seed_service(tray,
                    pulses = split_pulse_name,       # ! Use split pulses
                    seeds  = [ split_linefit_name ], # ! Seed with linefit
                    tstype = 'TFirst')               # Default

            split_spe1st_llh = lilliput.segments.add_pandel_likelihood_service(tray,
                    pulses = split_pulse_name, # ! Use split pulses
                    domllh = 'SPE1st')         # Default

            tray.AddModule('I3IterativeFitter', split_spe2it_name,
                    SeedService     = split_linefit_seed, # ! Seed with Linefit
                    Parametrization = para_name,          # Default
                    LogLikelihood   = split_spe1st_llh,   # ! Use llh on split pulses
                    Minimizer       = minimizer_name,     # Default
                    NIterations     = 2,                  # ! Do only 2 iterations
                    RandomService   = 'SOBOL',            # Default
                    CosZenithRange  = [ -1., 1. ],        # Default
                    OutputName      = split_spe2it_name,  # ! Output name
                    If = lambda f: If(f) and DoAdvancedReco(f) )

            # Bayesian Fit
            split_spe2it_seed = lilliput.segments.add_seed_service(tray,
                    pulses = split_pulse_name,
                    seeds  = [ split_spe2it_name ],
                    tstype = 'TFirst')

            split_llh_name = name+'_Split%s%i_ZenithWeightPandel' % (splittype, i)
            tray.AddService("I3EventLogLikelihoodCombinerFactory", split_llh_name,
                            InputLogLikelihoods = [ split_spe1st_llh, name+"_ZenithWeight" ] )

            tray.AddModule("I3SimpleFitter", split_bayes_name,
                    SeedService     = split_spe2it_seed,
                    Parametrization = para_name,
                    LogLikelihood   = split_llh_name,
                    Minimizer       = minimizer_name,
                    OutputName      = split_bayes_name,
                    If = lambda f: If(f) and DoAdvancedReco(f) and EventHasUpgoingTrack(f) )


    ############################################
    # Calculate some variables only on IC DOMs #
    ############################################

    tray.Add(SelectOnlyIceCubePulses, name+'_SelectICPulses', pulses=pulses,
             If = lambda f: If(f) and DoAdvancedReco(f))

    tray.AddSegment(hit_multiplicity.I3HitMultiplicityCalculatorSegment, name+'_HitMultiplicityValuesIC',
            PulseSeriesMapName                = pulses+'IC',
            OutputI3HitMultiplicityValuesName = name+'_HitMultiplicityValuesIC',
            BookIt                            = True,
            If = lambda f: If(f) and DoAdvancedReco(f)
            )

    tray.AddSegment(hit_statistics.I3HitStatisticsCalculatorSegment, name+'_HitStatisticsValuesIC',
            PulseSeriesMapName              = pulses+'IC',
            OutputI3HitStatisticsValuesName = name+'_HitStatisticsValuesIC',
            BookIt                          = True,
            If = lambda f: If(f) and DoAdvancedReco(f)
            )

    ##############################################################
    # To improve SplineMPE, first run a MuEx reco on the MPE fit #
    ##############################################################

    tray.AddModule("muex", name+'_BestFit_MuEx',
            pulses = pulses,
            rectrk = name+'_BestFit',
            result = name+'_BestFit_MuEx',
            energy = True,
            detail = True,
            compat = False,
            lcspan = 0,
            If = lambda f: If(f) and DoAdvancedReco(f) )

    #################
    # Run SplineMPE #
    #################

    tray.AddSegment(spline_reco.SplineMPE, name+'_SplineMPE',
                    fitname               = name+'_SplineMPE',
                    configuration         = 'fast',
                    PulsesName            = pulses,
                    TrackSeedList         = [ name+'_BestFit' ],
                    BareMuTimingSpline    = SplineRecoTimingTable,
                    BareMuAmplitudeSpline = SplineRecoAmplitudeTable,
                    EnergyEstimators      = [ name+'_BestFit_MuEx' ],
                    If = lambda f: If(f) and DoAdvancedReco(f) )

    tray.AddModule("CramerRao", name+'_SplineMPE_CramerRao',
            InputResponse = pulses,
            InputTrack    = name+'_SplineMPE',
            OutputResult  = name+'_SplineMPE_CramerRao',
            AllHits       = True,
            DoubleOutput  = True,
            PathToTable   = PathToCramerRaoTable,
            z_dependent_scatter = True,
            If = lambda f: If(f) and DoAdvancedReco(f) )

    # calculate track properties with all DOMs, and with only IceCube DOMs
    for suffix in [ '', 'IC' ]:
        tray.AddSegment(direct_hits.I3DirectHitsCalculatorSegment, name+'_SplineMPE_DirectHits'+suffix,
                DirectHitsDefinitionSeries       = dh_defs,
                PulseSeriesMapName               = pulses+suffix,
                ParticleName                     = name+'_SplineMPE',
                OutputI3DirectHitsValuesBaseName = name+'_SplineMPE_DirectHits'+suffix,
                BookIt                           = True,
                If = lambda f: If(f) and DoAdvancedReco(f) )

        tray.AddSegment(track_characteristics.I3TrackCharacteristicsCalculatorSegment, name+'_SplineMPE_Characteristics'+suffix,
                PulseSeriesMapName                     = pulses+suffix,
                ParticleName                           = name+'_SplineMPE',
                OutputI3TrackCharacteristicsValuesName = name+'_SplineMPE_Characteristics'+suffix,
                TrackCylinderRadius                    = 150.*I3Units.m,
                BookIt                                 = True,
                If = lambda f: If(f) and DoAdvancedReco(f) )

        tray.AddSegment(track_characteristics.I3TrackCharacteristicsCalculatorSegment, name+'_SplineMPE_CharacteristicsNoRCut'+suffix,
                PulseSeriesMapName                     = pulses+suffix,
                ParticleName                           = name+'_SplineMPE',
                OutputI3TrackCharacteristicsValuesName = name+'_SplineMPE_CharacteristicsNoRCut'+suffix,
                TrackCylinderRadius                    = 4000.*I3Units.m,
                BookIt                                 = True,
                If = lambda f: If(f) and DoAdvancedReco(f) )


    ############################################
    # Run energy estimators on SplineMPE track #
    ############################################

    def PutBadDomListInFrame(frame):
        if forceOnlineL2BadDOMList is None:
            frame[name+'_BadDomList'] = dataclasses.I3VectorOMKey(filter_globals.online_bad_doms)
        else:
            # If requested, store a copy of the forced onlineL2 bad DOM list. This is used for pass2 
            # where the hard-coded bad DOM list is not applicable to old data. We made the choice 
            # to re-use the L2 bad DOM list we have access to in pass2 for this instead. 
            frame[name+'_BadDomList'] = copy.copy(frame[forceOnlineL2BadDOMList])
    tray.AddModule(PutBadDomListInFrame, name+"_BadDOMsToFrame",)

    # find spline table service name
    splineServiceName = None
    for key in tray.context.keys():
        if key.startswith('BareMuSpline'):
            assert splineServiceName is None
            splineServiceName = key

    tray.AddModule("I3TruncatedEnergy", name+'_SplineMPE_TruncatedEnergy',
            RecoPulsesName =          pulses,
            RecoParticleName =        name+'_SplineMPE',
            ResultParticleName =      name+'_SplineMPE_TruncatedEnergy',
            I3PhotonicsServiceName =  splineServiceName,
            UseRDE =                  True, # default - correct for HQE DOMs
            BadDomListName =          name+'_BadDomList',
            If = lambda f: If(f) and DoAdvancedReco(f) )

    tray.AddModule("I3mue", name+'_SplineMPE_MuE',
            RecoPulseSeriesNames = [ pulses ],
            RecoResult           = name+'_SplineMPE',
            RecoIntr             = 1,
            OutputParticle       = name+'_SplineMPE_MuE',
            If = lambda f: If(f) and DoAdvancedReco(f) )

    tray.AddModule("muex", name+'_SplineMPE_MuEx',
            pulses = pulses,
            rectrk = name+'_SplineMPE',
            result = name+'_SplineMPE_MuEx',
            energy = True,
            detail = True,
            compat = False,
            lcspan = 0,
            If = lambda f: If(f) and DoAdvancedReco(f) )


    ##################################
    # Calculate InTime IceTop hits   #
    ##################################
    from icecube.filterscripts.icetophitcounter import CountIceTopInTime
    tray.AddModule(CountIceTopInTime,name+'_IT_hits',
                   InIceReco = name+'_SplineMPE',
                   IT_hlc_pulses = filter_globals.HLCTankPulses,
                   IT_slc_pulses = filter_globals.SLCTankPulses,
                   Count_HLC_InTime = filter_globals.IceTop_HLC_InTime,
                   Count_SLC_InTime = filter_globals.IceTop_SLC_InTime, 
                   If = lambda f: If(f) and DoAdvancedReco(f))

    ##################################
    # Variables to keep in the frame #
    ##################################

    filter_globals.onlinel2filter_keeps += [
        name+'_SPE2itFit',
        name+'_SPE2itFitFitParams',
        name+'_MPEFit',
        name+'_MPEFitFitParams',
        name+'_BestFit',
        name+'_BestFitFitParams',
        name+'_BestFit_Name',
        name+'_BestFit_DirectHitsA',
        name+'_BestFit_DirectHitsB',
        name+'_BestFit_DirectHitsC',
        name+'_BestFit_DirectHitsD',
        name+'_BestFit_DirectHitsE',
        name+'_HitMultiplicityValues',
        name+'_HitStatisticsValues',

        name+'_'+pulses,

        name+'_BestFit_MuEx',
        name+'_BestFit_MuEx_r',
        name+'_BestFit_CramerRao',
        name+'_BestFit_CramerRaoParams',
        name+'_BestFit_CramerRao_cr_azimuth',
        name+'_BestFit_CramerRao_cr_zenith',

        name+'_BayesianFit',
        name+'_BayesianFitFitParams',
        
        name+'_SplitGeo1_Linefit',
        name+'_SplitGeo1_SPE2itFit',
        name+'_SplitGeo1_SPE2itFitFitParams',
        name+'_SplitGeo1_BayesianFit',
        name+'_SplitGeo1_BayesianFitFitParams',
        name+'_SplitGeo2_Linefit',
        name+'_SplitGeo2_SPE2itFit',
        name+'_SplitGeo2_SPE2itFitFitParams',
        name+'_SplitGeo2_BayesianFit',
        name+'_SplitGeo2_BayesianFitFitParams',
        name+'_SplitTime1_Linefit',
        name+'_SplitTime1_SPE2itFit',
        name+'_SplitTime1_SPE2itFitFitParams',
        name+'_SplitTime1_BayesianFit',
        name+'_SplitTime1_BayesianFitFitParams',
        name+'_SplitTime2_Linefit',
        name+'_SplitTime2_SPE2itFit',
        name+'_SplitTime2_SPE2itFitFitParams',
        name+'_SplitTime2_BayesianFit',
        name+'_SplitTime2_BayesianFitFitParams',

        name+'_HitMultiplicityValuesIC',
        name+'_HitStatisticsValuesIC',

        name+'_SplineMPE',
        name+'_SplineMPEFitParams',
        name+'_SplineMPE_CramerRao',
        name+'_SplineMPE_CramerRaoParams',
        name+'_SplineMPE_CramerRao_cr_azimuth',
        name+'_SplineMPE_CramerRao_cr_zenith',
        name+'_SplineMPE_DirectHitsA',
        name+'_SplineMPE_DirectHitsB',
        name+'_SplineMPE_DirectHitsC',
        name+'_SplineMPE_DirectHitsD',
        name+'_SplineMPE_DirectHitsE',
        name+'_SplineMPE_Characteristics',
        name+'_SplineMPE_CharacteristicsNoRCut',
        name+'_SplineMPE_DirectHitsICA',
        name+'_SplineMPE_DirectHitsICB',
        name+'_SplineMPE_DirectHitsICC',
        name+'_SplineMPE_DirectHitsICD',
        name+'_SplineMPE_DirectHitsICE',
        name+'_SplineMPE_CharacteristicsIC',
        name+'_SplineMPE_CharacteristicsNoRCutIC',
        name+'_SplineMPE_TruncatedEnergy_AllDOMS_Muon',
        name+'_SplineMPE_TruncatedEnergy_AllDOMS_MuEres',
        name+'_SplineMPE_TruncatedEnergy_AllDOMS_Neutrino',
        name+'_SplineMPE_TruncatedEnergy_DOMS_Muon',
        name+'_SplineMPE_TruncatedEnergy_DOMS_MuEres',
        name+'_SplineMPE_TruncatedEnergy_DOMS_Neutrino',
        name+'_SplineMPE_TruncatedEnergy_AllBINS_Muon',
        name+'_SplineMPE_TruncatedEnergy_AllBINS_MuEres',
        name+'_SplineMPE_TruncatedEnergy_AllBINS_Neutrino',
        name+'_SplineMPE_TruncatedEnergy_BINS_Muon',
        name+'_SplineMPE_TruncatedEnergy_BINS_MuEres',
        name+'_SplineMPE_TruncatedEnergy_BINS_Neutrino',
        name+'_SplineMPE_TruncatedEnergy_ORIG_Muon',
        name+'_SplineMPE_TruncatedEnergy_ORIG_Neutrino',
        name+'_SplineMPE_TruncatedEnergy_ORIG_dEdX',
        name+'_SplineMPE_MuE',
        name+'_SplineMPE_MuEx',
        name+'_SplineMPE_MuEx_r',
    ]

    # remove leftover reconstructions for events that did not pass OnlineL2
    tray.Add('Delete', name+'_Delete_Leftovers',
            Keys = filter_globals.onlinel2filter_keeps,
            If = lambda f: If(f) and (not DoAdvancedReco(f)) )

