from icecube import icetray

@icetray.traysegment
def VEFFilter(tray, name, pulses='RecoPulses' ,singlestring = False, If=lambda f: True):
    """
    This tray segment is the Vertical Event Filter segment. 
    """
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)

    tray.AddModule("I3FilterModule<I3VEFFilter_13>", name+"_VEFFilter",
                   TriggerEvalList = [filter_globals.inicestringtriggered],
                   DecisionName = filter_globals.VEFFilter,
                   LinefitCut = 1.2,
                   PoleMuonLlhFit = filter_globals.muon_llhfit,
                   PoleMuonLinefit = filter_globals.muon_linefit, 
                   MuonLlhCut = 2.5,
                   DiscardEvents = False,
                   TopLayerDOMCut = 5,
                   RecoPulsesKey = pulses,
                   SingleStringRequirement = singlestring,
                   If = If
                   )

