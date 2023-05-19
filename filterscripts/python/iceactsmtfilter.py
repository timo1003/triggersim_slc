# module to filter events with the iceact mb trigger

from I3Tray import *

@icetray.traysegment
def IceActTrigFilter(tray, name, If = lambda f: True):

  from icecube.filterscripts import filter_globals

  icetray.load("filterscripts",False)
  
  tray.AddModule("I3FilterModule<I3BoolFilter>", name+"IceActTrigFilter",
	DecisionName=filter_globals.IceActFilter,
	DiscardEvents=False,
	Boolkey=filter_globals.iceactsmttriggered,
	TriggerEvalList=[filter_globals.iceactsmttriggered],
	If=If
	)

