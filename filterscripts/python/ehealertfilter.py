
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
# This segment will run the necessary modules in order to determine      #
# if the event passes EHE Online alert criteria.  This segment presently #
# requires one to run the ehefilter already.                             #
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#

from icecube import icetray
from icecube.filterscripts import filter_globals
import math

#
#   Define my precondition.
#
#  EHEAlertFilter -- Only run if NPE threshold high enough                              
# Note: this threshold higher than EHEFilter   

def RunEHEAlertFilter(frame):
    if 'PoleEHESummaryPulseInfo' not in frame:
        return False
    if filter_globals.EHEFilter not in frame:
        return False
    # Check EHE filter first, it's low rate to start...bool in frame here          
    ehefilterflag = frame[filter_globals.EHEFilter].value
    if not ehefilterflag:
        return False
    npe    = frame['PoleEHESummaryPulseInfo'].GetTotalBestNPEbtw()
    if math.isnan(npe): return False
    if npe <= 0:        return False
    lognpe = math.log10(npe)
    return lognpe >= 3.6



#----------------------------------------------#
# Run EHE Alert
#----------------------------------------------#
@icetray.traysegment
def EHEAlertFilter(tray, name, 
                   pulses         = 'CleanedMuonPulses',
                   portia_pulse   = 'EHEBestPortiaPulse',   # Maybe this should be 'Pole'
                   portia_summary = 'PoleEHESummaryPulseInfo',
                   split_dom_map  = 'splittedDOMMap',
                   If = lambda f: True):
    
    # Some necessary stuff
    from icecube import dataclasses, linefit
    from icecube.icetray import OMKey, I3Units
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)
    icetray.load("portia",False)
    icetray.load("ophelia",False)
    from icecube.STTools.seededRT.configuration_services import I3DOMLinkSeededRTConfigurationService

    # Get the largest OM Key in the frame
    tray.AddModule("I3PortiaEventOMKeyConverter", name + "portiaOMconverter",
                   InputPortiaEventName = portia_summary,
                   OutputOMKeyListName = "LargestOMKey",
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )

    # Static time window cleaning
    tray.AddModule("I3EHEStaticTWC", name + "portia_static",
                   InputPulseName = portia_pulse,
                   InputPortiaEventName = portia_summary,
                   outputPulseName = name + "BestPortiaPulse_BTW",
                   TimeInterval = 500.0 * I3Units.ns, #650, now no interval cut
                   TimeWidnowNegative =  -2000.0 * I3Units.ns,
                   TimeWindowPositive = 6400.0 * I3Units.ns,
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )

    # Convert portia pulses
    tray.AddModule("I3OpheliaConvertPortia", name + "portia2reco",
                   InputPortiaPulseName = name + "BestPortiaPulse_BTW",
                   OutputRecoPulseName = name + "RecoPulseBestPortiaPulse_BTW",
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )

    # Run delay cleaning
    tray.AddModule("DelayCleaningEHE", name + "DelayCleaning",
                   InputResponse = name + "RecoPulseBestPortiaPulse_BTW",
                   OutputResponse = name + "RecoPulseBestPortiaPulse_BTW_CleanDelay",
                   Distance = 200.0 * I3Units.m, #156m default
                   TimeInterval = 1800.0 * I3Units.ns, #interval 1.8msec
                   TimeWindow = 778.0 * I3Units.ns, #778ns default
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )

    seededRTConfigEHE = I3DOMLinkSeededRTConfigurationService(
        ic_ic_RTRadius              = 150.0*I3Units.m,
        ic_ic_RTTime                = 1000.0*I3Units.ns,
        treat_string_36_as_deepcore = False,
        useDustlayerCorrection      = True, # EHE use the dustlayer correction!
        allowSelfCoincidence        = True
        )
    
    tray.AddModule('I3SeededRTCleaning_RecoPulse_Module', name+'Isolated_DelayClean',
                   InputHitSeriesMapName  = name + "RecoPulseBestPortiaPulse_BTW_CleanDelay",
                   OutputHitSeriesMapName = name + "RecoPulseBestPortiaPulse_BTW_CleanDelay_RT",
                   STConfigService        = seededRTConfigEHE,
                   SeedProcedure          = 'HLCCOGSTHits',
                   MaxNIterations         = -1, # Infinite.
                   Streams                = [icetray.I3Frame.Physics],
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )                   



    # Huber fit
    tray.AddModule("HuberFitEHE", name + "HuberFit",
                   Name = "HuberFit",
                   Distance = 180.0 * I3Units.m, #153m default
                   InputRecoPulses = name + "RecoPulseBestPortiaPulse_BTW_CleanDelay_RT",
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )

    # Debiasing of pulses
    tray.AddModule("DebiasingEHE", name + "Debiasing",
                   OutputResponse = name + "debiased_BestPortiaPulse_CleanDelay",
                   InputResponse = name + "RecoPulseBestPortiaPulse_BTW_CleanDelay_RT",
                   Seed = "HuberFit",
                   Distance = 150.0 * I3Units.m,#116m default
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )
    
    # Convert back to portia pulses to be fed to ophelia
    tray.AddModule("I3OpheliaConvertRecoPulseToPortia", name + "reco2portia",
                   InputRecoPulseName = name + "debiased_BestPortiaPulse_CleanDelay",
                   OutputPortiaPulseName = name + "portia_debiased_BestPortiaPulse_CleanDelay",
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )

    # Run I3EHE First guess module and get final result
    tray.AddModule("I3EHEFirstGuess", name + "reco_improvedLinefit",
                   MinimumNumberPulseDom = 8,
                   InputSplitDOMMapName = split_dom_map,
                   OutputFirstguessName = "PoleEHEOphelia_ImpLF", # Final result
                   OutputFirstguessNameBtw = name + "OpheliaBTW_ImpLF", # Don't Use
                   InputPulseName1 = name + "portia_debiased_BestPortiaPulse_CleanDelay",
                   ChargeOption = 1,
                   LCOption =  False,  
                   InputPortiaEventName =portia_summary,
                   OutputParticleName = "PoleEHEOpheliaParticle_ImpLF", # Final Result
                   OutputParticleNameBtw = name + "OpheliaParticleBTW_ImpLF", # Don't Use
                   NPEThreshold = 0.0,
                   If = (If and (lambda f:RunEHEAlertFilter(f)))
                   )
    

    # Run the alert filter
    tray.AddModule("I3FilterModule<I3EHEAlertFilter_15>","EHEAlertFilter",
                   TriggerEvalList=[filter_globals.inicesmttriggered],
                   DecisionName = filter_globals.EHEAlertFilter,
                   DiscardEvents = False,
                   PortiaEventName = portia_summary,
                   EHEFirstGuessParticleName = "PoleEHEOpheliaParticle_ImpLF",
                   EHEFirstGuessName = "PoleEHEOphelia_ImpLF",
                   If = (If and (lambda f: 'PoleEHEOphelia_ImpLF' in f) # First Guess can fail
                         and (lambda f:RunEHEAlertFilter(f)))
                   )

    # Again for Heartbeat
    tray.AddModule("I3FilterModule<I3EHEAlertFilter_15>","EHEAlertFilterHB",
                   TriggerEvalList=[filter_globals.inicesmttriggered],
                   DecisionName = filter_globals.EHEAlertFilterHB,
                   DiscardEvents = False,
                   PortiaEventName = portia_summary,
                   EHEFirstGuessParticleName = "PoleEHEOpheliaParticle_ImpLF",
                   EHEFirstGuessName = "PoleEHEOphelia_ImpLF",
                   Looser = True, # For Heartbeat ~ 4 events / day
                   #Loosest = True, # For PnF testing ~ 4 events / hour
                   If = (If and (lambda f: 'PoleEHEOphelia_ImpLF' in f) # First Guess can fail
                         and (lambda f:RunEHEAlertFilter(f)))
                   )
    
    # Clean up garbage
    tray.AddModule("Delete", "EHEAlert_Cleanup",
                   keys = ['splittedDOMMap',
                           'EHEBestPortiaPulse',
                           'LargestOMKey',
                           'HuberFit',
                           name + 'BestPortiaPulse_BTW',
                           name + 'RecoPulseBestPortiaPulse_BTW',
                           name + 'RecoPulseBestPortiaPulse_BTW_CleanDelay',
                           name + 'RecoPulseBestPortiaPulse_BTW_CleanDelay_RT',
                           name + 'debiased_BestPortiaPulse_CleanDelay',
                           name + 'portia_debiased_BestPortiaPulse_CleanDelay',
                           name + 'OpheliaBTW_ImpLF',
                           name + 'OpheliaParticleBTW_ImpLF',
                           name + "DiscardedRecoPulse", 
                           ]
                   )
    
    
