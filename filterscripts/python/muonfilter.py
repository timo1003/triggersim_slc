from icecube import icetray

# Muon Filter Traysegment - 2013 Example, based on 2012 muon filter

@icetray.traysegment
def MuonFilter(tray,name, pulses='RecoPulses',If = lambda f: True):
    """
    Traysegment for the 2012 (Dragon processing) muon filter. No nch decision is made
    as in 2011 (this may change with the SDST decision).
    """
    # load needed libs, the "False" suppresses any "Loading..." messages
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)
  
    tray.AddModule("I3FilterModule<I3MuonFilter_13>",name + "_Muonfilter",
                   TriggerEvalList = [filter_globals.inicesmttriggered],
                   DecisionName = filter_globals.MuonFilter,
                   IceCubeResponseKey = pulses,
                   PriParticleKey = filter_globals.muon_llhfit,
                   LLHFitParamsKey = filter_globals.muon_llhfit+'FitParams',
                   If = If
                   )
  


