#!/usr/bin/env python3

from I3Tray import *
from icecube import icetray, dataclasses, dataio, filterscripts, filter_tools, trigger_sim
from icecube import phys_services
from icecube.filterscripts import filter_globals
from icecube import pfmonitoring
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
parser.add_option("-d", "--decode", action="store_true", 
		  dest="DECODE", help="Add the decoder to the processing")
parser.add_option("--simdata", action="store_true", 
		  dest="SIMDATA", help="This is IC86 sim data")
parser.add_option("--qify", action="store_true", default=False,
		  dest="QIFY", help="Apply QConverter, use if file is P frame only")
parser.add_option("-p", "--prettyprint", action="store_true", 
		  dest="PRETTY", help="Do nothing other than big tray dump")
parser.add_option("--disable-vemcal", action="store_false",  default=True,
		  dest="VEMCAL", help="Disable vemcal")
parser.add_option("--disable-gfu", action="store_false",  default=True,
		  dest="GFU", help="Disable gamma followup")
parser.add_option("--keepmc", action="store_true",  default=False,
      dest="SIMKEEP", help="Save crucial simulation-objects from being deleted; output might be considerably larger")

parser.add_option("--disable-hese-followup", action="store_false", default=True,
		  dest="HESE_FOLLOWUP", help="Disable HESE followup")
# this just uses a random example GCD file as the baseline (from simulation
# test data)
parser.add_option("--hese-followup-GCD-path", action="store", type="string",
		  default=os.path.expandvars("$I3_TESTDATA/sim/"),
		  dest="hese_followup_base_GCD_path",
		  help="base path for HESE follow-up GCD baseline files")
parser.add_option("--hese-followup-GCD-filename", action="store", type="string",
		  default="GeoCalibDetectorStatus_IC86.55697_corrected_V2.i3.gz",
		  dest="hese_followup_base_GCD_filename",
		  help="filename of the HESE follow-up GCD baseline file")
parser.add_option("--hese-followup-omit-GCD-diff", action="store_true", default=False,
		  dest="hese_followup_omit_GCD_diff", help="disable the GCD diff functionality (no GCD information will be sent)")


# get parsed args
(options,args) = parser.parse_args()

GCD = options.GCD
inputfile = options.INPUT
outputfile = options.OUTPUT
dodecode = options.DECODE
simdata = options.SIMDATA
prettyprint = options.PRETTY
dovemcal = options.VEMCAL
dogfu = options.GFU
dohese_followup = options.HESE_FOLLOWUP
hese_followup_base_GCD_path = options.hese_followup_base_GCD_path
hese_followup_base_GCD_filename = options.hese_followup_base_GCD_filename
hese_followup_omit_GCD_diff = options.hese_followup_omit_GCD_diff

load("libpfauxiliary")
load("libpfdebugging")

print('Opening file %s' % inputfile)
 
print('Preparing to write i3 file  %s' % outputfile) 

## Prep the logging hounds.
icetray.logging.console()   #Make python logging work
#icetray.logging.rotating_files('./filter_client.log')
icetray.I3Logger.global_logger.set_level(icetray.I3LogLevel.LOG_WARN)
icetray.I3Logger.global_logger.set_level_for_unit('I3FilterModule', icetray.I3LogLevel.LOG_INFO)


tray = I3Tray() 

sw_rootfile = 'StopWatch_' + outputfile + '.root'
print('Stopwatch file:', sw_rootfile)
tray.AddService("I3StopwatchServiceFactory","I3StopwatchService")(
    ("InstallServiceAs","I3StopwatchService"),
    ("OutputFileName", sw_rootfile),
    ("UseHighTimeResolution",False),
    )



tray.AddModule("I3Reader", "reader", filenamelist=[GCD,inputfile],
               SkipKeys = ['I3DST11',    ## Skip keys if your input file is previously filtered
                           'I3SuperDST',
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

tray.AddModule("I3StopwatchStart","stopwatchstart")(
    ("ID","I3ClientTime"),
    ("StopwatchServiceInstalledAs","I3StopwatchService"),
    )


if options.QIFY:
    tray.AddModule("QConverter", "qify", WritePFrame=False)

#def skip_first_frames(frame):
#    if skip_first_frames.counter <= 0:
#        return True
#    
#    skip_first_frames.counter -= 1
#    return False
#skip_first_frames.counter = 42000
#tray.AddModule(skip_first_frames, Streams=[icetray.I3Frame.DAQ])

tray.AddModule("PFEmitFlushFrame", 'emit_flush')

def insert_client_start_time(frame,
                             outputname = filter_globals.client_start_time):

    output = dataclasses.I3Double()
    output.value = time.time()
    frame[outputname] = output

tray.AddModule(insert_client_start_time, "insert_client_start_time",
               Streams=[icetray.I3Frame.DAQ])



tray.AddSegment(OnlineFilter, "Run",
                simulation=simdata,
                decode= dodecode,
                vemcal_enabled=dovemcal,
                gfu_enabled=dogfu,
                needs_wavedeform_spe_corr = True,
                # HESE follow-up configuration
                hese_followup=dohese_followup,
                hese_followup_omit_GCD_diff=hese_followup_omit_GCD_diff,
                hese_followup_base_GCD_path=hese_followup_base_GCD_path,
                hese_followup_base_GCD_filename=hese_followup_base_GCD_filename,
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

## Moni2.0 FTW
tray.AddSegment(pfmonitoring.ClientMoniTests, 'PFClient_moni_stuff')
tray.AddSegment(pfmonitoring.ClientCnVTests, 'PFClient_cnv_stuff')


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
    filter_globals.hese_followup_keeps + \
    filter_globals.ehe_followup_keeps + \
    filter_globals.estres_followup_keeps +\
    pfmonitoring.moni_client_keeps +\
    ['SpecialHits','InIceRawData','IceTopRawData']
  
if (options.SIMKEEP):
    prekeeps += simulation_keeps

tray.AddModule("Keep","keep_before_merge",
               keys = prekeeps)

tray.AddModule("I3StopwatchStop","stopwatchstop")(
    ("ID","I3ClientTime"),
    ("StopwatchServiceInstalledAs","I3StopwatchService"),
    ("ProcTimeFrameName","JEBClientInfo")
    )


# Write the physics and DAQ frames
tray.AddModule( "I3Writer", "EventWriter", filename=outputfile,
		Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ]
		)



if prettyprint:
    print(tray)
    exit(0)

tray.Execute()
#tray.Execute(20000)



stop_time = time.asctime()

print('Started:', start_time)
print('Ended:', stop_time)
