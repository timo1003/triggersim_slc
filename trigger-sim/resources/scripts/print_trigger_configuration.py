#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(description='Generate a retrigger GCD file.')
parser.add_argument("GCD_FILENAME", help="Name of the input GCD file.")
args = parser.parse_args()

from icecube import dataio
from icecube import dataclasses

f = dataio.I3File(args.GCD_FILENAME)

frame = f.pop_frame()
while f.more() and not "I3DetectorStatus" in frame:
    frame = f.pop_frame()
detector_status = frame["I3DetectorStatus"]

trigger_status_map = detector_status.trigger_status

for key, config in trigger_status_map.iteritems() :
    print("TriggerKey : %s" % str(key))
    print("  %s" % config.trigger_name)
    for name, setting in config.trigger_settings.iteritems():
        print("    %s = %s" % (name,setting))

