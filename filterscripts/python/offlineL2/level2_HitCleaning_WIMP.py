#!/usr/bin/env python3

###
# A Traysegement that does the IC86:2012 Level2 Processing specific for the WimpGroup 
# Please e-mail Meike de With (meike.de.with@desy.de) if you have any questions about this tray segment
###

from icecube import icetray, dataclasses
from I3Tray import I3Units

######################## MAIN ################################
@icetray.traysegment #This should be the main routine 
def WimpHitCleaning(tray, name,
  seededRTConfig,
  Pulses = "SplitInIcePulses",
  SRTPulses="SRTInIcePulses",
  If=lambda f: True,
  suffix = '_WIMP'): 
  
  #tray.AddSegment(BasicCleaning, name+"_BasicCleaning",
  #  If = If,
  #  suffix = suffix,
  #  InputSRTPulses = SRTPulses,
  #  TWSRTOfflinePulses = "TWSRTOfflinePulses"+suffix,
  #)

  tray.AddSegment(FiniteRecoCleaning, name+"_FiniteRecoCleaning",
    seededRTConfig = seededRTConfig,
    If = If,
    suffix = "_FR"+suffix,
    InputPulses = Pulses,
    TWOfflinePulses_FR = "TWOfflinePulses_FR"+suffix,
    RTTWOfflinePulses_FR = "RTTWOfflinePulses_FR"+suffix,
  )

########################### BASIC CLEANING DEF ########################

# This is the cleaning for Linefit, SPESingle, SPE2, it was taken from the 2011 L2 (std-processing/releases/V12-03-00/python/level2_HitCleaning.py) 
@icetray.traysegment
def BasicCleaning(tray, name,
  If = lambda f: True,
  suffix = '',
  InputSRTPulses = '',
  TWSRTOfflinePulses = "TWSRTOfflinePulses"):

    # trigger ids    nk: moved from wg globals
    deepcoreconfigid = 1011
    inicesmtconfigid = 1006
    inicestringconfigid = 1007
    slowparticleconfigid = 24002
    volumetriggerconfigid = 21001
 
    icetray.load('static-twc', False)
 
    tray.AddModule('I3StaticTWC<I3RecoPulseSeries>', name + '_StaticTWC',
      InputResponse = InputSRTPulses,
      OutputResponse = TWSRTOfflinePulses,
      TriggerConfigIDs = [inicesmtconfigid,inicestringconfigid,deepcoreconfigid,volumetriggerconfigid], # ! allow for multiple triggers
      TriggerName = 'I3TriggerHierarchy',
      WindowMinus = 4000, # ! align trigger readout start       
      WindowPlus = 10000, # ! conservative time window         
      FirstTriggerOnly = True, # ! based times relative to 1st trigger
      If = If,
      )


########################### FINITE RECO CLEANING DEF ##################

@icetray.traysegment
def FiniteRecoCleaning(tray, name,
  seededRTConfig,
  If = lambda f: True,
  suffix = '',
  InputPulses = '',
  TWOfflinePulses_FR = "TWOfflinePulses_FR",
  RTTWOfflinePulses_FR = "RTTWOfflinePulses_FR"):

    # Load dependencies.
    from icecube import STTools
    #icetray.load('SeededRTCleaning', False)
    icetray.load('static-twc', False)
 
    # trigger ids    nk: moved from wg globals
    deepcoreconfigid = 1011
    inicesmtconfigid = 1006
    inicestringconfigid = 1007
    slowparticleconfigid = 24002
    volumetriggerconfigid = 21001
 
 
      # This is the TW cleaning for FiniteReco, it was taken from the 2011 L2 (std-processing/releases/V12-03-00/python/Level2_HitCleaning.py) and is optimized for FiniteReco
    tray.AddModule('I3StaticTWC<I3RecoPulseSeries>', name + '_StaticTWC_FR',
        InputResponse = InputPulses,
        OutputResponse = TWOfflinePulses_FR,
        TriggerConfigIDs = [inicesmtconfigid, inicestringconfigid, deepcoreconfigid, volumetriggerconfigid],         # All in ice triggers
        TriggerName = 'I3TriggerHierarchy',
        WindowMinus = 4000,
        WindowPlus = 6000,      
        FirstTriggerOnly = True,   # base window on first inice trigger only
        If = If,
    )
 
    # SeededRT with these parameters is equivalent to ClassicRT
    # (this was NOT taken from the 2011 L2, the values are from the
    # SeededRTCleaning RELEASE_NOTES voor V02-01-01).
    tray.AddModule('I3SeededRTCleaning_RecoPulseMask_Module', name + '_ClassicRT_FR',
        InputHitSeriesMapName  = TWOfflinePulses_FR,
        OutputHitSeriesMapName = RTTWOfflinePulses_FR,
        STConfigService        = seededRTConfig,
        SeedProcedure          = 'AllCoreHits',
        NHitsThreshold         = 1,
        MaxNIterations         = 0,
        Streams                = [icetray.I3Frame.Physics],
        If = If
    )
    #tray.AddModule("I3SeededRTHitMaskingModule", name + '_ClassicRT_FR',
        #InputResponse = TWOfflinePulses_FR,
        #OutputResponse = RTTWOfflinePulses_FR,
        #Seeds = "AllCore",
        #MaxIterations = 0,
        #HLCCoreThreshold = 1,
        #If = If,
    #)
  
  
