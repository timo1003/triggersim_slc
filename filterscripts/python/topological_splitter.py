from icecube import icetray

@icetray.traysegment
def TopologicalSplitting(tray, name, seededRTConfig,
                         InputPulses = 'InIcePulses',
                         OutputPulses = 'TopoSplitPulses',
                         SplitName = 'TopologicalSplit'):
    """
    Applies the topological splitter to the DAQ frame by
    first doing a SeededRTHitCleaning, then splitting events
    with the I3TopologicalSplitter.
    """
    # Import dependecies.
    from icecube import TopologicalSplitter, STTools
    from icecube.icetray import OMKey, I3Units
    
    tray.AddModule('I3SeededRTCleaning_RecoPulseMask_Module', name + '_SeededRTCleaning',
        InputHitSeriesMapName  = InputPulses,
        OutputHitSeriesMapName = 'QSRTInIcePulses',
        STConfigService        = seededRTConfig,
        SeedProcedure          = 'HLCCoreHits',
        NHitsThreshold         = 2,
        MaxNIterations         = 3,
        Streams                = [icetray.I3Frame.DAQ]
    )
    #tray.AddModule("I3SeededRTHitMaskingModule",name + '_SeededRTCleaning',
        #InputResponse = InputPulses, # ! Name of input pulse series
        #OutputResponse = "QSRTInIcePulses",      # ! Name of output pulse series
        #MaxIterations = 3,                          # ! 3 iterations are enough
        #Seeds = 'HLCcore',                      # ! do not use all HLC hits as seed
        #Stream=icetray.I3Frame.DAQ,
        #)

    tray.AddModule("I3TopologicalSplitter",SplitName,
        InputName="QSRTInIcePulses",
        OutputName=OutputPulses,
        Multiplicity=5,
        TimeWindow=4000*I3Units.ns,
        XYDist=300*I3Units.m,
        ZDomDist=15,
        TimeCone=1000*I3Units.ns,
        SaveSplitCount=True)
