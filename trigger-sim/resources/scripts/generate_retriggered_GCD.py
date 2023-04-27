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

import sys
import argparse
import logging

from I3Tray import I3Tray
from icecube import icetray
from icecube import dataclasses
from icecube import dataio

parser = argparse.ArgumentParser(description='Generate a retrigger GCD file.')
parser.add_argument('--input-GCD',
                    dest='INPUT_GCD', 
                    help='Name of the input GCD file.')
parser.add_argument('--output-GCD',
                    dest='OUTPUT_GCD', 
                    help='Name of the output GCD file.')
parser.add_argument('--trigger-config-id',
                    dest='TRIGGER_CONFIG_ID',
                    type=int,
                    help='Trigger config ID')
parser.add_argument('--key',
                    dest='KEY', 
                    help='Member name in the I3TriggerStatus object.')
parser.add_argument('--value',
                    dest='VALUE', 
                    help='New value of the I3TriggerStatus member.')
args = parser.parse_args()


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

f = dataio.I3File(args.INPUT_GCD)
trigger_status_map = get_triggerstatus(f)

# find the trigger key
trigger_key = None
trigger_status = None
for key, status in trigger_status_map.items():
    if key.config_id == args.TRIGGER_CONFIG_ID:
        trigger_key = key
        trigger_status = status

if not trigger_key or not trigger_status:
    logging.error("  User defined trigger config_id = %d" % args.TRIGGER_CONFIG_ID)
    logging.error("  Trigger config_ids in the given GCD file:")
    for key, status in trigger_status_map.items():
        logging.error("    %s" % key.config_id)
    logging.critical("  I3TriggerStatus not found with config ID %s" % args.TRIGGER_CONFIG_ID)
    sys.exit(-1)

trigger_status.trigger_settings[args.KEY] = args.VALUE
trigger_status_map[trigger_key] = trigger_status

f = dataio.I3File(args.INPUT_GCD)
output_gcd = put_triggerstatus(trigger_status_map, f, args.OUTPUT_GCD)
output_gcd.close()

