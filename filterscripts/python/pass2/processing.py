#!/usr/bin/env python3

def process_sdst_archive_to_l2(tray, spe_correction_is_already_applied = False, ic79_geometry = False):
    import os
    from icecube import icetray, dataclasses, dataio, filterscripts, filter_tools
    from icecube import phys_services, WaveCalibrator, topeventcleaning, tpx
    from icecube.filterscripts import filter_globals
    from icecube.filterscripts.all_filters import OnlineFilter
    from icecube import payload_parsing
    

    # we might not have cvmfs, but $I3_DATA should exist
    if 'I3_DATA' in os.environ:
        TableDir = os.path.expandvars("$I3_DATA/photon-tables/")
    elif os.path.isdir('/cvmfs/icecube.opensciencegrid.org/data'):
        TableDir = os.path.expandvars("/cvmfs/icecube.opensciencegrid.org/data/photon-tables/")
    else:
        raise Exception('cannot find I3_DATA or cvmfs, no photon tables available')
    SplineDir = os.path.join(TableDir, "splines")
    SplineRecoAmplitudeTable = os.path.join(SplineDir, 'InfBareMu_mie_abs_z20a10_V2.fits')
    SplineRecoTimingTable = os.path.join(SplineDir, 'InfBareMu_mie_prob_z20a10_V2.fits')

    ## Prep the logging hounds.
    icetray.logging.console()
    icetray.I3Logger.global_logger.set_level(icetray.I3LogLevel.LOG_WARN)
    icetray.I3Logger.global_logger.set_level_for_unit('I3FilterModule', icetray.I3LogLevel.LOG_INFO)

    # Some PFDST files have FilterMasks already. 
    # Since we are going to recalculate the filters, these need to go away. 
    tray.AddModule("Delete","ClearOldFilters",Keys=["FilterMask"])

    # Run startup is complicated, and data may be recorded before it is complete.
    # As a result, we need to listen to what the DAQ says was the range of times 
    # when everything was really up and running, and discard events outside. 
    def clip_start_stop(frame):
        if not frame.Has("I3EventHeader"):
            return False # No header? No good!
        header = frame["I3EventHeader"]
        if frame.Has("GoodRunStartTime"):
            if frame["GoodRunStartTime"]>header.start_time:
                return False # event began too early
        if frame.Has("GoodRunEndTime"):
            if frame["GoodRunEndTime"]<header.end_time:
                return False # event ended too late
    tray.AddModule(clip_start_stop,Streams=[icetray.I3Frame.DAQ])

    # perform retroactive SPE correction on the SuperDST pulses
    # (unless the user told us that the input charges are already corrected)
    if not spe_correction_is_already_applied:
        tray.AddModule("Rename",Keys=["I3SuperDST","I3SuperDSTUnChargeCorrected"])
        def correctCharges(frame):
            if not frame.Has("I3SuperDSTUnChargeCorrected"):
                icetray.logging.log_fatal("Frame without SuperDST data")
            if not frame.Has("I3Calibration"):
                icetray.logging.log_fatal("No calibration")
            frame["I3SuperDST"]=dataclasses.I3RecoPulseSeriesMapApplySPECorrection("I3SuperDSTUnChargeCorrected","I3Calibration")
        tray.AddModule(correctCharges,Streams=[icetray.I3Frame.DAQ])

    # HACK #1: SPS GCD files do not have any bad DOM information. Rename it
    # so that modules in L1 processing don't use it...
    def rename_bad_DOM_lists(frame):
        for k in ('BadDomsList', 'BadDomsListSLC', 'IceTopBadDOMs', 'IceTopBadTanks'):
            frame[k+'_old'] = frame[k]
            del frame[k]
    tray.AddModule(rename_bad_DOM_lists, "rename_bad_DOM_lists",
        Streams=[icetray.I3Frame.DetectorStatus])

    # decode the IceTop saved waveforms (DAQ data format in I3DAQDataIceTop
    def it_decode_needed(frame):
        if frame.Has("IceTopRawData"):
            return False
        else:
            return True
    tray.AddSegment(payload_parsing.I3DOMLaunchExtractor,
                    'Make_IT_launches',
                    BufferID = 'I3DAQDataIceTop',
                    TriggerID = '',
                    HeaderID = '',
                    InIceID = 'UnusedInIce',
                    If = it_decode_needed
                    )
    # now clean out the Unused (and empty) inice readout
    tray.AddModule("Delete","InInceRaw_Cleaner",Keys=["UnusedInIceRawData"])


    # HACK #2: re-run IceTop calibration
    tray.AddModule("Delete", "IceTop_recal_cleanup", Keys=['IceTopErrata'])
    tray.AddModule("I3WaveCalibrator", "WaveCalibrator_IceTop",
           Launches="IceTopRawData",
           Waveforms="IceTopCalibratedWaveforms", Errata="IceTopErrata",
           WaveformRange="")
    tray.AddModule('I3WaveformSplitter', 'WaveformSplitter_IceTop',
           Force=True, Input='IceTopCalibratedWaveforms',
           PickUnsaturatedATWD=True, HLC_ATWD='CalibratedIceTopATWD_HLC',
           HLC_FADC='CalibratedIceTopFADC_HLC', SLC='CalibratedIceTopATWD_SLC')
    tray.AddModule('I3TopHLCPulseExtractor', 'tpx_hlc',
           Waveforms='CalibratedIceTopATWD_HLC', PEPulses='IceTopPulses_HLC',
           PulseInfo='IceTopHLCPulseInfo', VEMPulses='IceTopHLCVEMPulses',
           MinimumLeadingEdgeTime = -100.0*icetray.I3Units.ns, BadDomList=filter_globals.IceTopBadDoms)
    tray.AddModule('I3TopSLCPulseExtractor', 'tpx_slc',
           Waveforms='CalibratedIceTopATWD_SLC', PEPulses='IceTopPulses_SLC',
           VEMPulses='IceTopSLCVEMPulses', BadDomList=filter_globals.IceTopBadDoms)

    # HACK #3: the online filter scripts assume the triggers are in a frame object
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
                    # HACK #3.5:
                    # Officially there is no BDL in L1 but OnlineL2 needs
                    # one. In real production this is hard-coded, but it might
                    # not apply to the data we are looking at. So just use
                    # the offline bad DOM list in this case.
                    forceOnlineL2BadDOMList="BadDomsList_old", 
                    #gfu_enabled=False,
                    #ehealert_followup=False,
                    #hese_followup_base_GCD_filename=None,
                    hese_followup_omit_GCD_diff=True,
                    needs_wavedeform_spe_corr=False, # we already corrected it

                    SplineRecoAmplitudeTable = SplineRecoAmplitudeTable,
                    SplineRecoTimingTable = SplineRecoTimingTable,
                    PathToCramerRaoTable = None, # automatic guess should work here

                    ic79_geometry = ic79_geometry
                    )

    # now clean up the frame using the Keep module... 
    # (this is supposed to emulate dehydration at Pole and rehydration in L2)

    # Generate filter Masks for all P frames
    filter_mask_randoms = phys_services.I3GSLRandomService(9999)
    tray.AddModule(filter_tools.FilterMaskMaker, "MakeFilterMasks",
                   OutputMaskName = filter_globals.filter_mask,
                   FilterConfigs = filter_globals.filter_pairs + filter_globals.sdst_pairs,
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
    tray.AddSegment(Dehydration,"squish")

    # HACK #4: restore GCD bad DOM object names to original
    def restore_bad_DOM_lists(frame):
        for k in ('BadDomsList', 'BadDomsListSLC', 'IceTopBadDOMs', 'IceTopBadTanks'):
            frame[k] = frame[k+'_old']
            del frame[k+'_old']
    tray.AddModule(restore_bad_DOM_lists, "restore_bad_DOM_lists",
        Streams=[icetray.I3Frame.DetectorStatus])


    from icecube.filterscripts.offlineL2.level2_all_filters import OfflineFilter
    tray.AddSegment(OfflineFilter, 'OfflineFilter',
        dstfile=None,
        mc=False, # (no real P-to-Q conversion here)
        doNotQify=True,
        photonicsdir=TableDir,
        pass2=True,
        )
                    
    # clean up excess IceTop data
    # some versions of the PFDST processing keep the DAQ payloads, but no one should need those
    tray.AddModule("Delete", "remove_IT_payloads",
        Keys=["I3DAQDataIceTop"])
    # IceTop launches will have been kept for every frame, but we only need the ones associated with an IceTop filter
    def remove_extra_IceTop_launches(frame):
        relevant_filters=["IceTopSTA3_13","IceTopSTA5_13",
          "IceTop_InFill_STA3_13","InIceSMT_IceTopCoincidence_13"]
        if not frame.Has("QFilterMask"):
            frame.Delete("IceTopRawData")
            frame.Delete("CleanIceTopRawData")
            return
        filter_mask=frame["QFilterMask"]
        keep=False
        for filter in relevant_filters:
            if filter in filter_mask and (filter_mask[filter].condition_passed and filter_mask[filter].prescale_passed):
                keep=True
        if not keep:
            frame.Delete("IceTopRawData")
            frame.Delete("CleanIceTopRawData")
    tray.AddModule(remove_extra_IceTop_launches,"remove_extra_IceTop_launches",
        Streams=[icetray.I3Frame.DAQ])
