from icecube import icetray
from icecube.icetray import I3Units
icetray.load('coinc-twc', False)

from icecube.filterscripts.offlineL2 import level2_IceTop_globals


@icetray.traysegment
def IceTopCoincTWCleaning(tray, name,
    VEMPulses               = level2_IceTop_globals.icetop_clean_hlc_pulses,
    OfflinePulses           = 'InIcePulses',
    CleanCoincOfflinePulses = level2_IceTop_globals.icetop_clean_coinc_pulses):
    
    tray.AddModule('I3CoincTWC<I3RecoPulseSeries>', name + '_IceTopCoincTWC',
        IceTopVEMPulsesName  = VEMPulses,
        InputResponse        = OfflinePulses,
        OutputResponse       = CleanCoincOfflinePulses,
        Strategy             = 'method2',
        TriggerHierarchyName = 'DSTTriggers',           # ! use these instead of I3TriggerHierarchy
        CleanWindowMaxLength = 6500.0 * I3Units.ns,     # ! Also remove afterlaunches !!
        MaxTimeDiff          = 1500.0 * I3Units.ns,     # ! First IT pulse should be between [-400 ns, 1200 ns ] wrt to IT SMT, 1500 ns is very safe
        WindowMin            = 4780.0 * I3Units.ns,     # Optimized for contained 0-40 degree air showers
        WindowMax            = 7000.0 * I3Units.ns,     # Optimized for contained 0-40 degree air showers
        Stream               = icetray.I3Frame.Physics  # Default
        )
