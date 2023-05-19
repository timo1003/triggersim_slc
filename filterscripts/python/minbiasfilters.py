from icecube import icetray

@icetray.traysegment
def MinBiasFilters(tray, name, If=lambda f: True):

    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)

    tray.AddModule("I3FilterModule<I3FilterMinBias>",
                   name + "FilterminbiasFilter",
                   DecisionName = filter_globals.FilterMinBias,
                   If = If)


@icetray.traysegment
def ScintMinBiasFilters(tray, name, If=lambda f: True):

    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)


    tray.AddModule("I3FilterModule<I3BoolFilter>", name+"ScintMinBiasTrigFilter",
                   DecisionName=filter_globals.ScintMinBiasFilter,
                   DiscardEvents=False,
                   Boolkey=filter_globals.scintminbiastriggered,
                   If=If
                   )

