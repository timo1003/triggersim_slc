from icecube import icetray
from icecube.filterscripts import filter_globals

@icetray.traysegment
def CosmicRayFilter(tray, name,
    Pulses = filter_globals.CleanedHLCTankPulses,
    If     = lambda f: True):
  
    from icecube.filterscripts import filter_globals
    icetray.load('filterscripts', False)

    #Perform CR filtering on the IceTopSplit
    tray.AddModule('I3FilterModule<I3CosmicRayFilter_13>', name + '_CosmicRayFilter',
        TriggerEvalList    = [filter_globals.inicesmttriggered,
                              filter_globals.icetopsmttriggered],
        DecisionName       = filter_globals.CosmicRayFilter,
        TriggerKey         = filter_globals.triggerhierarchy,
        IceTopPulseMaskKey = Pulses,
        If                 = If
        )
