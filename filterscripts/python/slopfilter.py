#
# modules used for slow particle filtering and processing
#
from icecube import icetray

# SLOP Splitter (generates the p-Frame for the SLOPFilter)
@icetray.traysegment
def SLOPSplitter(tray, name, InputPulses="InIcePulses"):

    from icecube.filterscripts import filter_globals
    icetray.load("trigger-splitter", False)

    tray.AddModule("I3TriggerSplitter", filter_globals.SLOPSplitter,
        SubEventStreamName=filter_globals.SLOPSplitter,
        TrigHierName=filter_globals.qtriggerhierarchy,
        InputResponses=[InputPulses],
        OutputResponses=[filter_globals.SLOPPulses],
        TriggerConfigIDs=[filter_globals.slowparticleconfigid],
    )


# SLOP Filter (should run on SLOPSplit)
@icetray.traysegment
def SLOPFilter(tray, name, use_pulses=False, If = lambda f: True):

    from icecube.filterscripts import filter_globals
    from icecube.SLOPtools import TupleTagger
    icetray.load("filterscripts",False)

    tray.AddModule("I3FilterModule<I3BoolFilter>", name + "_SlowPartTriggerFilter",
	DecisionName = filter_globals.SlopFilter,
	DiscardEvents = False,
	Boolkey = filter_globals.slowparticletriggered,
	TriggerEvalList = [filter_globals.slowparticletriggered],
	If = If,
	)

    if not use_pulses:
        tray.AddModule(TupleTagger, name + "_TupleTagger",
            LaunchMapName="InIceRawData",
            RunOnLaunches=True,
            RunOnPulses=False,
            If=If,
            )
    else:
        tray.AddModule(TupleTagger, name + "_TupleTagger",
            PulseMapName=filter_globals.SLOPPulses,
            RunOnLaunches=False,
            RunOnPulses=True,
            If=If
            )


