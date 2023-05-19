from icecube import icetray, dataclasses
from icecube import dipolefit, clast, tensor_of_inertia, linefit, lilliput
from icecube.icetray import I3Units
import icecube.lilliput.segments

@icetray.traysegment
def OfflineDeepCoreReco(tray, name, If = lambda f: True, suffix = '',
                        Pulses = '',
                                                ):

    tray.AddModule('I3DipoleFit', name + '_DipoleFit' + suffix,
                   Name = 'DipoleFit' + suffix,
                   InputRecoPulses = Pulses,   
                   AmpWeightPower = 0.0,
                   DipoleStep = 0,
                   MinHits = 5,   
                   If = If,
                   )

    tray.AddModule('I3CLastModule', name+'_CascadeLast' + suffix,
                   Name = 'CascadeLast' + suffix,
                   InputReadout = Pulses,
                   MinHits = 3, #Default 
                   AmplitudeOption = 1, #Default
                   AmplitudeWeight = 1.0, #Default
                   AmandaMode = False, #Default   
                   DirectHitRadius = 300.0*I3Units.m, #Default
                   DirectHitWindow = 200.0*I3Units.ns, #Default
                   DirectHitThreshold = 3, #Default
                   AmEnergyParam0 = 1.448, #Default
                   AmEnergyParam1 = -1.312, #Default
                   AmEnergyParam2 = 0.9294, #Default
                   AmEnergyParam3 = -0.1696, #Default
                   AmEnergyParam4 = 0.001123, #Default
                   AmEnergyParam5 = 0.0, #Default
                   EnergyParam0 = -0.431, #Default
                   EnergyParam1 = 1.842, #Default  
                   EnergyParam2 = -0.49199, #Default
                   EnergyParam3 = 0.07499, #Default 
                   EnergyParam4 = 0.0, #Default
                   EnergyParam5 = 0.0, #Default
                   If = If,
                   )

    tray.AddModule('I3TensorOfInertia', name + '_ToI' + suffix,
                   InputReadout = Pulses,
                   Name = 'ToI'+suffix,  
                   MinHits = 3,
                   AmplitudeOption = 1,
                   AmplitudeWeight = 1,
                   InputSelection = '',
                   If = If,
                   )

    tray.AddSegment( linefit.simple,'LineFit'+suffix, inputResponse = Pulses, fitName = 'LineFit'+suffix, If = If)

    tray.AddSegment(lilliput.segments.I3SinglePandelFitter, 'SPEFitSingle'+suffix,
                    fitname = 'SPEFitSingle'+suffix,
                    pulses = Pulses,
                    seeds = ['LineFit'+suffix],
                    If = If
                    )
    
    tray.AddSegment(lilliput.segments.I3IterativePandelFitter, 'SPEFit2'+suffix,
                    fitname = 'SPEFit2'+suffix,
                    pulses = Pulses,
                    n_iterations = 2,
                    seeds = [ 'SPEFitSingle'+suffix ],
                    If = If
                    )

    #use only first hits.  Makes sense for an SPE likelihood
    tray.AddModule('CramerRao', 'SPE2'+suffix + '_SPEFitCramerRao' + suffix,
                   InputResponse = Pulses,
                   InputTrack = 'SPEFit2'+suffix,
                   OutputResult = 'SPEFit2CramerRao'+suffix,
                   AllHits = False, # ! doesn't make sense to use all hit for SPE pdf
                   DoubleOutput = False, # Default
                   z_dependent_scatter = True, # Default
                   If = If,
                   )
    
    tray.AddModule("Delete","DC_Cleanup",keys=['ToI_DCEval2','ToI_DCEval3','LineFit_DC_debiasedPulses','LineFit_DC_linefit_final_rusage','DeepCoreL2Reco_DipoleFit_DC_rusage'])
