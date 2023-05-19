#!/usr/bin/env python3

from I3Tray import *
from icecube import icetray, dataclasses, dataio 
from Rehydration import Rehydration
#from Offline_Base import RepeatBaseProc
from Globals import fwd, deepcore_stream
from icecube.phys_services.which_split import which_split
from DeepCoreRecoL2 import OfflineDeepCoreReco, DeepCoreHitCleaning
import sys
from optparse import OptionParser
icetray.load("naoko-counter",False)

parser = OptionParser()
parser.add_option("-i", "--input", action="store", type="string", default="", \
        dest="INPUT", help="Input IC86 simulation i3 file to reprocess")
parser.add_option("-g", "--gcd", action="store", type="string", default="", \
        dest="GCD", help="GCD file for input i3 file")
parser.add_option("-o", "--output", action="store", type="string", default="", \
        dest="OUTPUT", help="output i3 file")

# get parsed args
(options,args) = parser.parse_args()
infilestring = options.INPUT
gcdstring = options.GCD
outstring = options.OUTPUT

tray = I3Tray()

infiles = [gcdstring, infilestring]
print(infiles)

tray.AddModule( "I3Reader", "Reader")(
	("Filenamelist", infiles)
)

#tray.AddSegment(Rehydration, 'rehydrator')

#tray.AddSegment(RepeatBaseProc, 'redo_pole_process', If = which_split(split_name='InIceSplit'))

tray.AddSegment(DeepCoreHitCleaning,'DCHitCleaning', If = which_split(split_name='InIceSplit') & (lambda f: deepcore_stream(f)))

tray.AddSegment(OfflineDeepCoreReco,'DeepCoreL2Reco',pulses='SRTTWOfflinePulsesDC',If= which_split(split_name='InIceSplit') & (lambda f: deepcore_stream(f)), suffix='_DC')

tray.AddModule("I3PQEventCounter", "countme")(
	("Substreams", ["InIceSplit","NullSplit","IceTopSplit"]),
	("Bools",["NFramesIsDifferent"]),
)

def passedDCVeto(frame):
    return frame.Has("DipoleFit_DC")

tray.AddModule(passedDCVeto,"passedDCVeto")

tray.AddModule( "I3Writer", "EventWriter2" ) (
        ( "Filename", outstring),
	( "Streams",  [icetray.I3Frame.DAQ, icetray.I3Frame.Physics] ),
	( "DropOrphanStreams", [icetray.I3Frame.DAQ]),
)



tray.Execute()

