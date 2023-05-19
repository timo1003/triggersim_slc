# Version 1.003
# Changes from 1.002 to 1.002
#   See SVN commit message
# Changes from 1.001 to 1.002
#	More recent releases have filter stuff in filter_2013
#	PFDST instead of SDST
#	.i3 instead of .i3.bz2; do compression and bundling together
#	filterscripts instead of jeb_filter_2012
#	DOMCleaning needed
# Version 1.001
# Changes from 1.000 to 1.001
#	Includes entire event for EHE triggers
from icecube import icetray, dataclasses, dataio, WaveCalibrator, wavedeform, payload_parsing
from I3Tray import *
from icecube.filterscripts.baseproc_daqtrimmer import DAQTrimmer
from icecube.filterscripts.baseproc_superdst import SuperDST
from icecube.filterscripts.baseproc_onlinecalibration import OnlineCalibration, DOMCleaning
from icecube.filterscripts import filter_globals
import sys

def make_parser():
    """Make the argument parser"""
    from optparse import OptionParser
    parser = OptionParser()
    
    parser.add_option("-i", "--input", action="store",
        type="string", default="", dest="infile",
        help="Input i3 file(s)  (use comma separated list for multiple files)")
    
    parser.add_option("-g", "--gcd", action="store",
        type="string", default="", dest="gcdfile",
        help="GCD file for input i3 file")
    
    parser.add_option("-o", "--output", action="store",
        type="string", default="", dest="outfile",
        help="Main i3 output file")
    
    parser.add_option("-n", "--num", action="store",
        type="int", default=-1, dest="num",
        help="Number of frames to process")

    return parser

def main(options, stats={}):
    # Note: Can concatenate an entire run of PFRaw files here but do NOT combine
    # multiple runs!
    
    tray = I3Tray()
    
    if 'outfile' not in options or not len(options['outfile']):
        inDir = os.path.dirname(options['infile'])
        baseName = os.path.basename(options['infile'])
        outName = "PFDST_"+baseName[baseName.find("PFRaw_")+6:].replace(".tar.gz",".i3")
        outName = os.path.join(inDir,outName)
        options['outfile'] = outName
    
    files = [options['gcdfile']]

    if isinstance(options['infile'],str):
        files.append(options['infile'])
    else:
        for f in options['infile']:files.append(f)
    
    tray.Add(dataio.I3Reader, "reader", filenamelist=files)
    
    tray.AddModule('QConverter', WritePFrame=False)

    tray.AddSegment(
        payload_parsing.I3DOMLaunchExtractor, "decode",
        SpecialDataID = "SpecialHits",
        SpecialDataOMs = [OMKey(0,1),
                          OMKey(12,65),
                          OMKey(12,66),
                          OMKey(62,65),
                          OMKey(62,66)]
    )

    tray.AddSegment(DOMCleaning, "_DOMCleaning")
    
    tray.AddSegment(OnlineCalibration, 'Calibration')
    tray.AddSegment(SuperDST, 'SuperDST',
        InIcePulses=filter_globals.UncleanedInIcePulses, 
        IceTopPulses='IceTopPulses',
        Output = filter_globals.DSTPulses
        )
    tray.AddSegment(DAQTrimmer, 'DAQTrimmer')
    
    tray.AddModule('Rename', Keys=['UncleanedInIcePulsesTimeRange', 'I3SuperDSTTimeRange'])
    
    tray.AddModule('Delete', Keys=[
        'CalibratedWaveforms',
       'CalibratedWaveformRange',
       'DrivingTime',
       'I3DAQData',
       'I3EventHeader_orig',
       'OfflinePulses',
       'I3TriggerHierarchy',
       'DAQTrimmer_CleanRawData',
       'DAQTrimmer_I3SuperDST_CalibratedWaveforms_Chi',
       'DAQTrimmer_HighCharge',
       'DAQTrimmer_TrivialLaunches',
       'DAQTrimmer_TrivialLaunchesKeys',
       'CalibratedIceTopATWD_HLC',
       'CalibratedIceTopATWD_SLC',
       'CalibratedIceTopFADC_HLC',
       'CleanIceTopRawData',
       'CleanInIceRawData',
       'DAQTrimmer_I3SuperDST_CalibratedWaveforms_Borked',
       'IceTopCalibratedWaveforms',
       'IceTopDSTPulses',
       'IceTopHLCPulseInfo',
       'IceTopHLCVEMPulses',
       'IceTopPulses',
       'IceTopPulses_HLC',
       'IceTopPulses_SLC',
       'IceTopSLCVEMPulses',
       'InIceDSTPulses',
       'JEBEventInfo',
       'RawDSTPulses',
       'UncleanedInIcePulses',
       ])
    
    # Needed features: IceTop data, seatbelts
    
    tray.AddModule("Delete",Keys=["InIceRawData"],If=lambda frame:not ( "QFilterMask" in frame and "EHEFilter_12" in frame["QFilterMask"] and frame["QFilterMask"]["EHEFilter_12"].condition_passed ) )
    
    tray.AddModule('I3Writer', Filename=options['outfile'],
        Streams=[icetray.I3Frame.TrayInfo, icetray.I3Frame.DAQ, icetray.I3Frame.Physics])
    
    # make it go
    if options['num'] >= 0:
        tray.Execute(options['num'])
    else:
        tray.Execute()

    print("Done")

### iceprod stuff ###
try:
    from iceprod.modules import ipmodule
except ImportError as e:
    print('Module iceprod.modules not found. Will not define IceProd Class')
else:
    Level2Filter = ipmodule.FromOptionParser(make_parser(),main)
### end iceprod stuff ###


# the business!
if (__name__=="__main__"):
    parser = make_parser()

    (options,args) = parser.parse_args()
    opts = {}
    # convert to dictionary
    for name in parser.defaults:
        value = getattr(options,name)
        if name == 'infile' and ',' in value:
            value = value.split(',') # split into multiple inputs
        opts[name] = value
    
    print("\nArgument : Value")
    for k in opts:
        print(k," : ",opts[k])
    
    if opts['infile']=='' or opts['gcdfile']=='':
        print("you must specify the input and gcd file arguments")
        exit(1)
    
    main(opts)
