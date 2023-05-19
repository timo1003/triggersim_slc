from icecube import icetray, dataclasses, linefit
from icecube.icetray import OMKey, I3Units

def SelectOMKeySeedPulse(omkey_name, pulses_name, seed_name):
    def do(f):
        om = f[omkey_name][0]
        f[seed_name] = dataclasses.I3RecoPulseSeriesMapMask(f, pulses_name, lambda omkey, p_idx, p: omkey == om and p_idx == 0)
    return do

@icetray.traysegment
def HitCleaningEHE(tray, name,
                   inATWD = 'EHECalibratedATWD_Wave', inFADC = 'EHECalibratedFADC_Wave',
                   If = lambda f: True):

    from icecube import STTools
    #icetray.load("libSeededRTCleaning");

    # Create a SeededRT configuration object with the standard RT settings.
    # This object will be used by all the different SeededRT modules of this EHE
    # hit cleaning tray segment.
    from icecube.STTools.seededRT.configuration_services import I3DOMLinkSeededRTConfigurationService
    seededRTConfigEHE = I3DOMLinkSeededRTConfigurationService(
        ic_ic_RTRadius              = 150.0*I3Units.m,
        ic_ic_RTTime                = 1000.0*I3Units.ns,
        treat_string_36_as_deepcore = False,
        useDustlayerCorrection      = True, # EHE use the dustlayer correction!
        allowSelfCoincidence        = True
    )

    #*********************************************************** 
    # portia splitter
    # This module takes the splitted start time and end time and makes split DOM map
    #*********************************************************** 
    tray.AddModule("I3PortiaSplitter", name + "EHE-SplitMap-Maker",
                   DataReadOutName="HLCOfflineCleanInIceRawDataWODC",
                   SplitDOMMapName="splittedDOMMap",
                   SplitLaunchTime=True, 
		   TimeWindowName = "TriggerSplitterLaunchWindow",
                   If = If,)

    #***************************************************************                                    
    #     Portia Pulse process  with the spllit DOM map for SeededRT seed
    #***************************************************************                                    
    tray.AddModule("I3Portia", name + "pulseSplitted",
                   SplitDOMMapName = "splittedDOMMap",
                   OutPortiaEventName = "EHEPortiaEventSummary",
                   ReadExternalDOMMap=True,
                   MakeIceTopPulse=False,
                   ATWDPulseSeriesName = "EHEATWDPulseSeries",
                   ATWDPortiaPulseName = "EHEATWDPortiaPulse",
                   ATWDWaveformName = inATWD,
                   ATWDBaseLineOption = "eheoptimized",
                   FADCBaseLineOption = "eheoptimized",
                   ATWDThresholdCharge = 0.1*I3Units.pC,
                   ATWDLEThresholdAmplitude = 1.0*I3Units.mV,
                   UseFADC = True,
                   FADCPulseSeriesName = "EHEFADCPulseSeries",
                   FADCPortiaPulseName = "EHEFADCPortiaPulse",
                   FADCWaveformName = inFADC,
                   FADCThresholdCharge = 0.1*I3Units.pC,
                   FADCLEThresholdAmplitude = 1.0*I3Units.mV,
                   MakeBestPulseSeries = True,
                   BestPortiaPulseName = "EHEBestPortiaPulse",
                   PMTGain = 10000000,
                   If = If )
    
    tray.AddModule("I3PortiaEventOMKeyConverter", name + "portiaOMconverter",
                   InputPortiaEventName = "EHEPortiaEventSummary",
                   OutputOMKeyListName = "LargestOMKey",
                   If = If
                   )

    #***************************************************************
    #     EHE event selector to apply EHE filter on Pframe events
    #***************************************************************
# This turned out to be a bad idea because this module stop the stream
# and event may be both in EHE stream and other streams. So we should not
# stop the stream here in order not to affect to the other streams
#
#    tray.AddModule("I3EHEEventSelector","selector",
#                   setCriteriaOnJulietParticle = False,
#                   setCriteriaOnInIceDOMLaunch = False,
#                   setCriteriaOnEHEFirstGuess = False,
#                   setCriteriaOnPortiaPulse = True,
#                   inAtwdPortiaName = "EHEATWDPortiaPulse",
#                   inFadcPortiaName = "EHEFADCPortiaPulse",
#                   InputPortiaEventName = "EHEPortiaEventSummary",
#                   lowestNPEs = pow(10., 3.),
#                   highestNPEs = pow(10., 10.),
#                   numberOfDOMs = 0,
#                   If = If)

    #***************************************************************
    #     EHE SeededRTCleaning for DOMmap
    #***************************************************************

    #---------------------------------------------------------------------------
    # The splittedDOMMap frame object is an I3MapKeyVectorDouble
    # object. In order to use STTools in the way SeededRTCleaning did it, we
    # need to convert this into an I3RecoPulseSeriesMap where the time of each
    # pulse is set to the double value of the splittedDOMMap frame object.
    def I3MapKeyVectorDouble_to_I3RecoPulseSeriesMap(f):
        i3MapKeyVectorDouble = f['splittedDOMMap']
        i3RecoPulseSeriesMap = dataclasses.I3RecoPulseSeriesMap()
        for (k,l) in i3MapKeyVectorDouble.items():
            pulses = dataclasses.I3RecoPulseSeries()
            for d in l:
                p = dataclasses.I3RecoPulse()
                p.time = d
                pulses.append(p)
            i3RecoPulseSeriesMap[k] = pulses
        f['splittedDOMMap_pulses'] = i3RecoPulseSeriesMap
    tray.AddModule(I3MapKeyVectorDouble_to_I3RecoPulseSeriesMap, name+'IsolatedHitsCutSRT_preconvert',
        If = If
    )

    # Also we need the seed pulse, which is the first pulse of the OM which is
    # named "LargestOMKey".
    tray.AddModule(SelectOMKeySeedPulse(
            omkey_name  = 'LargestOMKey',
            pulses_name = 'splittedDOMMap_pulses',
            seed_name   = 'IsolatedHitsCutSRT_seed'
        ),
        name+'IsolatedHitsCutSRT_seed_pulse_selector',
        If = If
    )

    # Do SeededRT cleaning.
    tray.AddModule('I3SeededRTCleaning_RecoPulse_Module', name+'IsolatedHitsCutSRT',
        InputHitSeriesMapName  = 'splittedDOMMap_pulses',
        OutputHitSeriesMapName = 'splittedDOMMapSRT_pulses',
        STConfigService        = seededRTConfigEHE,
        SeedProcedure          = 'HitSeriesMapHitsFromFrame',
        SeedHitSeriesMapName   = 'IsolatedHitsCutSRT_seed',
        MaxNIterations         = -1,
        Streams                = [icetray.I3Frame.Physics],
        If = If
    )

    # Convert the resulting I3RecoPulseSeriesMap back into an
    # I3MapKeyVectorDouble object.
    def I3RecoPulseSeriesMap_to_I3MapKeyVectorDouble(f):
        i3RecoPulseSeriesMap = f['splittedDOMMapSRT_pulses']
        i3MapKeyVectorDouble = dataclasses.I3MapKeyVectorDouble()
        for (k,l) in i3RecoPulseSeriesMap.items():
            doubles = [p.time for p in l]
            i3MapKeyVectorDouble[k] = doubles
        f['splittedDOMMapSRT'] = i3MapKeyVectorDouble
    tray.AddModule(I3RecoPulseSeriesMap_to_I3MapKeyVectorDouble, name+'IsolatedHitsCutSRT_postconvert',
        If = If
    )
    #---------------------------------------------------------------------------
    #tray.AddModule( "I3SeededRTHitCleaningModule<double>", name + "IsolatedHitsCutSRT",
                    #InputResponse = "splittedDOMMap", # ! Name of input Launches
                    #OutputResponse = "splittedDOMMapSRT",      # ! Name of output Launches
                    #InputOMKeyName = "LargestOMKey",
                    #RTRadius = 150,              # ! Radius for RT cleaning
                    #RTTime = 1000,               # ! Time for RT cleaning
                    #DeepCoreRTRadius =  -1,      # Default
                    #DeepCoreRTTime =  -1,        # Default
                    #MaxIterations = -1,          # infinite
                    #Seeds = "Brightest",         # ! do not use all HLC its as seed
                    #HLCCoreThreshold = 2,        # Default
                    #CylinderHeight = -1,         # Default
                    #IgnoreDustGap = True,
                    #Stream = icetray.I3Frame.Physics,
                    #If = If )

    #***************************************************************
    #     Portia Pulse process with the spllited DOM map after SeededRT
    #***************************************************************
    tray.AddModule("I3Portia", name + "pulseSplittedSRT",
                   SplitDOMMapName = "splittedDOMMapSRT",
                   OutPortiaEventName = "EHEPortiaEventSummarySRT",
                   ReadExternalDOMMap = True,
                   MakeIceTopPulse = False,
                   ATWDPulseSeriesName = "EHEATWDPulseSeriesSRT",
                   ATWDPortiaPulseName = "EHEATWDPortiaPulseSRT",
                   ATWDWaveformName = inATWD,
                   ATWDBaseLineOption = "eheoptimized",
                   FADCBaseLineOption = "eheoptimized",
                   ATWDThresholdCharge = 0.1*I3Units.pC,
                   ATWDLEThresholdAmplitude = 1.0*I3Units.mV,
                   UseFADC = True,
                   FADCPulseSeriesName = "EHEFADCPulseSeriesSRT",
                   FADCPortiaPulseName = "EHEFADCPortiaPulseSRT",
                   FADCWaveformName = inFADC,
                   FADCThresholdCharge = 0.1*I3Units.pC,
                   FADCLEThresholdAmplitude = 1.0*I3Units.mV,
                   MakeBestPulseSeries = True,
                   BestPortiaPulseName = "EHEBestPortiaPulseSRT",
                   PMTGain = 10000000,
                   If = If )

    #***************************************************************
    #     EHE SeededRTCleaning for reco pulse
    #***************************************************************
    # Remove Deep core string at first #
    tray.AddModule("I3OMSelection<I3RecoPulseSeries>", name+"omselection",
        # The name of this InputResponse should be changed to the one from the standard process
        # Especially, the one with standard SRT cleaned and TWC static one

	# nk: 11/9/2012 We took out redoign the pole standard processing from L2,
	# so the standard pulses is no longer SRTWC but just SRT. Uncommnet module below
                   InputResponse = "SRTInIcePulses",
                   OmittedStrings = [79,80,81,82,83,84,85,86],
                   OutputOMSelection = "SRTInIcePulses_BadOMSelectionString",
                   OutputResponse = 'SRTInIcePulses_WODC',
                   If = If,
                   )

    #---------------------------------------------------------------------------
    tray.AddModule(SelectOMKeySeedPulse(
            omkey_name  = 'LargestOMKey',
            pulses_name = 'SRTInIcePulses_WODC',
            seed_name   = 'SRTInIcePulses_WODC_seed'),
        name+'IsolatedHitsCutSRTReco_seed_pulse_selector',
        If = If
    )
    tray.AddModule('I3SeededRTCleaning_RecoPulse_Module', name+'IsolatedHitsCutSRTReco',
        InputHitSeriesMapName  = 'SRTInIcePulses_WODC',
        OutputHitSeriesMapName = 'EHEInIcePulsesSRT',
        STConfigService        = seededRTConfigEHE,
        SeedProcedure          = 'HitSeriesMapHitsFromFrame',
        SeedHitSeriesMapName   = 'SRTInIcePulses_WODC_seed',
        MaxNIterations         = -1, # Infinite.
        Streams                = [icetray.I3Frame.Physics],
        If = If)
    #---------------------------------------------------------------------------
    #tray.AddModule( "I3SeededRTHitCleaningModule<I3RecoPulse>", name + "IsolatedHitsCutSRTReco",
                    #InputResponse = "SRTInIcePulses_WODC", # ! Name of input recopulses
                    #OutputResponse = "EHEInIcePulsesSRT",      # ! Name of output recopulses
                    #InputOMKeyName = "LargestOMKey",
                    #RTRadius = 150,                     # ! Radius for RT cleaning
                    #RTTime = 1000,                      # ! Time for RT cleaning
                    #DeepCoreRTRadius = -1,              # Default
                    #DeepCoreRTTime = -1,                # Default
                    #MaxIterations = -1,                 # infinite
                    #Seeds = "Brightest",                # ! do not use all HLC its as seed
                    #HLCCoreThreshold = 2,               # Default
                    #CylinderHeight = -1,                # Default
                    #IgnoreDustGap = True,
                    #Stream = icetray.I3Frame.Physics,
                    #If = If )

    # If we used the TWC cleaned reco pulses above, this may not be needed in the end,
    # but let me just keep it as commented out

    # nk: 11/9/2012 as explained above, standard pulses have no TWC, uncomment this
    # one question though is why in the original comments above, it says "TWC static one"
    # when the original standard pulses as well as this cleanings is dynamic TWC
    tray.AddModule( "I3TimeWindowCleaning<I3RecoPulse>", name + "TimeWindowHLC_NFESRT",
                    InputResponse = "EHEInIcePulsesSRT",    # ! Use pulse series 
                    OutputResponse = "EHETWCInIcePulsesSRT", # ! Name of cleanedpulse series
                    TimeWindow = 6000 * I3Units.ns,         # ! 6 usec time window  
                    If = If )



    #***************************************************************
    # Improved line fit from IC86 analysis
    #***************************************************************
    #####################################################################
    # Below this line is for improvedLineFit geometrical reconstruction #
    # Not used for the other purposes                                   #
    #####################################################################
    tray.AddModule("I3EHEStaticTWC", name + "portia_static",
                   InputPulseName = "EHEBestPortiaPulseSRT",
                   InputPortiaEventName = "EHEPortiaEventSummarySRT",
                   outputPulseName = "EHEBestPortiaPulseSRT_BTW",
                   TimeInterval = 500.0 * I3Units.ns, #650, now no interval cut
                   TimeWidnowNegative =  -2000.0 * I3Units.ns,
                   TimeWindowPositive = 6400.0 * I3Units.ns,
                   If = If )
    ######################################################################
    # Convert Opheria pulses to reco pulses to goes into improvedLineFit #
    ###################################################################### 
    tray.AddModule("I3OpheliaConvertPortia", name + "portia2reco",
                   InputPortiaPulseName = "EHEBestPortiaPulseSRT_BTW",
                   OutputRecoPulseName = "EHERecoPulseBestPortiaPulseSRT_BTW",
                   If = If  )
    
    ######################################################################  
    # Now processing with improvedLineFit                                # 
    ######################################################################
    tray.AddModule("DelayCleaningEHE", name + "DelayCleaning",
                   InputResponse = "EHERecoPulseBestPortiaPulseSRT_BTW",
                   OutputResponse = "EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay",
                   Distance = 200.0 * I3Units.m, #156m default
                   TimeInterval = 1800.0 * I3Units.ns, #interval 1.8msec
                   TimeWindow = 778.0 * I3Units.ns, #778ns default
                   If = If )

    #**********************************************************************
    # The Second time SeededRT cleaning - this is only for imprlvedLineFit 
    # Now aplying on the COG                                   
    #**********************************************************************  
    tray.AddModule('I3SeededRTCleaning_RecoPulse_Module', name+'Isolated_DelayClean',
        InputHitSeriesMapName  = 'EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay',
        OutputHitSeriesMapName = 'EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay_RT',
        STConfigService        = seededRTConfigEHE,
        SeedProcedure          = 'HLCCOGSTHits',
        MaxNIterations         = -1, # Infinite.
        Streams                = [icetray.I3Frame.Physics],
        If = If)
    #tray.AddModule( "I3SeededRTHitCleaningModule<I3RecoPulse>", name + "Isolated_DelayClean",
                    #InputResponse = "EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay", # ! Name of input Launches
                    #OutputResponse = "EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay_RT",      # ! Name of output Launches
                    #RTRadius = 150,                     # ! Radius for RT cleaning
                    #RTTime = 1000,                      # ! Time for RT cleaning
                    #DeepCoreRTRadius = -1,              # Default
                    #DeepCoreRTTime = -1,                # Default
                    #MaxIterations = -1,                 # infinite
                    #Seeds = "COG",                      # ! do not use all HLC hits as seed
                    #HLCCoreThreshold = 2,               # Default
                    #CylinderHeight = -1,                # Default
                    #IgnoreDustGap = True,
                    #Stream = icetray.I3Frame.Physics,
                    #If = If )
    ######################################################################### 
    tray.AddModule("HuberFitEHE", name + "HuberFit",
                   Name = "HuberFit",
                   Distance = 180.0 * I3Units.m, #153m default
                   InputRecoPulses = "EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay_RT",
                   If = If)
    #########################################################################
    tray.AddModule("DebiasingEHE", name + "Debiasing",
                   OutputResponse = "EHEdebiased_BestPortiaPulseSRT_CleanDelay",
                   InputResponse = "EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay_RT",
                   Seed = "HuberFit",
                   Distance = 150.0 * I3Units.m,#116m default
                   If = If)

    tray.AddModule("Delete", name + "EHE_Cleanup",
                   keys=[ 'EHEATWDPulseSeries', 'EHEATWDPortiaPulse',
                          'EHEFADCPulseSeries', 'EHEFADCPortiaPulse',
                          'splittedDOMMap_pulses',
                          'splittedDOMMapSRT_pulses',
                          'IsolatedHitsCutSRT_seed',
                          'SRTInIcePulses_WODC_seed',
                          'EHEBestPortiaPulse',
                          'EHEBestPortiaPulseSRT_BTW',
                          'EHERecoPulseBestPortiaPulseSRT_BTW',
                          'EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay',
                          'EHERecoPulseBestPortiaPulseSRT_BTW_CleanDelay_RT',
                          'SRTInIcePulses_BadOMSelectionString'
                          ])

