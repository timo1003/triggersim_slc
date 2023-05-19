#!/usr/bin/env python3

from optparse import OptionParser
import subprocess

from I3Tray import *
from icecube import icetray, dataclasses, dataio
from icecube.filterscripts.pass2.processing import process_sdst_archive_to_l2
from icecube.filterscripts.offlineL2 import SpecialWriter

def make_parser():
    # handling of command line arguments
    parser = OptionParser()
    usage = """%prog [options]"""
    parser.set_usage(usage)
    parser.add_option("-g", "--gcd", action="store",
        type="string", default="", dest="gcdfile",
        help="GCD file for input i3 file")
    parser.add_option("-i", "--input", action="store", type="string", default="",
    		  dest="infile", help="Input sdst archive i3 file to process")
    parser.add_option("-o", "--output", action="store", type="string", default="",
    		  dest="outfile", help="Output i3 file")
    parser.add_option("-n", "--num", action="store", type="int", default=None,
              dest="num", help="number of frames to run (default: all)")
    parser.add_option("--qify", action="store_true", default=False,
                      dest="QIFY", help="Apply QConverter, use if file is P frame only")
    parser.add_option("--gapsfile", action="store",
        type="string", default=None, dest="gapsfile",
        help="gaps text file (should be .txt)")
    parser.add_option("--spe-correction-is-already-applied", action="store_true", default=False,
                      dest="spe_already_applied", help="Skip the retroactive SPE correction. Use this for data from 2015/16 on where we already apply the correction at Pole/SPS")
    parser.add_option("--ic79-geometry", action="store_true", default=False,
                      dest="ic79_geometry", help="Enable if you are processing data of IC79.")

    # Dummy entry to satisfy the iceprod1 L2 module
    parser.add_option("--photonicsdir", action="store",
        type="string", default=None,
        dest="photonicsdir", help="Directory with photonics tables")

    return parser

def main(options, stats={}):
    # make list of input files from GCD and infile
    inputfiles = None
    if isinstance(options['infile'],list):
        inputfiles = [options['gcdfile']]
        inputfiles.extend(options['infile'])
    else:
        inputfiles = [options['gcdfile'], options['infile']]

    # clean up special case for bz2 files to get around empty file bug
    bzip2_files = []
    if options['outfile'] and options['outfile'].endswith('.bz2'):
        options['outfile'] = options['outfile'][:-4]
        bzip2_files.append(options['outfile'])
 
    #inputfiles = args[:-1]
    outputfile = options['outfile']
    num = options['num']
    qify = options['QIFY']
    
    print('Opening file(s):', inputfiles)
    print('Preparing to write i3 file', outputfile)
   
    tray = I3Tray()
    
    tray.context['I3FileStager'] = dataio.get_stagers()
    tray.AddModule("I3Reader", "reader",
        filenamelist=inputfiles)
    
    if qify:
        # Needed for SDST files from SPS
        tray.AddModule("QConverter", "qify", WritePFrame=False)
    
    process_sdst_archive_to_l2(tray, spe_correction_is_already_applied = options['spe_already_applied'], ic79_geometry = options['ic79_geometry'])
    
    # Write the physics and DAQ frames
    tray.AddModule("I3Writer", "EventWriter",
            filename=outputfile,
            Streams=[icetray.I3Frame.TrayInfo,icetray.I3Frame.Physics,icetray.I3Frame.DAQ]
            )
    
    if options['gapsfile']:
        tray.AddSegment(SpecialWriter.GapsWriter, "write_gaps",
            Filename = options['gapsfile'],
            MinGapTime = 1
        )

    
    
    if num:
        tray.Execute(num)
    else:
        tray.Execute()
    

    # print more CPU usage info. than speicifed by default
    tray.PrintUsage(fraction=1.0) 
    for entry in tray.Usage():
        stats[entry.key()] = entry.data().usertime

    if bzip2_files:
        # now do bzip2
        if os.path.exists('/usr/bin/bzip2'):
           subprocess.check_call(['/usr/bin/bzip2', '-f']+bzip2_files)   
        elif os.path.exists('/bin/bzip2'):
           subprocess.check_call(['/bin/bzip2', '-f']+bzip2_files)   
        else:
           raise Exception('Cannot find bzip2')
 
    del tray

### iceprod stuff ###
try:
    from iceprod.modules import ipmodule
except ImportError as e:
    print('Module iceprod.modules not found. Will not define IceProd Class')
else:
    Level2Filter = ipmodule.FromOptionParser(make_parser(),main)
### end iceprod stuff ###

if __name__ == '__main__':
    # run as script from the command line
    # get parsed args
    parser = make_parser()
    (options,args) = parser.parse_args()
    opts = {}
    # convert to dictionary
    for name in parser.defaults:
        value = getattr(options,name)
        if name == 'infile' and ',' in value:
            value = value.split(',') # split into multiple inputs
        opts[name] = value

    # call main function
    main(opts)
