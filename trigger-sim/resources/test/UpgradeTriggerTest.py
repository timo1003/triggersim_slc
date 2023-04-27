#!/usr/bin/env python3
from I3Tray import *

from icecube import icetray, dataclasses, dataio, trigger_sim

from os.path import expandvars
import sys

from icecube.trigger_sim.inice_test_modules import TestSource, TestSourcePulses, TestModule

gcd_file = expandvars("$I3_TESTDATA/GCD/GeoCalibDetectorStatus_ICUpgrade.v55.mixed_mergedGeo.V5.i3.bz2")
trigger_config_id = 21001 # Hijack this one just for this test

#-----------------------------------------------------------------------
# Test MeasurementMode = 0 (ie, all LC pulses for each PMT)
#-----------------------------------------------------------------------
tray = I3Tray()
tray.AddModule("I3InfiniteSource", prefix=gcd_file, stream=icetray.I3Frame.DAQ)

tray.AddModule(TestSourcePulses, NPMTs = 50)
tray.AddModule(TestSource, NDOMs = 8)

tray.AddModule("CylinderTrigger", 
               DataReadoutName = "InIceRawData",
               PulseReadoutName = "InIcePulses",
               TriggerConfigID = 21001,
               MeasurementMode = 0, # All LC pulses
)

tray.AddModule("I3GlobalTriggerSim", RunID = 0)

tray.AddModule(TestModule, TriggerName = 'I3TriggerHierarchy',
               TriggerTypeID = dataclasses.VOLUME,
               TriggerConfigID = trigger_config_id)
                              
tray.Execute(100)
print("PASSED (MeasurementMode 0)")


#-----------------------------------------------------------------------
# Test MeasurementMode = 1 (ie, first LC pulse on each PMT)
#-----------------------------------------------------------------------
tray = I3Tray()
tray.AddModule("I3InfiniteSource", prefix=gcd_file, stream=icetray.I3Frame.DAQ)

tray.AddModule(TestSourcePulses, NPMTs = 50)
tray.AddModule(TestSource, NDOMs = 8)

tray.AddModule("CylinderTrigger", 
               DataReadoutName = "InIceRawData",
               PulseReadoutName = "InIcePulses",
               TriggerConfigID = 21001,
               MeasurementMode = 1, 
)

tray.AddModule("I3GlobalTriggerSim", RunID = 0)

tray.AddModule(TestModule, 
               TriggerName = 'I3TriggerHierarchy',
               TriggerTypeID = dataclasses.VOLUME,
               TriggerConfigID = trigger_config_id)

                              
tray.Execute(100)
print("PASSED (MeasurementMode 1)")


#-----------------------------------------------------------------------
# Test MeasurementMode = 2 (ie, first LC pulse on each module)
#-----------------------------------------------------------------------
tray = I3Tray()
tray.AddModule("I3InfiniteSource", prefix=gcd_file, stream=icetray.I3Frame.DAQ)

tray.AddModule(TestSourcePulses, NPMTs = 50)
tray.AddModule(TestSource, NDOMs = 8)

tray.AddModule("CylinderTrigger", 
               DataReadoutName = "InIceRawData",
               PulseReadoutName = "InIcePulses",
               TriggerConfigID = 21001,
               MeasurementMode = 2, 
)

tray.AddModule("I3GlobalTriggerSim", RunID = 0)

tray.AddModule(TestModule, 
               TriggerName = 'I3TriggerHierarchy',
               TriggerTypeID = dataclasses.VOLUME,
               TriggerConfigID = trigger_config_id)

tray.Execute(100)
print("PASSED (MeasurementMode 2)")
