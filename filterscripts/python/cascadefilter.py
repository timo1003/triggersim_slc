from icecube import icetray
from icecube.filterscripts import filter_globals

# written by Lukas Schulte <lschulte@physik.uni-bonn.de>
# changes to If condition as per Erik B. suggestion done by MLB on Jan22, 2013

@icetray.traysegment
def CascadeFilter(tray,name,
                  pulses='RecoPulses',
                  muon_llhfit_name=filter_globals.muon_llhfit,
                  output_pulses_HLC=None,
                  doCleanup=True,
                  If=lambda f: True):
    """
    This tray segment is a first version of the 2013 cascade filter segment.
    
    :param pulses:
        Name of the I3RecoPulseSeriesMap to work on.
        This filter has been tested in 2011 with uncleaned pulses,
        TW, SRT and TW+SRT-cleaned pulses. It does not work
        too well for TW-cleaned pulses. All other cleanings
        or no cleaning at all is acceptable.
    :param muon_llhfit_name:
        Name of the I3Particle containing the muon llh
        reconstruction result from the muon filter.
    :param output_pulses_HLC:
        Set this to a string to store the HLC cleaned pulses
        for use by other filters downstream.
    :param doCleanup:
        Clean up all "internal" reconstruction reuslts after
        the final filter decision.
    :param If:
        Python function to use as conditional execution test for segment modules.
    """
    
    # load needed libs, the "False" suppresses any "Loading..." messages
    from icecube import (dataclasses, recclasses, clast, linefit, 
                         tensor_of_inertia, CascadeVariables)
    from icecube.common_variables import hit_multiplicity
    from icecube.dataclasses import I3RecoPulseSeriesMap
    
    icetray.load("filterscripts",False)
    icetray.load("DomTools",False)
    icetray.load("cscd-llh",False)
    
    # get rid of SLC launches
    if output_pulses_HLC is None:
        cascadePulseName = pulses+"_HLC"
    else:
        cascadePulseName = output_pulses_HLC
    tray.AddModule("I3LCPulseCleaning", name+"_I3LCPulseCleaning",
                   Input=pulses,
                   OutputHLC=cascadePulseName,
                   OutputSLC="",
                   If=If)
    
    # For calculating NString
    tray.AddSegment(hit_multiplicity.I3HitMultiplicityCalculatorSegment, name+'_HitMult',
    		    PulseSeriesMapName = cascadePulseName,
		    OutputI3HitMultiplicityValuesName = name+'_HitMultiplicityValues',
                    If = If)
    '''
    # Save the kittens. No IcePicks.
    def cascade_nch_check(hit_mult = None, threshold = 8):
        def cascade_nch_check(frame):
	    if frame.Has(hit_mult) and frame.Stop == icetray.I3Frame.Physics:
	    	return frame[hit_mult].n_hit_doms >= threshold
	    else:
	        return False
	return cascade_nch_check
    
    def cascade_nstr_check(hit_mult = None, threshold = 2):
        def cascade_nstr_check(frame):
	    if frame.Has(hit_mult) and frame.Stop == icetray.I3Frame.Physics:
	        return frame[hit_mult].n_hit_strings >= threshold
	    else:
	        return False
	return cascade_nstr_check
    '''
########## MLB 22Jan #########
    def cascade_nch_check(frame, hit_mult = None, threshold = 8):
        returnVal = False
        if frame.Has(hit_mult) and frame.Stop == icetray.I3Frame.Physics:
            if frame[hit_mult].n_hit_doms >= threshold:
                returnVal = True
        return returnVal
    
    def cascade_nstr_check(frame, hit_mult = None, threshold = 2):
        returnVal = False
        if frame.Has(hit_mult) and frame.Stop == icetray.I3Frame.Physics:
            if frame[hit_mult].n_hit_strings >= threshold:
                returnVal = True
        return returnVal
#########################

    # Do CLast - seed for CscdLlh
    tray.AddModule("I3CLastModule", name + "_CLast",
                   InputReadout = cascadePulseName,
                   Name = name + "_CLast",
                   If = lambda f: If(f) and cascade_nstr_check(f, hit_mult=name+'_HitMultiplicityValues', threshold=2)
                   )
    
    # Do Cascade Llh - cut variable
    tray.AddModule("I3CscdLlhModule", name + "_CascadeLlh",
                   InputType =         "RecoPulse",                     # ! Use reco pulses
                   RecoSeries =        cascadePulseName,                # ! Name of pulse series
                   FirstLE =           True,                            # Default
                   SeedWithOrigin =    False,                           # Default
                   SeedKey =           name + "_CLast",                 # ! Seed fit - CLast reco
                   MinHits =           8,                               # ! Require 8 hits
                   AmpWeightPower =    0.0,                             # Default
                   ResultName =        name + "_CascadeLlh",   		# ! Name of fit result
                   Minimizer =         "Powell",                        # ! Set the minimizer to use
                   PDF =               "UPandel",                       # ! Set the pdf to use
                   ParamT =            "1.0, 0.0, 0.0, false",          # ! Setup parameters
                   ParamX =            "1.0, 0.0, 0.0, false",          # ! Setup parameters
                   ParamY =            "1.0, 0.0, 0.0, false",          # ! Setup parameters
                   ParamZ =            "1.0, 0.0, 0.0, false",          # ! Setup parameters
                   If = lambda f: If(f) and cascade_nstr_check(f, hit_mult=name+'_HitMultiplicityValues', threshold=2) and cascade_nch_check(f,hit_mult=name+'_HitMultiplicityValues', threshold=8)
                   )
    
    # Do Tensor of Inertia - cut variable (eigenvalue ratio)
    tray.AddModule("I3TensorOfInertia", name + "_Tensorofinertia",
                   InputReadout = cascadePulseName,
                   Name = name + "_Tensorofinertia",
                   MinHits = 8,
                   If = lambda f: If(f) and cascade_nstr_check(f, hit_mult=name+'_HitMultiplicityValues', threshold=2)
                   )
    
    # Do LineFit - cut variable (velocity)
    tray.AddModule("I3LineFit", name + "_CascadeLinefit",
                   Name = name + "_CascadeLinefit",
                   InputRecoPulses = cascadePulseName,
                   If = lambda f: If(f) and cascade_nstr_check(f, hit_mult=name+'_HitMultiplicityValues', threshold=2)
                   )
    
    # The actual cascade I3FilterModule 
    tray.AddModule("I3FilterModule<I3CascadeFilter_13>", name + "_Cascadefilter",
                   TriggerEvalList = [filter_globals.inicesmttriggered],
                   DecisionName = filter_globals.CascadeFilter,
                   DiscardEvents = False,         # do not discard events here
		   HitMultiplicityKey = name+'_HitMultiplicityValues',		# input (NString)
                   LlhParticleKey = muon_llhfit_name, 				# input
                   LinefitKey = name + "_CascadeLinefit", 			# input
                   CscdLlhFitParams = name + "_CascadeLlhParams", 		# input
                   TensorOfInertiaFitParams = name + "_TensorofinertiaParams", 	# input
		   minNString = 2,		# discard one-string-events
                   cosThetaMax = 0.20,		# separate region 1 and 2
                   CscdrLlh1 = 12.75,		# cut value (region 1 only)
                   CscdrLlh2 = 10.00,		# cut value (region 2 only)
                   ToIEvalRatio = 0.08,		# cut value (region 2 only)
                   LinefitVelocity = 0.08,	# cut value (region 2 only)
                   EvalRatioKey = filter_globals.cascade_toi,       # output (I3Double)
                   LFVelKey = filter_globals.cascade_lfvel,         # output (I3Double)
                   CascadeLlhKey = filter_globals.cascade_cscdllh,  # output (I3Double)
                   If = lambda f: If(f) and cascade_nstr_check(f, hit_mult=name+'_HitMultiplicityValues', threshold=2)
                   )
    
    # Remove CLast results (only needed as seed for CscdLlh)
    if doCleanup:
        tray.AddModule("Delete", name + "_Cleanup",
                       Keys = [name + "_CLast",
                               name + "_CLastParams"],
                       If = If)
