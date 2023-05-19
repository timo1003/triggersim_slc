#!/usr/bin/env python3
"""
Script to convert SDST i3 files into L2 i3 files for pass3.
"""

def run(gcdfile, infiles, outfile, gapsfile=None, num=-1, ic79_geometry=False):
    """
    Convert SDST input files into a L2 output file.

    Note: Can concatenate an entire run of SDST files here but do NOT combine
    multiple runs!

    Args:
        gcdfile (str): filename for GCD file
        infiles (list): list of input filenames
        outfile (str): filename to write out to
        gapsfile (str): filename to write gaps txt file to (default: no file)
        num (int): number of frames to process (default: all)
        ic79_geometry (bool): is this ic79? (default: False)
    """
    from I3Tray import I3Tray
    from icecube import icetray, dataclasses, dataio
    from icecube.filterscripts.pass3.l1_post_sdst import sdst_to_l1
    from icecube.filterscripts.offlineL2.level2_all_filters import OfflineFilter
    from icecube.filterscripts.offlineL2 import SpecialWriter

    icetray.logging.console()
    icetray.I3Logger.global_logger.set_level(icetray.I3LogLevel.LOG_WARN)
    icetray.I3Logger.global_logger.set_level_for_unit('I3FilterModule', icetray.I3LogLevel.LOG_INFO)

   
    tray = I3Tray()

    files = [gcdfile] + infiles
    tray.context['I3FileStager'] = dataio.get_stagers()
    tray.AddModule("I3Reader", "reader",
        filenamelist=files)

    # SPS GCD files do not have any bad DOM information. Rename it
    # so that modules in L1 processing don't use it...
    def rename_bad_DOM_lists(frame):
        for k in ('BadDomsList', 'BadDomsListSLC', 'IceTopBadDOMs', 'IceTopBadTanks'):
            if k in frame:
                frame[k+'_old'] = frame[k]
                del frame[k]
    tray.AddModule(rename_bad_DOM_lists, "rename_bad_DOM_lists",
        Streams=[icetray.I3Frame.DetectorStatus])

    # remainder of L1 processing
    tray.AddSegment(sdst_to_l1, ic79_geometry=ic79_geometry)

    # restore GCD bad DOM object names to original
    def restore_bad_DOM_lists(frame):
        for k in ('BadDomsList', 'BadDomsListSLC', 'IceTopBadDOMs', 'IceTopBadTanks'):
            if k+'_old' in frame:
                frame[k] = frame[k+'_old']
                del frame[k+'_old']
    tray.AddModule(restore_bad_DOM_lists, "restore_bad_DOM_lists",
        Streams=[icetray.I3Frame.DetectorStatus])

    # L2 processing
    tray.AddSegment(OfflineFilter, 'OfflineFilter',
        dstfile=None,
        mc=False, # (no real P-to-Q conversion here)
        doNotQify=True,
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

    # Write the physics and DAQ frames
    tray.AddModule("I3Writer", "EventWriter",
            filename=outfile,
            Streams=[icetray.I3Frame.TrayInfo, icetray.I3Frame.Physics, icetray.I3Frame.DAQ]
    )

    if gapsfile:
        tray.AddSegment(SpecialWriter.GapsWriter, "write_gaps",
            Filename=gapsfile,
            MinGapTime=1
        )

    if num >= 0:
        tray.Execute(num)
    else:
        tray.Execute()

    # print more CPU usage info. than speicifed by default
    tray.PrintUsage(fraction=1.0) 

def main():
    import argparse
    parser = argparse.ArgumentParser(description='RAW -> SDST processing')
    parser.add_argument('-g', '--gcdfile', type=str, required=True,
                        help='GCD filename')
    parser.add_argument('-i', '--infiles', type=str, action='append', required=True,
                        help='Input i3 filenames')
    parser.add_argument('-o', '--outfile', type=str, required=True,
                        help='Output i3 filename')
    parser.add_argument("--gapsfile", default=None,
                        help="gaps text file, should be .txt (default: do not generate)")
    parser.add_argument('-n','--num', default=-1, type=int,
                        help='Number of frames to process (default: all)')
    parser.add_argument("--ic79-geometry", action="store_true", default=False,
                      dest="ic79_geometry", help="Enable if you are processing data of IC79.")
    args = parser.parse_args()

    run(**vars(args))

if __name__ == "__main__":
    main()

