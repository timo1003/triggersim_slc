from icecube import icetray

# High Charge Filter Traysegment - 2017/Pass2

@icetray.traysegment
def HighQFilter(tray,name, pulses='RecoPulses',If = lambda f: True):
    """
    Traysegment for a high charge filter (formerly EHE).
    """    
    # load needed libs, the "False" suppresses any "Loading..." messages
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)
    
    from icecube import VHESelfVeto

    HighQFilter_threshold = 1000.0
    
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
        Output=filter_globals.homogenized_qtot,
        If = If_with_triggers)

    tray.AddModule("I3FilterModule<I3HighQFilter_17>",
                   name+"HighQFilter",
                   MinimumCharge = HighQFilter_threshold,
                   ChargeName = filter_globals.homogenized_qtot,
                   TriggerEvalList = TriggerEvalList,
                   DecisionName = filter_globals.HighQFilter,
                   If = If)

