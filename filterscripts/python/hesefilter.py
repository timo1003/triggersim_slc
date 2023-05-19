from icecube import icetray

# HESE Filter Traysegment - 2015 Example

@icetray.traysegment
def HeseFilter(tray,name, pulses='RecoPulses',If = lambda f: True):
    """
    Traysegment for a potential HESE filter. NEW
    """    
    # load needed libs, the "False" suppresses any "Loading..." messages
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)
    icetray.load("cscd-llh",False)
    
    from icecube import VHESelfVeto
    from icecube import clast
    from icecube import linefit,lilliput
    from icecube import dataclasses
    
    minimum_charge=1500.
    
    TriggerEvalList = [filter_globals.inicesmttriggered] # work on SMT8 triggers
    def If_with_triggers(frame):
        if not If(frame):
            return False
        for trigger in TriggerEvalList:
            if frame[trigger].value:
                return True
        return False
    
    # apply the veto 
    tray.AddModule('HomogenizedQTot', name+'_qtot_total',
        Pulses=pulses,
        Output='HESE_HomogenizedQTot',
        If = If_with_triggers)

    tray.AddModule('I3LCPulseCleaning', name+'_lcclean1',
        Input=pulses,
        OutputHLC=pulses+'HLC'+name,
        OutputSLC=pulses+'SLC'+name,
        If = If_with_triggers)

    tray.AddModule('VHESelfVeto', name+'_selfveto',
        Pulses=pulses+'HLC'+name,
        OutputBool='HESE_VHESelfVeto',
        OutputVertexTime='HESE_VHESelfVetoVertexTime',
        OutputVertexPos='HESE_VHESelfVetoVertexPos',
        If = If_with_triggers)
  
    # add CausalQTot frame
    tray.AddModule('HomogenizedQTot', name+'_qtot_causal',
        Pulses=pulses,
        Output='HESE_CausalQTot',
        VertexTime='HESE_VHESelfVetoVertexTime',
        If = If_with_triggers)
    
    # only calculate the LLH ratio inputs and ratio if we need it
    def filter_llh_ratio_condition(frame):
        if "HESE_VHESelfVeto" not in frame:
            return False
        if frame["HESE_VHESelfVeto"].value:
            # veto==True means "vetoed", so ignore it
            return False
        if frame["HESE_CausalQTot"].value < minimum_charge:
            return False
        return True
    
    # run CascadeLlhVertexFit reconstruction 
    tray.AddModule('I3CLastModule', name+'_CascadeLast',
               InputReadout=pulses+'HLC'+name, Name='HESE_CascadeLast'+name,
               If = lambda f: If_with_triggers(f) and filter_llh_ratio_condition(f))
    tray.AddModule( 'I3CscdLlhModule', name+'_CascadeLlh',
               InputType = 'RecoPulse', # ! Use reco pulses
               RecoSeries = pulses+'HLC'+name, # ! Name of input pulse series
               FirstLE = True, # Default
               SeedWithOrigin = False, # Default
               SeedKey = 'HESE_CascadeLast'+name, # ! Seed fit - CLast reco
               MinHits = 8, # ! Require 8 hits
               AmpWeightPower = 0.0, # Default
               ResultName = 'HESE_CascadeLlhVertexFit', # ! Name of fit result
               Minimizer = 'Powell', # ! Set the minimizer to use
               PDF = 'UPandel', # ! Set the pdf to use
               ParamT = '1.0, 0.0, 0.0, false',   # ! Setup parameters
               ParamX = '1.0, 0.0, 0.0, false',   # ! Setup parameters
               ParamY = '1.0, 0.0, 0.0, false',   # ! Setup parameters
               ParamZ = '1.0, 0.0, 0.0, false',   # ! Setup parameters
               If = lambda f: If_with_triggers(f) and filter_llh_ratio_condition(f),
               )   
 
    # run SPEFit2 reconstruction
    tray.AddSegment( linefit.simple, name+'_MuonImprovedLineFit',
                inputResponse = pulses+'HLC'+name, fitName = 'HESE_MuonImprovedLineFit',
                If = lambda f: If_with_triggers(f) and filter_llh_ratio_condition(f))

    tray.AddSegment( lilliput.segments.I3SinglePandelFitter, name+'_SPEFitSingle',
                fitname = 'HESE_SPEFitSingle', # the output frame object name
                pulses = pulses+'HLC'+name, seeds =  ['HESE_MuonImprovedLineFit'],
                If = lambda f: If_with_triggers(f) and filter_llh_ratio_condition(f))

    tray.AddSegment( lilliput.segments.I3IterativePandelFitter, name+'_SPEFit2',
                fitname = 'HESE_SPEFit2', # the output frame object name
                pulses = pulses+'HLC'+name, n_iterations = 2, seeds = ['HESE_SPEFitSingle'],
                If = lambda f: If_with_triggers(f) and filter_llh_ratio_condition(f))
    
    # calculate the loglikelihood ratio of CascadeLlhVertexFit to SPEFit2
    # events with a positive llh_ratio are more likely track-like
    def calculateLlhRatio(frame):
        cascadefitpar = frame['HESE_CascadeLlhVertexFitParams'].NegLlh
        trackfitpar = frame['HESE_SPEFit2FitParams'].logl
        llhratio = cascadefitpar - trackfitpar
        frame["HESE_llhratio"] = dataclasses.I3Double(llhratio)
    
    tray.AddModule(calculateLlhRatio, name+"_calcLlhRatio",
        If = lambda f: If_with_triggers(f) and filter_llh_ratio_condition(f))

    tray.AddModule("I3FilterModule<I3HeseFilter_15>",
                   name+"HeseFilter",
                   MinimumCharge = minimum_charge,
                   VetoName = "HESE_VHESelfVeto",
                   ChargeName = "HESE_CausalQTot",
                   TriggerEvalList = TriggerEvalList,
                   DecisionName = filter_globals.HESEFilter,
                   If = If)

    def cleanup(frame, Keys=[]):
        for key in Keys:
            if key in frame:
                del frame[key]

    # cleanup all filter output if we just made a negative filter decision
    tray.AddModule(cleanup, name+"_cleanup", Streams=[icetray.I3Frame.Physics],
        Keys = filter_globals.hese_reco_keeps,
        If = lambda f: If_with_triggers(f) and (not f[filter_globals.HESEFilter].value)
        )
        
    # cleanup things we don't need after this
    tray.AddModule(cleanup, name+"_cleanup2", Streams=[icetray.I3Frame.Physics],
        Keys = [
            pulses+'HLC'+name,
            pulses+'SLC'+name,
            "HESE_CascadeLast"+name,
        ],
        If = If_with_triggers
        )
