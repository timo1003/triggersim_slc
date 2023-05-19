from icecube import icetray

## LowUpFilter for 2013                                                        
@icetray.traysegment
def LowUpFilter(tray, name, If=lambda f: True):

  from icecube.filterscripts import filter_globals
  from I3Tray import I3Units
  icetray.load("filterscripts",False)

  tray.AddModule("I3FilterModule<I3LowUpFilter_13>", name+"LowUpFilter",
    TriggerEvalList = [filter_globals.inicesmttriggered,
		      filter_globals.inicestringtriggered,
		      filter_globals.deepcoresmttriggered,
		      filter_globals.volumetrigtriggered], # input response trigger list
    DecisionName = filter_globals.LowUpFilter, #switch for filter_globals.LowUpFilter                                                       
    Pulses = filter_globals.CleanedMuonPulses, # input response pulses
    RecoTrackNameList = [filter_globals.muon_llhfit,
			filter_globals.muon_linefit], # list of RecoTracks to evaluate                                                     
    nchanCut = 5, # default parameter                        
    zenithCut = 80*I3Units.degree, # default parameter       
    zExtensionCut = 600.0*I3Units.m, # default parameter 
    timeExtensionCut = 4000.0*I3Units.ns, # default parameter                                                                               
    zTravelCut = -10*I3Units.m, # Tuning parameter           
    zMaxCut = 440*I3Units.m, # default parameter            
    ISCrit = True, # default parameter                       
    If = If)
