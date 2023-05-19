#!/usr/bin/env python3

from I3Tray import *
from icecube import icetray, dataclasses, dataio, filterscripts, filter_tools
from icecube import phys_services
from icecube.filterscripts import filter_globals
from icecube.filterscripts.all_filters import OnlineFilter
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
parser.add_option("--simdata", action="store_true", 
		  dest="SIMDATA", help="This is IC86 sim data")
parser.add_option("--qify", action="store_true", default=False,
		  dest="QIFY", help="Apply QConverter, use if file is P frame only")
parser.add_option("-p", "--prettyprint", action="store_true", 
		  dest="PRETTY", help="Do nothing other than big tray dump")
parser.add_option("--keepmc", action="store_true",  default=False,
      dest="SIMKEEP", help="Save crucial simulation-objects from being deleted; output might be considerably larger")


# get parsed args
(options,args) = parser.parse_args()

GCD = options.GCD
inputfile = options.INPUT
outputfile = options.OUTPUT
simdata = options.SIMDATA
prettyprint = options.PRETTY

print('Opening file %s' % inputfile)
 
print('Preparing to write i3 file  %s' % outputfile )

## Prep the logging hounds.
icetray.logging.console()   #Make python logging work
icetray.I3Logger.global_logger.set_level(icetray.I3LogLevel.LOG_WARN)
icetray.I3Logger.global_logger.set_level_for_unit('I3FilterModule', icetray.I3LogLevel.LOG_INFO)


tray = I3Tray() 

tray.Add(dataio.I3Reader, "reader", filenamelist=[GCD,inputfile],
               SkipKeys = [],
)

# SPS GCD files do not have any bad DOM information. Rename it
# so that modules in L1 processing don't use it...
def rename_bad_DOM_lists(frame):
    for k in ('BadDomsList', 'BadDomsListSLC', 'IceTopBadDOMs', 'IceTopBadTanks'):
        if k in frame:
            frame[k+'_old'] = frame[k]
            del frame[k]
tray.AddModule(rename_bad_DOM_lists, "rename_bad_DOM_lists",
               Streams=[icetray.I3Frame.DetectorStatus])



# shim the D frame with IceTop Bad Doms.  Add empty lists.
def shim_bad_icetopdoms(frame):
    frame[filter_globals.IcetopBadTanks] = dataclasses.I3VectorTankKey()
    frame[filter_globals.IceTopBadDoms] = dataclasses.I3VectorOMKey()
    
tray.AddModule(shim_bad_icetopdoms,'Base_shim_icetopbads',
              Streams = [icetray.I3Frame.DetectorStatus])


if options.QIFY:
    tray.AddModule("QConverter", "qify", WritePFrame=False)


# PFDST files keep trigger information in a compact record.  Rehydrate to a full I3TriggerHierarchy
def shim_triggers(frame):
    triggers = dataclasses.I3TriggerHierarchy.from_frame(frame, 'DSTTriggers')
    frame[filter_globals.triggerhierarchy] = triggers

tray.AddModule(shim_triggers,'tshim',
               Streams = [icetray.I3Frame.DAQ])

tray.AddSegment(OnlineFilter, "Run",
                simulation=simdata,
                sdstarchive=True,
                decode= False,
                vemcal_enabled=False,
                gfu_enabled=False,
                # alert follow-up configuration
                alert_followup=False,
                ) 


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

simulation_keeps = [
            'BackgroundI3MCTree',
            'BackgroundI3MCTreePEcounts',
            'BackgroundI3MCPESeriesMap',
            'BackgroundI3MCTree_preMuonProp',
            'BackgroundMMCTrackList',
            'BeaconLaunches',
            'CorsikaInteractionHeight',
            'CorsikaWeightMap',
            'EventProperties',
            'GenerationSpec',
            'I3LinearizedMCTree',
            'I3MCTree',
            'I3MCTreePEcounts',
            'I3MCTree_preMuonProp',
            'I3MCPESeriesMap',
            'I3MCPulseSeriesMap',
            'I3MCPulseSeriesMapParticleIDMap',
            'I3MCWeightDict',
            'LeptonInjectorProperties',
            'MCHitSeriesMap',
            'MCPrimary',
            'MCPrimaryInfo',
            'MMCTrackList',
            'PolyplopiaInfo',
            'PolyplopiaPrimary',
            'RNGState',
            'SignalI3MCPEs',
            'SimTrimmer', # for SimTrimmer flag
            'TimeShift', # the time shift amount
            'WIMP_params', # Wimp-sim
            'noise_weight', # weights for noise-only vuvuzela simulations
            'I3GENIEResultDict' # weight informaition for GENIE simulations
           ]




prekeeps = filter_globals.q_frame_keeps + \
    [filter_globals.rawdaqdata,'JEBEventInfo'] + \
    [filter_globals.triggerhierarchy,filter_globals.qtriggerhierarchy] + \
    filter_globals.null_split_keeps + \
    filter_globals.inice_split_keeps + \
    filter_globals.icetop_split_keeps + \
    filter_globals.onlinel2filter_keeps + \
    filter_globals.ofufilter_keeps + \
    filter_globals.gfufilter_keeps + \
    filter_globals.alert_followup_keeps + \
    filter_globals.greco_reco_keeps
  
if (options.SIMKEEP):
    prekeeps += simulation_keeps

tray.AddModule("Keep","keep_before_write",
               keys = prekeeps)

# Write the physics and DAQ frames
tray.AddModule( "I3Writer", "EventWriter", filename=outputfile,
		Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ]
		)


if prettyprint:
    print(tray)
    exit(0)


#tray.Execute(10000)
tray.Execute()


tray.PrintUsage(fraction=1.0) 
for entry in tray.Usage():
    print(entry.key(),':',entry.data().usertime)


stop_time = time.asctime()

print('Started:', start_time)
print('Ended:', stop_time)
