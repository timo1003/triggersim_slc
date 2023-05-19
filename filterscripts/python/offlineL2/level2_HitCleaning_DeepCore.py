from icecube import icetray, dataclasses
from icecube.icetray import I3Units


@icetray.traysegment
def DeepCoreHitCleaning(tray, name, Pulses = 'SRTInIcePulses',
                        SRTTWOfflinePulsesDC = 'SRTTWOfflinePulsesDC',
                        DeepCoreTrig = 1011,
                        I3TriggerHierarchy = 'I3TriggerHierarchy',
                        If = lambda f: True,
                        ):

    icetray.load('static-twc', False)
#    icetray.load('SeededRTCleaning', False)

    tray.AddModule('I3StaticTWC<I3RecoPulseSeries>', name + '_StaticTWC_DC',
                   InputResponse = Pulses,
                   OutputResponse = SRTTWOfflinePulsesDC,
                   TriggerConfigIDs = [DeepCoreTrig], 
                   TriggerName = I3TriggerHierarchy,  
                   WindowMinus = 5000,                
                   WindowPlus = 4000,
                   If = If,
                   )

# nk: already done in offline base proc, same setting. input to this segment is SRTInIcePulses now
#    tray.AddModule( 'I3SeededRTHitMaskingModule', name + '_SeededRTCleaning_DC',
#                    InputResponse = TWOfflinePulsesDC, # ! Name of input pulse series
#                    OutputResponse = SRTTWOfflinePulsesDC,      # ! Name of output pulse series
#                    RTRadius = 150,                        # ! Radius for RT cleaning
#                    RTTime = 1000,                       # ! Time for RT cleaning
#                    MaxIterations = 3,                          # ! 3 iterations are enough
#                    Seeds = 'HLCcore',                  # ! do not use all HLC hits as seed
#                    HLCCoreThreshold = 2,                          # Default
#                    If = If,
#                    )


