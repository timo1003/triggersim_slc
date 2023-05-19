#!/usr/bin/env python3

from I3Tray import *
from icecube import icetray, dataclasses, dataio, filterscripts, filter_tools, trigger_sim
from icecube import phys_services
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
parser.add_option("-d", "--decode", action="store_true", 
		  dest="DECODE", help="Add the decoder to the processing")
parser.add_option("--simdata", action="store_true", 
		  dest="SIMDATA", help="This is IC86 sim data")
parser.add_option("--qify", action="store_true", default=False,
		  dest="QIFY", help="Apply QConverter, use if file is P frame only")
parser.add_option("-p", "--prettyprint", action="store_true", 
		  dest="PRETTY", help="Do nothing other than big tray dump")

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
hese_followup_base_GCD_path = options.hese_followup_base_GCD_path
hese_followup_base_GCD_filename = options.hese_followup_base_GCD_filename
hese_followup_omit_GCD_diff = options.hese_followup_omit_GCD_diff

load("libpfauxiliary")
load("libmonitoring")
# For the Stopwatch                                                             
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
               SkipKeys = ['I3DST11',    
                           'I3SuperDST',
                           'I3VEMCalData',
                           'IceTopRawData',
                           'InIceRawData',
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



# kick the stopwatch
spe_correction_file = os.path.expandvars("$I3_BUILD/filterscripts/resources/data/final-spe-fits-pole-run2016.json.bz2")
tray.AddModule(I3SPEFitInjector, "fixspe", Filename = spe_correction_file)
 

tray.AddModule("I3StopwatchStart","stopwatchstart")(                           
    ("ID","I3ClientTime"),                                                 
    ("StopwatchServiceInstalledAs","I3StopwatchService"),                  
    )                             

if options.QIFY:
    tray.AddModule("QConverter", "qify", WritePFrame=False)


# Slip in a "EndQ/E" frame, act to prevent PacketModules from caching
tray.AddModule("PFEmitFlushFrame", 'emit_flush')


tray.AddSegment(OnlineFilter, "Run",
                simulation=simdata,
                decode= dodecode,
                
                # HESE follow-up configuration
                hese_followup=True,
                hese_followup_omit_GCD_diff=hese_followup_omit_GCD_diff,
                hese_followup_base_GCD_path=hese_followup_base_GCD_path,
                hese_followup_base_GCD_filename=hese_followup_base_GCD_filename,
                ) 


# Generate filter Masks for all P frames
filter_mask_randoms = phys_services.I3GSLRandomService(9999)
print(filter_globals.filter_pairs + filter_globals.sdst_pairs)
## filter_tools.FilterMaskMaker runs on the Physics stream
## Online: PFFilterModule...
tray.AddModule(filter_tools.FilterMaskMaker, "MakeFilterMasks",
               OutputMaskName = filter_globals.filter_mask,
               FilterConfigs = filter_globals.filter_pairs+ filter_globals.sdst_pairs,
               RandomService = filter_mask_randoms)

# Merge the FilterMasks into Q frame:
tray.AddModule("OrPframeFilterMasks", "make_q_filtermask",
               InputName = filter_globals.filter_mask,
               OutputName = filter_globals.qfilter_mask)

#I3Moni
UniqueName = "Test" + "_" + str(os.getpid())
write_period = 100000 
tray.AddModule("I3EvtMonitoring","Moni_analysis")(
        ("AnalysisName","EvtMon"),
        ("CalibratedATWDWaveforms","CalibratedWaveforms"),
        ("CalibratedFADCWaveforms","NoneNow"),
        ("EventHeader",filter_globals.eventheader),
        ("FilterName","PhysicsFiltering"),
        ("InitialHitSeriesReco",filter_globals.UncleanedInIcePulses),
        ("NumberOfInputFiles",1),
        ("OmrName1","InIceRawData"),
        ("OmrName2","IceTopRawData"),
        ("OutputDirectory",'./'),
        ("PfFilterMask",filter_globals.qfilter_mask),
        ("PhysicsName","PhysicsData"),
        ("RecoName1",filter_globals.muon_linefit),
        ("RecoName2","None2"),
        ("RecoName3","None3"),
        ("RecoName4","None4"),
        ("RecoName5","None5"),
        ("RecoName6",filter_globals.muon_llhfit),
        ("RecoName7","None7"),
        ("RecoName8","None8"),
        ("RecoName9","None9"),
        ("Subrun",0),
        ("TriggerHierarchy",filter_globals.qtriggerhierarchy),
        ("UniqueName",UniqueName),
        ("DeepCoreSMTConfigID",filter_globals.deepcoreconfigid),
        ("WriteOutputEveryEvent",write_period),
        )


#Q+P frame specific keep module needs to go first,  you can add additional items you 
##  want to keep for your filter testing.

def is_Q(frame):
        return frame.Stop==frame.DAQ

tray.AddModule("Keep","keep_before_merge",
               keys = filter_globals.q_frame_keeps + ['I3DAQData'],
               If=is_Q)

tray.AddModule("I3IcePickModule<FilterMaskFilter>","filterMaskCheckAll",
               FilterNameList = filter_globals.filter_streams,
               FilterResultName = filter_globals.qfilter_mask,
               DecisionName = "PassedAnyFilter",
               DiscardEvents = False, 
               Streams = [icetray.I3Frame.DAQ]
               )

def do_save_just_superdst(frame):
    if frame.Has("PassedAnyFilter"):
        if not frame["PassedAnyFilter"].value:
            return True    #  <- Event failed to pass any filter.  
        else:
            return False # <- Event passed some filter

    else:
        print("Failed to find key frame Bool!!")
        return False

tray.AddModule("Keep", "KeepOnlySuperDSTs",
               keys = filter_globals.keep_nofilterpass+["PassedAnyFilter"],
               If = do_save_just_superdst
               )

tray.AddModule("I3IcePickModule<FilterMaskFilter>","filterMaskCheckSDST",
               FilterNameList = filter_globals.sdst_streams,
               FilterResultName = filter_globals.qfilter_mask,
               DecisionName = "PassedKeepSuperDSTOnly",
               DiscardEvents = False,
               Streams = [icetray.I3Frame.DAQ]
               )

def dont_save_superdst(frame):
    if frame.Has("PassedKeepSuperDSTOnly") and frame.Has("PassedAnyFilter"):
        if frame["PassedAnyFilter"].value:
            return False  #  <- these passed a regular filter, keeper
        elif not frame["PassedKeepSuperDSTOnly"].value:
            return True    #  <- Event failed to pass SDST filter.
        else:
            return False # <- Event passed some  SDST filter
    else:
        return False


tray.AddModule("Keep", "KeepOnlyDSTs",
               keys = filter_globals.keep_dst_only
                      + ["PassedAnyFilter","PassedKeepSuperDSTOnly"]
                      + [filter_globals.eventheader,
                         ##filter_globals.qfilter_mask
                         ],
               If = dont_save_superdst
               )


## Frames should now contain only what is needed.  now flatten, write/send to server
# Squish P frames back to single Q frame, one for each split:

tray.AddModule("KeepFromSubstream","null_stream",
               StreamName = filter_globals.NullSplitter,
               KeepKeys = filter_globals.null_split_keeps,
               )

tray.AddModule("KeepFromSubstream","inice_split_stream",
               StreamName = filter_globals.InIceSplitter,
               KeepKeys = filter_globals.inice_split_keeps + filter_globals.onlinel2filter_keeps + filter_globals.hese_followup_keeps + filter_globals.estres_followup_keeps,
               )

tray.AddModule("KeepFromSubstream","icetop_split_stream",
               StreamName = filter_globals.IceTopSplitter,
               KeepKeys = filter_globals.icetop_split_keeps,
               )

tray.AddModule("KeepFromSubstream","slop_split_stream",
               StreamName = filter_globals.SLOPSplitter,
               KeepKeys = filter_globals.slop_split_keeps,
               )

print('Wants I3DAQData: ',filter_globals.filters_keeping_allraw)

# Remove I3DAQData object for events not passing one of the 'filters_keeping_allraw'
tray.AddModule("I3IcePickModule<FilterMaskFilter>","filterMaskCheck",
               FilterNameList = filter_globals.filters_keeping_allraw,
               FilterResultName = filter_globals.qfilter_mask,
               DecisionName = "PassedConventional",
               DiscardEvents = False,
               Streams = [icetray.I3Frame.DAQ]
               )

# Clean out the SuperDST errata when you have full I3DAQData
def I3DAQDataCleaner(frame):
    if frame.Has("PassedConventional"):
        if frame['PassedConventional'].value == False:
            frame.Delete(filter_globals.rawdaqdata)
            
# TODO: This needs to be done in the server.
tray.AddModule(I3DAQDataCleaner,"CleanErrataForConventional",
               Streams=[icetray.I3Frame.DAQ])

# Change Q frame into a P frame and send it back to server
tray.AddModule("PConverter","pify")

# Stop the stopwatch                                                            
tray.AddModule("I3StopwatchStop","stopwatchstop")(                             
    ("ID","I3ClientTime"),                                                 
    ("StopwatchServiceInstalledAs","I3StopwatchService"),                  
    ("ProcTimeFrameName","ExecutionTime")                                  
    )                                            

# Write the physics and DAQ frames
tray.AddModule( "I3Writer", "EventWriter", filename=outputfile,
		Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ]
		)





if prettyprint:
    print(tray)
    exit(0)

#tray.Execute()
tray.Execute(20000)



stop_time = time.asctime()

print('Started:', start_time)
print('Ended:', stop_time)
