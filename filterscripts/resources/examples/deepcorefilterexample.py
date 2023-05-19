#!/usr/bin/env python3

from I3Tray import *
from icecube import icetray, dataclasses, dataio, filterscripts, filter_tools, trigger_sim
from icecube import phys_services
from icecube.filterscripts import filter_globals
from icecube.phys_services.which_split import which_split
import os, sys, time
from math import log10, cos, radians
from optparse import OptionParser

start_time = time.asctime()

print('Started:', start_time)
 
# handling of command line arguments  
parser = OptionParser()
usage = """%prog [options]"""
parser.set_usage(usage)
parser.add_option("-i", "--input", action="store", type="string", default="", 
		  dest="INPUT", help="Input i3 file to process")
parser.add_option("-o", "--output", action="store", type="string", default="",
		  dest="OUTPUT", help="Output i3 file")
parser.add_option("-g", "--gcd", action="store", type="string", default="",
		  dest="GCD", help="GCD file for input i3 file")
parser.add_option("-d", "--decode", action="store_true", 
		  dest="DECODE", help="Add the decoder to the processing")
parser.add_option("--simdata", action="store_true", 
		  dest="SIMDATA", help="This is IC86 sim data, decode and triger")
parser.add_option("--qify", action="store_true", default=False,
		  dest="QIFY", help="Apply QConverter, use if file is P frame only")
parser.add_option("-p", "--prettyprint", action="store_true", 
		  dest="PRETTY", help="Do nothing other than big tray dump")

# get parsed args
(options,args) = parser.parse_args()

GCD = options.GCD
inputfile = options.INPUT
outputfile = options.OUTPUT
dodecode = options.DECODE
simdata = options.SIMDATA
prettyprint = options.PRETTY

print('Opening file %s' % inputfile)
 
print('Preparing to write i3 file  %s' % outputfile) 

tray = I3Tray() 

tray.AddModule("I3Reader", "reader", filenamelist=[GCD,inputfile],
#               SkipKeys = ['I3DST11',    ## Skip keys if your input file is previously filtered
#                           'I3SuperDST',
#                           'I3VEMCalData',
#                           'IceTopRawData',
#                           'InIceRawData',
#                           'PoleMuonLlhFit',
#                           'PoleMuonLlhFitCutsFirstPulseCuts',
#                           'PoleMuonLlhFitFitParams',
#                           'CramerRaoPoleL2IpdfGConvolute_2itParams',
#                           'CramerRaoPoleL2MPEFitParams',
#                           'PoleL2IpdfGConvolute_2it',
#                           'PoleL2IpdfGConvolute_2itFitParams',
#                           'PoleL2MPEFit',
#                           'PoleL2MPEFitCuts',
#                           'PoleL2MPEFitFitParams',
#                           'PoleL2MPEFitMuE',
#                           ]
)

if options.QIFY:
    tray.AddModule("QConverter", "qify", WritePFrame=False)


## base processing requires:  GCD and frames being fed in by reader or Inlet
## base processing include:  decoding, TriggerCheck, Bad Dom cleaning, calibrators, Feature extraction,
##     pulse cleaning (seeded RT, and Time Window), PoleMuonLineit, PoleMuonLlh,
##     Cuts module and Mue on PoleMuonLlh

tray.AddSegment(filter_2013.BaseProcessing, "BaseProc",
		pulses=filter_globals.CleanedMuonPulses,
		decode=dodecode,simulation=simdata,
		)

## Todo:  Check with IceTop group has this changed?
#tray.AddSegment(filter_2013.IceTopVEMCal, "VEMCALStuff")

## Filters that use the InIce Trigger splitting

tray.AddSegment(filter_2013.DeepCoreFilter,"DeepCoreFilter",
                pulses = filter_globals.SplitUncleanedInIcePulses,
		If = which_split(split_name=filter_globals.InIceSplitter)
		)

#tray.AddSegment(filter_2013.MuonFilter, "MuonFilter",
#                pulses = filter_globals.CleanedMuonPulses,
#                If = which_split(split_name=filter_globals.InIceSplitter)
#                )

## Filters on the Null split

tray.AddSegment(filter_2013.MinBiasFilters, "MinBias",
                If = which_split(split_name=filter_globals.NullSplitter)
                )

## Filters on the CR split
#tray.AddSegment(filter_2013.CosmicRayFilter, "CosmicRayFilter", 
#                pulseMask = filter_globals.SplitUncleanedITPulses,
#                If = which_split(split_name=filter_globals.IceTopSplitter)
#                )


#tray.AddSegment(filter_2013.DST, "DSTFilter", 
#                dstname  = "I3DST12",
#                pulses   = filter_globals.CleanedMuonPulses,
#                If = which_split(split_name=filter_globals.InIceSplitter))

# Generate filter Masks for all P frames
filter_mask_randoms = phys_services.I3GSLRandomService(9999)
print(filter_globals.filter_pairs + filter_globals.sdst_pairs)
## filter_tools.FilterMaskMaker runs on the Physics stream
tray.AddModule(filter_tools.FilterMaskMaker, "MakeFilterMasks",
               OutputMaskName = filter_globals.filter_mask,
               FilterConfigs = filter_globals.filter_pairs+ filter_globals.sdst_pairs,
               RandomService = filter_mask_randoms)

# Merge the FilterMasks into Q frame:
tray.AddModule("OrPframeFilterMasks", "make_q_filtermask",
               InputName = filter_globals.filter_mask,
               OutputName = filter_globals.qfilter_mask)


#Q+P frame specific keep module needs to go first,  you can add additional items you 
##  want to keep for your filter testing.

prekeeps = filter_globals.q_frame_keeps + \
    [filter_globals.rawdaqdata,'JEBEventInfo'] + \
    [filter_globals.triggerhierarchy,filter_globals.qtriggerhierarchy] + \
    filter_globals.null_split_keeps + \
    filter_globals.inice_split_keeps + \
    filter_globals.icetop_split_keeps + \
    filter_globals.onlinel2filter_keeps

tray.AddModule("Keep","keep_before_merge",
               keys = prekeeps)

# Write the physics and DAQ frames
tray.AddModule( "I3Writer", "EventWriter", filename=outputfile+".i3",
		Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ]
		)



if prettyprint:
    print(tray)
    exit(0)

tray.Execute()
#tray.Execute(2000)



stop_time = time.asctime()

print('Started:', start_time)
print('Ended:', stop_time)
