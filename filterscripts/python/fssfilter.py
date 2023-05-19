from icecube import icetray
from icecube.filterscripts import filter_globals

##Icetray Segment for Full Sky Starting (FSS) Filter for Season 2013


@icetray.traysegment
def FSSFilter(tray, name, pulses=filter_globals.SplitUncleanedInIcePulses, If = lambda f: True, ic79_geometry = False):
    
    icetray.load("filterscripts",False)
    icetray.load("static-twc",False)
    icetray.load("finiteReco",False)
    
    def FiniteRecoPick(frame):
        if (frame.Has(filter_globals.FSSCandidate) and frame[filter_globals.FSSCandidate].value):
            return True
        return False
    
    pulses_hlc = name + '_pulses_hlc'
    pulses_slc = name + '_pulses_slc'
    tray.AddModule('I3LCPulseCleaning', 'LCCleaning',
                   Input=filter_globals.SplitUncleanedInIcePulses,
                   OutputHLC=pulses_hlc,
                   OutputSLC=pulses_slc,
                   If = If
                   )

    tray.AddModule("I3FilterModule<I3FSSCandidate_13>",name + "_candidate",
                   TriggerEvalList = [filter_globals.inicesmttriggered,filter_globals.deepcoresmttriggered,filter_globals.inicestringtriggered],
                   DecisionName = filter_globals.FSSCandidate,
                   DiscardEvents = False,
                   MuonTrackFitName = filter_globals.muon_llhfit,
                   IceCubeResponseKey = pulses_hlc, #HLC only
                   NSideVetoLayers = 1,
                   NTopVetoLayers = 5,
                   If = If,
                   )
    
    tray.AddModule("I3StaticTWC<I3RecoPulseSeries>",name + "_static-twc",
                   InputResponse = pulses, #HLC+SLC
                   OutputResponse = name + "_STWC_pulses",
                   TriggerConfigIDs = [filter_globals.inicesmtconfigid,
                                         filter_globals.deepcoreconfigid,
                                         filter_globals.inicestringconfigid],
                   TriggerName = filter_globals.triggerhierarchy,
                   WindowMinus = 4000,        
                   WindowPlus = 6000,  
                   FirstTriggerOnly = True, # ! base window on first inIce trigger only
                   If = lambda f: If(f) and FiniteRecoPick(f),
                   )
    
    tray.AddModule("I3IsolatedHitsCutModule<I3RecoPulse>",name + "_CRTCleaning",
                   InputResponse = name + "_STWC_pulses",
                   OutputResponse = name + "_CRT_pulses",
                   RTRadius = 150,
                   RTTime = 1000,
                   RTMultiplicity = 1,
                   UseWidth = 0,
                   If = lambda f: If(f) and FiniteRecoPick(f),
                   )
    
    tray.AddModule("I3StartStopPoint",name + "_VertexReco",
                   Name = filter_globals.muon_llhfit, 
                   InputRecoPulses = name + "_CRT_pulses", 
                   ExpectedShape = 70, 
                   CylinderRadius = 200, 
                   If = lambda f: If(f) and FiniteRecoPick(f),
                   )
    
    tray.AddModule("I3FilterModule<I3FSSFilter_13>",name + "_fRStarting",
                   DecisionName = filter_globals.FSSFilter,
                   DiscardEvents = False,
                   finiteRecoParticleName = filter_globals.muon_llhfit+'_Finite',
                   ##RCut = 600.0,
                   zCut = 400.0,
                   scaleAroundString36 = True,
                   usePolygonCut = True,  
                   #polygonCutStringNumbers = [1,6,50,74,72,78,75,31] if not ic79_geometry else [2,6,50,74,72,78,75,41], 
                   polygonCutScale = 0.9, 
                   If = lambda f: If(f) and FiniteRecoPick(f),
                   )
