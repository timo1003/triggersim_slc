#!/usr/bin/env python3

from I3Tray import *
from icecube import icetray, dataclasses, dataio, filterscripts, filter_tools, trigger_sim
from icecube import phys_services, WaveCalibrator, tpx
from icecube.filterscripts import filter_globals
from icecube.filterscripts.all_filters import OnlineFilter
import os, sys, time
from math import log10, cos, radians
from optparse import OptionParser
from icecube.phys_services.spe_fit_injector import I3SPEFitInjector


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
parser.add_option("-p", "--prettyprint", action="store_true", 
		  dest="PRETTY", help="Do nothing other than big tray dump")
parser.add_option("--disable-gfu", action="store_false",  default=True,
		  dest="GFU", help="Disable gamma followup")
parser.add_option("--disable-alert-followup", action="store_false", default=True,
		  dest="ALERT_FOLLOWUP", help="Disable alert followup")
parser.add_option("--alert-followup-GCD-path", action="store", type="string",
		  default=os.path.expandvars("$I3_TESTDATA/sim/"),
		  dest="alert_followup_base_GCD_path",
		  help="base path for follow-up GCD baseline files")
parser.add_option("--alert-followup-GCD-filename", action="store", type="string",
		  default="GeoCalibDetectorStatus_IC86.55697_corrected_V2.i3.gz",
		  dest="alert_followup_base_GCD_filename",
		  help="filename of the follow-up GCD baseline file")
parser.add_option("--alert-followup-omit-GCD-diff", action="store_true", default=False,
		  dest="alert_followup_omit_GCD_diff", help="disable the GCD diff functionality (no GCD information will be sent)")


# get parsed args
(options,args) = parser.parse_args()

GCD = options.GCD
inputfile = options.INPUT
outputfile = options.OUTPUT
prettyprint = options.PRETTY
dogfu = options.GFU
doalert_followup = options.ALERT_FOLLOWUP
alert_followup_base_GCD_path = options.alert_followup_base_GCD_path
alert_followup_base_GCD_filename = options.alert_followup_base_GCD_filename
alert_followup_omit_GCD_diff = options.alert_followup_omit_GCD_diff

print('Opening file %s' % inputfile)
 
print('Preparing to write i3 file  %s' % outputfile) 

## Prep the logging hounds.
icetray.logging.console()   #Make python logging work
#icetray.logging.rotating_files('./filter_client.log')
icetray.I3Logger.global_logger.set_level(icetray.I3LogLevel.LOG_WARN)
icetray.I3Logger.global_logger.set_level_for_unit('I3FilterModule', icetray.I3LogLevel.LOG_INFO)


tray = I3Tray() 

tray.Add(dataio.I3Reader, "reader", filenamelist=[GCD,inputfile],
               SkipKeys = ['I3DST11',    ## Skip keys if your input file is previously filtered
                           'I3VEMCalData',
                           'PoleMuonLlhFit',
                           'PoleMuonLlhFitCutsFirstPulseCuts',
                           'PoleMuonLlhFitFitParams',
                           'CramerRaoPoleL2IpdfGConvolute_2itParams',
                           'CramerRaoPoleL2MPEFitParams',
                           'PoleL2IpdfGConvolute_2it',
                           'PoleL2IpdfGConvolute_2itFitParams',
                           'PoleL2MPEFit',
                           'PoleL2MPEFitCuts',
                           'PoleL2MPEFitFitParams',
                           'PoleL2MPEFitMuE',
                           ]
)
#tray.AddModule("Dump","readstuff")


# shim the D frame with IceTop Bad Doms.
def shim_bad_icetopdoms(frame):
#    frame[filter_globals.IcetopBadTanks] = dataclasses.I3VectorTankKey()
    frame[filter_globals.IceTopBadDoms] = dataclasses.I3VectorOMKey()
    
tray.AddModule(shim_bad_icetopdoms,'Base_shim_icetopbads',
              Streams = [icetray.I3Frame.DetectorStatus])



tray.AddModule("QConverter", "qify", WritePFrame=False)

# prepare things for OnlineFilter

tray.AddModule("Delete","ClearOldFilters",Keys=["FilterMask","QFilterMask"])

# HACK #2: re-run IceTop calibration                                                                 
#tray.AddModule("Delete", "IceTop_recal_cleanup", Keys=['IceTopErrata'])
#tray.AddModule("I3WaveCalibrator", "WaveCalibrator_IceTop",
#               Launches="IceTopRawData",
#               Waveforms="IceTopCalibratedWaveforms", Errata="IceTopErrata",
#               WaveformRange="")
#tray.AddModule('I3WaveformSplitter', 'WaveformSplitter_IceTop',
#               Force=True, Input='IceTopCalibratedWaveforms',
#               PickUnsaturatedATWD=True, HLC_ATWD='CalibratedIceTopATWD_HLC',
#               HLC_FADC='CalibratedIceTopFADC_HLC', SLC='CalibratedIceTopATWD_SLC')
#tray.AddModule('I3TopHLCPulseExtractor', 'tpx_hlc',
#               Waveforms='CalibratedIceTopATWD_HLC', PEPulses='IceTopPulses_HLC',
#               PulseInfo='IceTopHLCPulseInfo', VEMPulses='IceTopHLCVEMPulses',
#               MinimumLeadingEdgeTime = -100.0*icetray.I3Units.ns, BadDomList=filter_globals.IceTopBadDoms)
#tray.AddModule('I3TopSLCPulseExtractor', 'tpx_slc',
#               Waveforms='CalibratedIceTopATWD_SLC', PEPulses='IceTopPulses_SLC',
#               VEMPulses='IceTopSLCVEMPulses', BadDomList=filter_globals.IceTopBadDoms)
def KeepInteresting(frame):
    if 'DSTTriggers' not in frame:
        return False
    else:
        return True
tray.AddModule(KeepInteresting,"ki",Streams=[icetray.I3Frame.DAQ])


def copyTriggers(frame):
    if "I3TriggerHierarchy" in frame:
        raise RuntimeError("I3TriggerHierarchy unexpectedly already in frame")
    frame["I3TriggerHierarchy"] = frame["DSTTriggers"]
tray.AddModule(copyTriggers, "copyTriggers", Streams=[icetray.I3Frame.DAQ])

#tray.AddModule("Dump","dumpppe")

#def print_now(frame):
#    eh = frame["I3EventHeader"]
#    print eh.run_id,eh.event_id

#tray.Add(print_now,"pn",Streams = [icetray.I3Frame.DAQ])


#def skip_first_frames(frame):
#    if skip_first_frames.counter <= 0:
#        return True
#    
#    skip_first_frames.counter -= 1
#    return False
#skip_first_frames.counter = 42000
#tray.AddModule(skip_first_frames, Streams=[icetray.I3Frame.DAQ])

tray.AddSegment(OnlineFilter, "Run",
                simulation=False,
                decode=False,
                sdstarchive=True,
                vemcal_enabled=False,
                gfu_enabled=dogfu,
                needs_wavedeform_spe_corr = True,
                # alert follow-up configuration
                alert_followup=doalert_followup,
                alert_followup_omit_GCD_diff=alert_followup_omit_GCD_diff,
                alert_followup_base_GCD_path=alert_followup_base_GCD_path,
                alert_followup_base_GCD_filename=alert_followup_base_GCD_filename,
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

simulation_keeps = ["I3MCTree",
                    "I3MCTree_preMuonProp",
                    "I3MCPulseSeriesMap",
                    "I3MCPulseSeriesMapParticleIDMap",
                    "MMCTrackList",
                    #"I3MCPESeriesMap",
                    #"I3MCPESeriesMapWithoutNoise"
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
    filter_globals.alert_followup_keeps 
  

tray.AddModule("Keep","keep_before_merge",
               keys = prekeeps)

# Write the physics and DAQ frames
tray.AddModule( "I3Writer", "EventWriter", filename=outputfile,
		Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ]
		)



if prettyprint:
    print(tray)
    exit(0)

tray.Execute()
#tray.Execute(30000)

tray.PrintUsage(fraction=1.0) 
for entry in tray.Usage():
    stats[entry.key()] = entry.data().usertime
    print(entry.key(),':',entry.data().usertime)



stop_time = time.asctime()

print('Started:', start_time)
print('Ended:', stop_time)
