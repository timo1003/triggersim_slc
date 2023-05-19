import os
from icecube import icetray, dataclasses, filter_tools
from icecube import phys_services, WaveCalibrator, topeventcleaning, tpx
from icecube import payload_parsing
from icecube.filterscripts import filter_globals
from icecube.filterscripts.all_filters import OnlineFilter
from icecube.filterscripts import filter_globals

@icetray.traysegment
def sdst_to_l1(tray, name, ic79_geometry=False):
    """SDST to L1, the second part of L1"""
    # Run startup is complicated, and data may be recorded before it is complete.
    # As a result, we need to listen to what the DAQ says was the range of times 
    # when everything was really up and running, and discard events outside. 
    def clip_start_stop(frame):
        if not frame.Has("I3EventHeader"):
            return False # No header? No good!
        header = frame["I3EventHeader"]
        if frame.Has("GoodRunStartTime"):
            if frame["GoodRunStartTime"] > header.start_time:
                return False # event began too early
        if frame.Has("GoodRunEndTime"):
            if frame["GoodRunEndTime"] < header.end_time:
                return False # event ended too late
    tray.AddModule(clip_start_stop,Streams=[icetray.I3Frame.DAQ])

    # ~ # decode the IceTop saved waveforms (DAQ data format in I3DAQDataIceTop
    # ~ def it_decode_needed(frame):
        # ~ if frame.Has("IceTopRawData"):
            # ~ return False
        # ~ else:
            # ~ return True
    # ~ tray.AddSegment(payload_parsing.I3DOMLaunchExtractor,
                    # ~ 'Make_IT_launches',
                    # ~ BufferID = 'I3DAQDataIceTop',
                    # ~ TriggerID = '',
                    # ~ HeaderID = '',
                    # ~ InIceID = 'UnusedInIce',
                    # ~ If = it_decode_needed
                    # ~ )
    # ~ # now clean out the Unused (and empty) inice readout
    # ~ tray.AddModule("Delete","InInceRaw_Cleaner",Keys=["UnusedInIceRawData"])


    # ~ # HACK #2: re-run IceTop calibration
    # ~ tray.AddModule("Delete", "IceTop_recal_cleanup", Keys=['IceTopErrata'])
    # ~ tray.AddModule("I3WaveCalibrator", "WaveCalibrator_IceTop",
           # ~ Launches="IceTopRawData",
           # ~ Waveforms="IceTopCalibratedWaveforms", Errata="IceTopErrata",
           # ~ WaveformRange="")
    # ~ tray.AddModule('I3WaveformSplitter', 'WaveformSplitter_IceTop',
           # ~ Force=True, Input='IceTopCalibratedWaveforms',
           # ~ PickUnsaturatedATWD=True, HLC_ATWD='CalibratedIceTopATWD_HLC',
           # ~ HLC_FADC='CalibratedIceTopFADC_HLC', SLC='CalibratedIceTopATWD_SLC')
    # ~ tray.AddModule('I3TopHLCPulseExtractor', 'tpx_hlc',
           # ~ Waveforms='CalibratedIceTopATWD_HLC', PEPulses='IceTopPulses_HLC',
           # ~ PulseInfo='IceTopHLCPulseInfo', VEMPulses='IceTopHLCVEMPulses',
           # ~ MinimumLeadingEdgeTime = -100.0*icetray.I3Units.ns, BadDomList=filter_globals.IceTopBadDoms)
    # ~ tray.AddModule('I3TopSLCPulseExtractor', 'tpx_slc',
           # ~ Waveforms='CalibratedIceTopATWD_SLC', PEPulses='IceTopPulses_SLC',
           # ~ VEMPulses='IceTopSLCVEMPulses', BadDomList=filter_globals.IceTopBadDoms)

    # the online filter scripts assume the triggers are in a frame object
    # called "I3TriggerHierarchy". SuperDST only has "DSTTriggers" (the compressed
    # version). Make a copy for now so it is accessible with the other name.
    # After the filter has been run, it should be named "QTriggerHierarchy".
    # The "QTriggerHierarchy" will be cleaned up by the "Keep" modules later on
    # anyway.
    def copyTriggers(frame):
        if "I3TriggerHierarchy" in frame:
            raise RuntimeError("I3TriggerHierarchy unexpectedly already in frame")
        frame["I3TriggerHierarchy"] = frame["DSTTriggers"]
    tray.AddModule(copyTriggers, "copyTriggers", Streams=[icetray.I3Frame.DAQ])

    # run the online filter
    tray.AddSegment(OnlineFilter, "OnlineFilter",
                    sdstarchive=True, # our input data is SDST archive data
                    # Officially there is no BDL in L1 but OnlineL2 needs
                    # one. In real production this is hard-coded, but it might
                    # not apply to the data we are looking at. So just use
                    # the offline bad DOM list in this case.

                    needs_wavedeform_spe_corr=False, # we already corrected it
                    alert_followup_omit_GCD_diff=True,
                    forceOnlineL2BadDOMList="BadDomsList_old", 
                    ic79_geometry = ic79_geometry,
                    #gfu_enabled=False # to run without ROOT
    )

    # now clean up the frame using the Keep module... 
    # (this is supposed to emulate dehydration at Pole and rehydration in L2)

    # Generate filter Masks for all P frames
    filter_mask_randoms = phys_services.I3GSLRandomService(9999)
    filter_mask_configs = dataclasses.I3MapStringInt(filter_globals.filter_pairs + filter_globals.sdst_pairs)
    tray.AddModule("FilterMaskMaker", "MakeFilterMasks",
                   OutputMaskName = filter_globals.filter_mask,                   
                   FilterConfigs = filter_mask_configs,
                   RandomService = filter_mask_randoms)

    # Merge the FilterMasks into Q frame:
    tray.AddModule("OrPframeFilterMasks", "make_q_filtermask",
                   InputName = filter_globals.filter_mask,
                   OutputName = filter_globals.qfilter_mask)

    #Q+P frame specific keep module needs to go first,  you can add additional items you 
    ##  want to keep for your filter testing.

    def keep(frame, keys):
        keys = set(keys)
        for k in frame.keys():
            if k not in keys:
                del frame[k]

    tray.AddModule(keep,"keep_before_merge",
                   keys=filter_globals.q_frame_keeps + ['I3DAQData', 'DSTPulses', "I3DAQDataTrimmed", "I3SuperDSTUnChargeCorrected", "IceTopRawData", "TriggerSplitterLaunchWindow"],
                   Streams=[icetray.I3Frame.DAQ])

    def removeRawData(frame):
        keepRaw=False;
        filtermask=frame["QFilterMask"];
        for filter in filter_globals.filters_keeping_allraw:
            if filter in filtermask and filtermask[filter].condition_passed:
                keepRaw=True;
                break;
        if not keepRaw:
            frame.Delete("I3DAQDataTrimmed")
    tray.AddModule(removeRawData,Streams = [icetray.I3Frame.DAQ]);

    tray.AddModule("I3IcePickModule<FilterMaskFilter>","filterMaskCheckAll",
                   FilterNameList = filter_globals.filter_streams,
                   FilterResultName = filter_globals.qfilter_mask,
                   DecisionName = "PassedAnyFilter",
                   DiscardEvents = False, 
                   Streams = [icetray.I3Frame.DAQ]
                   )

    def do_save_just_superdst(frame):
        if not (frame.Stop==icetray.I3Frame.DAQ or frame.Stop==icetray.I3Frame.Physics):
            return False
        if frame.Has("PassedAnyFilter"):
            if not frame["PassedAnyFilter"].value:
                return True    #  <- Event failed to pass any filter.
            else:
                return False   #  <- Event passed some filter

        else:
            print("Failed to find key frame Bool!!")
            return False

    tray.AddModule(keep, "KeepOnlySuperDSTs",
                   keys = filter_globals.keep_nofilterpass+["PassedAnyFilter", 'DSTPulses', "I3SuperDSTUnChargeCorrected"],
                   If = do_save_just_superdst,
                   Streams = [icetray.I3Frame.DAQ, icetray.I3Frame.Physics]
                   )

    tray.AddModule("I3IcePickModule<FilterMaskFilter>","filterMaskCheckSDST",
                   FilterNameList = filter_globals.sdst_streams,
                   FilterResultName = filter_globals.qfilter_mask,
                   DecisionName = "PassedKeepSuperDSTOnly",
                   DiscardEvents = False,
                   Streams = [icetray.I3Frame.DAQ]
                   )

    def dont_save_superdst(frame):
        if not (frame.Stop==icetray.I3Frame.DAQ or frame.Stop==icetray.I3Frame.Physics):
            return False
        if frame.Has("PassedKeepSuperDSTOnly") and frame.Has("PassedAnyFilter"):
            if frame["PassedAnyFilter"].value:
                return False  #  <- these passed a regular filter, keeper
            elif not frame["PassedKeepSuperDSTOnly"].value:
                return True    #  <- Event failed to pass SDST filter.
            else:
                return False # <- Event passed some  SDST filter
        else:
            return False


    tray.AddModule(keep, "KeepOnlyDSTs",
                   keys = filter_globals.keep_dst_only
                          + ["PassedAnyFilter","PassedKeepSuperDSTOnly"]
                          + [filter_globals.eventheader,
                             ##filter_globals.qfilter_mask
                             ],
                   If = dont_save_superdst,
                   Streams = [icetray.I3Frame.DAQ, icetray.I3Frame.Physics]
                   )

    from icecube.filterscripts.offlineL2.Rehydration import Dehydration
    tray.AddSegment(Dehydration, "squish")
