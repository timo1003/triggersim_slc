#!/usr/bin/env python3

from I3Tray import I3Tray
from icecube.icetray import I3Test
from icecube import icetray
from icecube import dataclasses
from icecube import phys_services
from icecube.trigger_sim.modules.time_shifter import I3TimeShifter
from icecube import simclasses

TIME = 999.9
def TestSetup(frame) :

    # I3TriggerHierarchy
    t = dataclasses.I3Trigger()
    t.time = TIME
    t.fired = True
    trigger_h = dataclasses.I3TriggerHierarchy()
    trigger_h.insert(t)
    frame["EarlyTrigger"] = trigger_h

    # I3TriggerHierarchy
    t = dataclasses.I3Trigger()
    t.time = TIME + 1000
    t.fired = True
    trigger_h = dataclasses.I3TriggerHierarchy()
    trigger_h.insert(t)
    frame["LateTrigger"] = trigger_h

def TestShift(frame):

    print(frame)
    # I3TriggerHierarchy
    for t in frame["EarlyTrigger"] :
        print("TriggerH t.time = ",t.time)
        I3Test.ENSURE(t.time == 0, "I3Trigger")

    for t in frame["LateTrigger"] :
        print("TriggerH t.time = ",t.time)
        I3Test.ENSURE(t.time > 0, "I3Trigger")

# The following tests standard operating conditions
# I3TimeShifter should determine the time shift from
# the trigger hierarchy in the frame
tray = I3Tray()
tray.AddModule("I3InfiniteSource")
tray.AddModule(TestSetup, streams = [icetray.I3Frame.DAQ])
tray.AddModule(I3TimeShifter)
tray.AddModule(TestShift, streams = [icetray.I3Frame.DAQ])
tray.Execute(1)
