from icecube import icetray
@icetray.traysegment
def FPFilter(tray, name, If = lambda f: True):

    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)

    tray.AddModule("I3FilterModule<I3BoolFilter>", name + "_FaintParticleTriggerFilter",
    DecisionName = filter_globals.FPFilter,
    DiscardEvents = False,
    Boolkey = filter_globals.faintparticletriggered,
    TriggerEvalList = [filter_globals.faintparticletriggered],
    If = If,
    )
