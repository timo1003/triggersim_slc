#!/usr/bin/env python3
"""
Script to convert RAW i3 files into SDST i3 files.
"""

def run(gcdfile, infiles, outfile, num=-1):
    """
    Convert raw input files into a SDST output file.

    Note: Can concatenate an entire run of PFRaw files here but do NOT combine
    multiple runs!

    Args:
        gcdfile (str): filename for GCD file
        infiles (list): list of input filenames
        outfile (str): filename to write out to
        num (int): number of frames to process (default: all)
    """
    from icecube import icetray, dataclasses, dataio
    from I3Tray import I3Tray

    from icecube.filterscripts import filter_globals
    from icecube.filterscripts.pass3.l1_pre_sdst import raw_to_sdst

    tray = I3Tray()

    files = [gcdfile]+infiles
    tray.Add(dataio.I3Reader, "reader", filenamelist=files)

    # shim the D frame with IceTop Bad Doms.
    def shim_bad_icetopdoms(frame):
        if filter_globals.IcetopBadTanks not in frame:
            frame[filter_globals.IcetopBadTanks] = dataclasses.I3VectorTankKey()
        if filter_globals.IceTopBadDoms not in frame:
            frame[filter_globals.IceTopBadDoms] = dataclasses.I3VectorOMKey()

    tray.AddModule(shim_bad_icetopdoms, 'Base_shim_icetopbads',
                  Streams=[icetray.I3Frame.DetectorStatus])

    tray.AddModule('QConverter', WritePFrame=False)

    tray.AddSegment(raw_to_sdst)

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
        #'IceTopHLCPulseInfo',
        #'IceTopHLCVEMPulses',
        'IceTopPulses',
        #'IceTopPulses_HLC',
        #'IceTopPulses_SLC',
        #'IceTopSLCVEMPulses',
        'InIceDSTPulses',
        'JEBEventInfo',
        'RawDSTPulses',
        'UncleanedInIcePulses',
    ])

    # Needed features: IceTop data, seatbelts
    def FailedEHE(frame):
        return not ("QFilterMask" in frame and "EHEFilter_12" in frame["QFilterMask"]
                    and frame["QFilterMask"]["EHEFilter_12"].condition_passed) 
    tray.AddModule("Delete", Keys=["InIceRawData"], If=FailedEHE)

    tray.AddModule('I3Writer', Filename=outfile,
        Streams=[icetray.I3Frame.TrayInfo, icetray.I3Frame.DAQ, icetray.I3Frame.Physics]
    )

    # make it go
    if num >= 0:
        tray.Execute(num)
    else:
        tray.Execute()

    print("Done")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='RAW -> SDST processing')
    parser.add_argument('-g', '--gcdfile', type=str, required=True,
                        help='GCD filename')
    parser.add_argument('-i', '--infiles', type=str, action='append', required=True,
                        help='Input i3 filenames')
    parser.add_argument('-o', '--outfile', type=str, required=True,
                        help='Output i3 filename')
    parser.add_argument('-n','--num', default=-1, type=int,
                        help='Number of frames to process (default: all)')
    args = parser.parse_args()

    run(**vars(args))

if __name__ == "__main__":
    main()
