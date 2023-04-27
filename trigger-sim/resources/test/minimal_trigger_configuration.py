#!/usr/bin/env python3

import os
from icecube import icetray, dataclasses, dataio
from icecube import trigger_sim, phys_services
from I3Tray import I3Tray
from os.path import expandvars

tray = I3Tray()

i3_testdata = expandvars("$I3_TESTDATA") 
gcd_file = i3_testdata + "/GCD/GeoCalibDetectorStatus_2016.57531_V0.i3.gz"

tray.AddModule("I3InfiniteSource", prefix = gcd_file)               

tray.AddModule("SimpleMajorityTrigger","IISMT8",               
               TriggerConfigID = 1006)

tray.AddModule("SimpleMajorityTrigger","DCSMT3",
               TriggerConfigID = 1011)

tray.AddModule("ClusterTrigger","string")    
tray.AddModule("SlowMonopoleTrigger","slop")
tray.AddModule("SimpleMajorityTrigger","ITSMT6",
               TriggerConfigID = 102)

tray.Execute(10)
