from icecube import icetray
@icetray.traysegment
def FPTFilter(tray, name, If = lambda f: True):

    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)

    tray.AddModule("I3FilterModule<I3BoolFilter>", name + "_SlowPartTriggerFilter",
    DecisionName = filter_globals.SlopFilter,
    DiscardEvents = False,
    Boolkey = filter_globals.slowparticletriggered,
    TriggerEvalList = [filter_globals.slowparticletriggered],
    If = If,
    )
