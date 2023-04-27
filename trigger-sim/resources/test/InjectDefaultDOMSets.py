#!/usr/bin/env python3

from os.path import expandvars

from icecube import icetray, dataclasses, dataio, trigger_sim
from I3Tray import I3Tray

tray = I3Tray()

gcd_file = expandvars("$I3_TESTDATA/GCD/GeoCalibDetectorStatus_2013.56429_V1.i3.gz")
tray.AddModule("I3Reader", Filename=gcd_file)               

tray.AddModule(trigger_sim.InjectDefaultDOMSets)

tray.AddModule("I3Writer", Filename = "outfile.i3.gz")    

tray.Execute()


import os
os.unlink("outfile.i3.gz")

