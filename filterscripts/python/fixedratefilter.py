# module to filter events with the fixed rate trigger

from I3Tray import *

@icetray.traysegment
def FixedRateTrigFilter(tray, name, If = lambda f: True):

  from icecube.filterscripts import filter_globals

  icetray.load("filterscripts",False)
  
  tray.AddModule("I3FilterModule<I3BoolFilter>", name+"FixedRateTrigFilter",
	DecisionName=filter_globals.FixedRateFilterName,
	DiscardEvents=False,
	Boolkey=filter_globals.fixedratetriggered,
	TriggerEvalList=[filter_globals.fixedratetriggered],
	If=If
	)

