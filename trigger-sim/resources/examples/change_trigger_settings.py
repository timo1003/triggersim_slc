#!/usr/bin/env python3

'''
This example shows how to add a new trigger status to a GCD file.
This is useful if you want to change the trigger setting for one
of the trigger modules.

This is important because the trigger modules aren't capable of
changing the threshold, for example, via IceTray parameters.  They
get their configuration from the GCD file.

This script takes a GCD file and adds the TriggerStatus to the D frame.
'''

def get_triggerstatus(gcdfile):
    '''
    Gets the I3TriggerStatus from a GCD file.
    '''
    frame = gcdfile.pop_frame()
    while not frame.Has("I3DetectorStatus"):
        frame = gcdfile.pop_frame()

    return frame.Get("I3DetectorStatus").trigger_status

def put_triggerstatus(trigger_status_map,
                      gcdfile,
                      output_gcd_filename):
    '''
    Adds an I3TriggerStatus to a GCD file.
    '''
    newgcd = dataio.I3File(output_gcd_filename, 'w')
    frame = gcdfile.pop_frame()

    while not frame.Has("I3DetectorStatus"):
        newgcd.push(frame)
        frame = gcdfile.pop_frame()
        
    ds = frame.Get("I3DetectorStatus")
    del frame["I3DetectorStatus"]
    ds.trigger_status = trigger_status_map
    frame["I3DetectorStatus"] = ds
    newgcd.push(frame)

    return newgcd



from I3Tray import I3Tray
from icecube import icetray, dataclasses, dataio
from os.path import expandvars
import os

# make a trigger key
tkey = dataclasses.TriggerKey()
tkey.source = dataclasses.IN_ICE
tkey.type = dataclasses.SIMPLE_MULTIPLICITY
tkey.config_id = 999

# make a trigger status
tstat = dataclasses.I3TriggerStatus()

# set the triggername
tstat.trigger_name = "MyNewTrigger"
tstat.trigger_settings["threshold"] = '3'
tstat.trigger_settings["timeWindow"] = '2500'
tstat.trigger_settings["domSet"] = '5'

# make a readout config
roc = dataclasses.I3TriggerStatus.I3TriggerReadoutConfig()
roc.readout_time_minus = 10000
roc.readout_time_plus = 10000
roc.readout_time_offset = 0

# add the readout config to the trigger status
tstat.readout_settings[dataclasses.I3TriggerStatus.ALL] = roc

f = dataio.I3File(expandvars("$I3_TESTDATA/GCD/GeoCalibDetectorStatus_2016.57531_V0.i3.gz"))

ts = get_triggerstatus(f)
ts[tkey] = tstat

# it's important that you reopen the file
# because it seems the I3File.rewind doesn't
# do what I thought it should do
f = dataio.I3File(expandvars("$I3_TESTDATA/GCD/GeoCalibDetectorStatus_2016.57531_V0.i3.gz"))
newgcd = put_triggerstatus(ts,f,"./newGCD.i3.gz")

newgcd.close()

# this is being run as a test. clean up.
os.unlink('./newGCD.i3.gz')

