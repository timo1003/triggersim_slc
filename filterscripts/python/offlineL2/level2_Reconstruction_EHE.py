from icecube import icetray, dataclasses, linefit, lilliput, shield, phys_services
from icecube.icetray import OMKey, I3Units

from icecube.filterscripts.offlineL2 import Globals
import icecube.lilliput.segments

#***************************************************************  
# Jan's closest tank calculation                         
#***************************************************************         
def closestTank(fr, reco, output):
    if not fr.Has(reco):
        return
    geometry = fr.Get("I3Geometry")
    recofr = fr[reco]
    recov = 10000.0
    test = 0.0
    listofOMs = [om for om in geometry.omgeo.keys() if om.om > 60]
    for oms in listofOMs:
        test = phys_services.I3Calculator.closest_approach_distance(recofr, geometry.omgeo[oms].position)
        if test < recov:
            recov = test
    fr[output] = dataclasses.I3Double(recov)
            

@icetray.traysegment
def ReconstructionEHE(tray, name, Pulses = 'EHETWCInIcePulsesSRT',
                      suffix = 'EHE', LineFit = 'LineFit', 
                      SPEFitSingle = 'SPEFitSingle', SPEFit = 'SPEFit12',
                      N_iter = 12,  If = lambda f: True):

    #***************************************************************  
    #     EHE line fit                                                               
    #***************************************************************                                 
    tray.AddModule("I3EHEFirstGuess", name + "reco-split",
                   MinimumNumberPulseDom = 8,
                   InputSplitDOMMapName = "splittedDOMMapSRT",
                   OutputFirstguessName = "EHEOpheliaSRT",
                   OutputFirstguessNameBtw = "EHEOpheliaBTWSRT",
                   InputPulseName1 = "EHEBestPortiaPulseSRT",
                   ChargeOption = 1,
                   LCOption = True,
                   InputPortiaEventName = "EHEPortiaEventSummarySRT",
                   NPEThreshold = 0.0,
                   OutputParticleName = "EHEOpheliaParticleSRT",       #this is not BTW applied one   
                   OutputParticleNameBtw = "EHEOpheliaParticleBTWSRT", #this is BTW applied one 
                   If = If )


    tray.AddSegment( linefit.simple, LineFit + suffix, inputResponse = Pulses, fitName = LineFit + suffix, If = If )
    
    tray.AddSegment(lilliput.segments.I3SinglePandelFitter, SPEFitSingle + suffix,
                    fitname = SPEFitSingle + suffix,
                    pulses = Pulses,
                    seeds = [LineFit + suffix],
                    If = If
                    )
    
    tray.AddSegment(lilliput.segments.I3IterativePandelFitter, SPEFit + suffix,
                    fitname = SPEFit + suffix,
                    pulses = Pulses,
                    n_iterations = N_iter,
                    seeds = [ SPEFitSingle + suffix ],
                    If = If
                    )
    
    


    #########################################################################
    # modified improvedLineFit
    # Convert back reco pulse to portia pulse to be reconstructed EHE LineFit
    #########################################################################
    tray.AddModule("I3OpheliaConvertRecoPulseToPortia", name + "reco2portia",
                   InputRecoPulseName = "EHEdebiased_BestPortiaPulseSRT_CleanDelay",
                   OutputPortiaPulseName = "EHEportia_debiased_BestPortiaPulseSRT_CleanDelay",
                   If = If)
    #########################################################################
    tray.AddModule("I3EHEFirstGuess", name + "reco_improvedLinefit",
                   MinimumNumberPulseDom = 8,
                   InputSplitDOMMapName = "splittedDOMMapSRT",
                   OutputFirstguessName = "EHEOpheliaSRT_ImpLF", #This is the final reconstruction results
                   OutputFirstguessNameBtw = "EHEOpheliaBTWSRT_ImpLF", #This should not be used
                   InputPulseName1 = "EHEportia_debiased_BestPortiaPulseSRT_CleanDelay",
                   ChargeOption = 1,
                   LCOption =  False,  # Is this OK?
                   InputPortiaEventName ="EHEPortiaEventSummarySRT",
                   OutputParticleName ="EHEOpheliaParticleSRT_ImpLF", #This is the final reconstruction resuls in the form of I3Particle
                   OutputParticleNameBtw = "EHEOpheliaParticleBTWSRT_ImpLF",#this should not be used
                   NPEThreshold = 0.0,
                   If = If )
    


    #***************************************************************  
    #     IceTop veto information
    #***************************************************************                                 
    tray.AddModule("I3ShieldDataCollector", name + "shield_SPE12",
                   InputRecoPulses="IceTopDSTPulses",
                   InputTrack=SPEFit + suffix,
                   OutputName="EHEDSTShieldParameters_SPE12",
                   If = If)

    tray.AddModule("I3ShieldDataCollector", name + "shield_ImpLF",
                   InputRecoPulses="IceTopDSTPulses",
                   InputTrack = "EHEOpheliaParticleSRT_ImpLF",
                   OutputName="EHEDSTShieldParameters_ImpLF",
                   If = If)

    tray.AddModule("Delete", name + "EHE_Cleanup",
                   keys=['EHEInIcePulsesSRT', 'EHETWCInIcePulsesSRT',
                         'EHEdebiased_BestPortiaPulseSRT_CleanDelay',
                         'EHEportia_debiased_BestPortiaPulseSRT_CleanDelay',
                         'EHEOpheliaBTWSRT_ImpLF', 'EHEOpheliaParticleBTWSRT_ImpLF'
                         ])
# nk: this is taken from the main.py script supplied by ehe
    tray.AddModule("Delete", name + "EHE_Master_Cleanup",
               keys=['EHECalibratedATWD_Wave',
                     'EHECalibratedFADC_Wave',
                     'HLCOfflineCleanInIceRawDataWODC',
                     'CleanInIceRawData',
                     'SRTInIcePulses_WODC'
                     ])


