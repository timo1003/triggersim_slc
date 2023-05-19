# Rehydration of DST and sDST files

import sys
from I3Tray import *
from icecube import icetray
from icecube.icetray import I3PacketModule
from icecube.filterscripts import filter_globals
from icecube import trigger_splitter

@icetray.traysegment
def Dehydration(tray, name):
    """
    Use this for PnF files (or online L1) that have not been run through
    PConverter. 

    Squishes all frame objects back into the Q-frame and gets rid of P-frames.
    """
    
    # ==== copy from online baseproc.py =====

    ## Frames should now contain only what is needed.  now flatten, write/send to server
    # Squish P frames back to single Q frame, one for each split:
    tray.AddModule("KeepFromSubstream",name+"_null_stream",
                   StreamName = filter_globals.NullSplitter,
                   KeepKeys = filter_globals.null_split_keeps,
                   )

    tray.AddModule("KeepFromSubstream",name+"_inice_split_stream",
                   StreamName = filter_globals.InIceSplitter,
                   KeepKeys = filter_globals.inice_split_keeps + filter_globals.onlinel2filter_keeps + filter_globals.gfufilter_keeps,
                   )

    tray.AddModule("KeepFromSubstream",name+"_icetop_split_stream",
                   StreamName = filter_globals.IceTopSplitter,
                   KeepKeys = filter_globals.icetop_split_keeps,
                   )

    tray.AddModule("KeepFromSubstream",name+"_slop_stream",
                   StreamName = filter_globals.SLOPSplitter,
                   KeepKeys = filter_globals.slop_split_keeps,
                   )
    
    # Do not Pify here. to compensate, you need to set the doNotQify option
    # to True when using the "Rehydration" tray segment.
    # tray.AddModule("PConverter",name+"_pify")

    # ==== end copy from online baseproc.py =====

    # get rid of all P-frames
    tray.AddModule(lambda f: False, name+"_noP", Streams=[icetray.I3Frame.Physics])

@icetray.traysegment
def Rehydration(tray, name, dstfile = None, mc = False, doNotQify = True, pass2=False):

    ################################
    #### REHYDRATION HERE ##########
    ################################
    
    from icecube import filter_tools, dataclasses, cramer_rao, paraboloid, portia
    from icecube import payload_parsing, lilliput, linefit
    from icecube.dst import ExtractDST
    from icecube.filterscripts.offlineL2.Recalibration import OfflineCalibration
    
    def FrameDropper(frame):
        # save only filtered frames (traditional filter + SuperDST filter)
        # delete the rest
        if not frame.Has('I3SuperDST') or not frame.Has('DSTTriggers'):
            return 0
        else:
            return 1
 
    def MaskMaker(frame):
        if frame.Has('I3SuperDST') and frame.Has('DSTTriggers'): # save only filtered frames (traditional filter + SuperDST filter) FOR NOW
            pulses = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, 'I3SuperDST')
            ii_mask = dataclasses.I3RecoPulseSeriesMapMask(frame, 'I3SuperDST')
            it_mask = dataclasses.I3RecoPulseSeriesMapMask(frame, 'I3SuperDST')
            i3geometry = frame['I3Geometry']
            for omkey in pulses.keys():
                g = i3geometry.omgeo[omkey]
                ii_mask.set(omkey, g.omtype == dataclasses.I3OMGeo.IceCube)
                it_mask.set(omkey, g.omtype == dataclasses.I3OMGeo.IceTop)

            frame['InIceDSTPulses']  = ii_mask
            frame['IceTopDSTPulses'] = it_mask
        else:
            # delete the DST-only Q frame
            # only works for data because data only has Q frames
            return 0 

    if (not mc) and (not doNotQify):
        tray.AddModule("QConverter", name+"_convert",
            WritePFrame = False
        )

    # only write dst file if asked
    if dstfile:
        tray.AddSegment(ExtractDST,"extractdst",
            dst_output_filename = dstfile,
            simulation = mc
        )
    
    if mc:
        tray.AddModule(FrameDropper, name+'_framedropper',
            Streams = [icetray.I3Frame.DAQ,icetray.I3Frame.Physics])
    else:
        if pass2: # kill off DST only P frames
            tray.AddModule(FrameDropper, name+'_framedropper',
                Streams = [icetray.I3Frame.DAQ,icetray.I3Frame.Physics])
        tray.AddModule(MaskMaker, name+'_maskme', Streams = [icetray.I3Frame.DAQ])

    tray.AddModule("Delete", name+'_deleteme',
        Keys = ['JEBEventInfo','PFContinuity']
    )

    #######################################################################
    ######## RCALIBRATION  ################################################
    # Now do Recalibration. This happens for DATA ONLY (not for sim files)#
    #######################################################################
    if not mc:
        tray.AddSegment(OfflineCalibration, name+'_recal',
            InIceOutput='InIcePulses',
            IceTopOutput='IceTopPulses',
            WavedeformSPECorrections=True, # this only needs to be done in data
            pass2=pass2) 
    else:
        # for simulation, fake calibrated outputs
        def simCalibration(frame):
            if 'InIceDSTPulses' in frame and 'InIcePulses' not in frame:
                frame['InIcePulses'] = dataclasses.I3RecoPulseSeriesMapMask(frame, 'InIceDSTPulses')
            if 'IceTopDSTPulses' in frame and 'IceTopPulses' not in frame:
                frame['IceTopPulses'] = dataclasses.I3RecoPulseSeriesMapMask(frame, 'IceTopDSTPulses')
            if 'InIceRawData' in frame and 'CleanInIceRawData' not in frame:
                frame['CleanInIceRawData'] = frame['InIceRawData']
            if 'IceTopRawData' in frame and 'CleanIceTopRawData' not in frame:
                frame['CleanIceTopRawData'] = frame['IceTopRawData']
        tray.AddModule(simCalibration, name+'_simcal',
                       Streams=[icetray.I3Frame.DAQ])

    #############Now Split ###############################################
    # The name of the module here has to be the same as the substream name that was used online
    if not mc:
        tray.AddModule('I3TriggerSplitter',name+'_InIceSplit',
            SubEventStreamName = 'InIceSplit',
            TrigHierName = 'DSTTriggers',
            InputResponses = ['InIceDSTPulses','InIcePulses'],
            OutputResponses = ['SplitInIceDSTPulses', 'SplitInIcePulses'],
            WriteTimeWindow = True,
        )
    else:
        tray.AddModule("Rename", name+'_rename_pulses',
            Keys=['SplitUncleanedInIcePulses','SplitInIceDSTPulses'])
        tray.AddModule("Rename", name+'_rename_pulses_timerange',
            Keys=['SplitUncleanedInIcePulsesTimeRange','SplitInIceDSTPulsesTimeRange'])
        def renameDSTPulses(frame):
            if 'SplitInIceDSTPulses' in frame:
                frame['SplitInIcePulses'] = dataclasses.I3RecoPulseSeriesMapMask(frame, 'SplitInIceDSTPulses')
            if 'SplitInIceDSTPulsesTimeRange' in frame:
                frame['SplitInIcePulsesTimeRange'] = frame['SplitInIceDSTPulsesTimeRange']
        tray.AddModule(renameDSTPulses, name+'_split',
                       Streams=[icetray.I3Frame.Physics])

    # 2016: re-introducing NullSplit for scintillator MinBias
    tray.AddModule("I3NullSplitter", name + '_' + filter_globals.NullSplitter,
        SubEventStreamName = filter_globals.NullSplitter)
    # No more IceTopSplit:  IceTop have their own splitting in L2

    # SLOPSplit: 
    tray.AddModule("I3TriggerSplitter", name+ "_SLOPSplit",
         SubEventStreamName='SLOPSplit',
         TrigHierName="DSTTriggers",
         InputResponses=["InIceDSTPulses", "InIcePulses"],
         OutputResponses=["SLOPDSTPulseMask", "SLOPPulseMask"],
         TriggerConfigIDs=[24002],
    )
    #######################################################################

    if mc:
        # skip the rest if simulation
        return

    # very special HACK for offline L2 of the 24h test run:
    # L1 sent "SLOPPulseMaskTimeRange" which is also generated
    # by trigger-splitter below. This has been fixed in L1,
    # but we need to remove the windows here to make it work
    # for the test runs:
    tray.AddModule("Delete", name+"very_special_SLOP_cleanup",
        Keys=["SLOPPulseMaskTimeRange_SLOPSplit0", "SLOPPulseMaskTimeRange_SLOPSplit1", "SLOPPulseMaskTimeRange_SLOPSplit2", "SLOPPulseMaskTimeRange_SLOPSplit3"])

    #some book keeping: count frames from pole
    def PoleInIceFrameCounter(frame):
        #Only for traditional filter events.... SDST filter only events don't have record of splits
        if frame.Has('FilterMask_InIceSplit0'):
            count = 0
            while True:
                if not frame.Has('FilterMask_InIceSplit'+str(count)):
                    break
                count = count + 1
            frame['PoleNInIcePFrames']=icetray.I3Int(count)
 
    tray.AddModule(PoleInIceFrameCounter, name+'count_pole', Streams=[icetray.I3Frame.DAQ])
 
    #some book keeping: count frames from trigger-splitter
    class RehydrateInIceFrameCounter(I3PacketModule):
        def __init__(self, context):
            I3PacketModule.__init__(self, context, icetray.I3Frame.DAQ)
            self.AddOutBox("OutBox")
        def Configure(self):
            pass
        def FramePacket(self, frames):
            count = 0
            for fr in frames:
                if fr['I3EventHeader'].sub_event_stream == 'InIceSplit':
                    count = count + 1
            frames[0]['RehydrateNInIcePFrames'] = icetray.I3Int(count)
            for fr in frames:
                self.PushFrame(fr)
 
    tray.AddModule(RehydrateInIceFrameCounter, name+'count_north')
 
    # Distribute pole frame objects back into P frames
    tray.AddModule("DistributePnFObjects", name+'_distribute',
        #Do not attempt to rehydrate IceTop here, it is handled in CalibrateAndExtractIceTop
        SubstreamNames = [filter_globals.NullSplitter, filter_globals.InIceSplitter, filter_globals.SLOPSplitter]
    ) 

    ################################
    #### COMPARISONS HERE ##########
    ################################

    def InIceFramesComp(frame):
        if frame.Has('PoleNInIcePFrames'):
            frame['NFramesIsDifferent'] = icetray.I3Bool(not frame['RehydrateNInIcePFrames'].value == frame['PoleNInIcePFrames'].value)
    tray.AddModule(InIceFramesComp, name+'_howaboutthemsplits', Streams=[icetray.I3Frame.DAQ])

    tray.AddModule("Delete", name+'_delete_comp_info',
        Keys = ['RehydrateNInIcePFrames','PoleNInIcePFrames'],
        If = lambda frame: frame.Has('NFramesIsDifferent') and not frame['NFramesIsDifferent'].value
    )
