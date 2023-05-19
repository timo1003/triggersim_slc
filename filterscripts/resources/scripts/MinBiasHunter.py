#!/usr/bin/env python3

"""
Search for MinBias events and save em.

It's got what zombie-plants crave. It's got brains.
"""

import sys, os, glob
from os.path import expandvars

from icecube import icetray, dataclasses, dataio
import I3Tray

outfile_in = sys.argv[-1]
outfile = outfile_in + '-%u.i3.bz2'

I3Tray.load("payload-parsing")
I3Tray.load("daq-decode")
I3Tray.load("I3Db")
I3Tray.load("dst")
I3Tray.load("filter-tools")

workspace = expandvars("$I3_BUILD")

mb_id_file = workspace + "/phys-services/resources/mainboard_ids.xml.gz"

infiles = glob.glob('/data/i3store1/exp/2012/filtered/PFFilt/0701/PFFilt_PhysicsTrig_PhysicsFiltering_*.tar.bz2')
infiles.sort()

tray = I3Tray.I3Tray()


tray.AddService("I3XMLOMKey2MBIDFactory","omkey2mbid")(
   ("Infile",mb_id_file),
   )
tray.AddService("I3PayloadParsingEventDecoderFactory", "EventDecoder",
                headerid="")

tray.AddModule("I3Reader", "reader", filenameList=infiles)
tray.AddModule("QConverter", "qify", WritePFrame=False)

def check_mask(frame, fmkey = "FilterMinBias_12"):
    if frame.Has("QFilterMask"):
        fm = frame.Get("QFilterMask")
        if fmkey in fm:
            fmmb = fm.get(fmkey)
            if (fmmb.condition_passed and fmmb.prescale_passed):
                #print 'Found one'
                return True
            else:
                return False
        else:
            print("Key not found in FilterMask")
            return False
    else:
        #print "FilterMask not found in frame"
        return False


tray.AddModule(check_mask,"FilterMaskCheck",Streams=[icetray.I3Frame.DAQ])


tray.AddModule("I3FrameBufferDecode", "I3Decoder", bufferID="I3DAQData", exceptionID="I3DAQDecodeException")

tray.AddModule("Rename","filtermaskmover",Keys=["QFilterMask","OrigQFilterMask"])

keep_keys = [
	"I3EventHeader",
	"I3TriggerHierarchy",
        "DrivingTime",
        "I3DAQData",
        "OrigQFilterMask",
        "IceTopRawData",
        "InIceRawData",
]

tray.AddModule("Keep", "trapper_keeper", keys=keep_keys)

tray.AddModule("I3MultiWriter", "writer",
               streams=[icetray.I3Frame.TrayInfo, icetray.I3Frame.DAQ],
               filename=outfile,
               sizelimit = 400000000
)



tray.Execute()


