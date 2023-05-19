from icecube import icetray, dataclasses
from icecube.icetray import OMKey, I3Units

## Import the 2.4 compatibility helpers for SPS/SPTS python
from icecube.icetray.pycompat import *

from icecube.filterscripts import filter_globals

def Unify(frame, Keys, Output):
    """
    Simple utility to merge RecoPulseSerieses into a single Union.
    """
    extants = [k for k in Keys if k in frame]
    union = dataclasses.I3RecoPulseSeriesMapUnion(frame, extants)
    frame[Output] = union

# From a SuperDST object, generate a set of RecoPulseMasks with
#   useful selection
def MaskMaker(frame, Output):
    pulses = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, 'I3SuperDST')
    ii_mask = dataclasses.I3RecoPulseSeriesMapMask(frame, 'I3SuperDST')
    it_mask = dataclasses.I3RecoPulseSeriesMapMask(frame, 'I3SuperDST')
    
    i3geometry = frame['I3Geometry']
    for omkey in pulses.keys():
        g = i3geometry.omgeo[omkey]
        ii_mask.set(omkey, g.omtype == dataclasses.I3OMGeo.IceCube)
        it_mask.set(omkey, g.omtype == dataclasses.I3OMGeo.IceTop)
    frame['InIce'+Output]  = ii_mask
    frame['IceTop'+Output] = it_mask

@icetray.traysegment
def SuperDST(tray, name, InIcePulses='InIcePulses', IceTopPulses='IceTopPulses',
             Output='EventPulses'):
    """
    Pack pulses extracted from InIce and IceTop DOMs into a SuperDST payload,
    and set up aliases pointing to the entire event as well as just to the
    InIce and IceTop portions.
    """
    
    from icecube import dataclasses

    def TriggerPacker(frame):
        """
        Create a compressed representation of the trigger hierarchy, 
        using the position of the TriggerKey in
        I3DetectorStatus::triggerStatus to identify each trigger.
        """
        triggers = frame[filter_globals.triggerhierarchy]
        status = frame['I3DetectorStatus']
        packed = dataclasses.I3SuperDSTTriggerSeries(triggers, status)
        frame['DSTTriggers'] = packed
    
    def I3SuperDSTPacker(frame, Pulses='Pulses', Output='I3SuperDST'):
        """
        Create a compressed representation of the reco pulses,
        using I3SuperDST.
        """
        if Pulses not in frame:
            pulses_ = dataclasses.I3RecoPulseSeriesMap()
        else:
            pulses_ = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, Pulses)
        frame[Output] = dataclasses.I3SuperDST(pulses_)

    DAQ = [icetray.I3Frame.DAQ]

    # Merge InIce and IceTop Pulses
    tray.AddModule(Unify, name + '_smush_InIce_IceTop',
                   Keys=[InIcePulses, IceTopPulses], Output='Raw'+Output,
                   Streams=DAQ)
    
    tray.AddModule(I3SuperDSTPacker, name + '_superdst',
                   Pulses='Raw'+Output,
                   Streams=DAQ)
    
    # Encode triggers
    tray.AddModule(TriggerPacker, name+'_triggers', Streams=DAQ)
