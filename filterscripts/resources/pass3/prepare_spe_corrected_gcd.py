#!/usr/bin/env python3

def run(run, spefile, outfile, skip_audit=False):
    from I3Tray import I3Tray
    from icecube import icetray, dataclasses, dataio
    from icecube.phys_services import spe_fit_injector
    from icecube.filterscripts.pass3 import gcd_generation

    tray = I3Tray()

    tray.Add(gcd_generation.generate, run_id=run)

    # inject the SPE correction data into the C frame
    tray.Add(spe_fit_injector.I3SPEFitInjector, Filename=spefile)

    if not skip_audit:
        tray.Add(gcd_generation.audit, run_id=run)

    streams = [icetray.I3Frame.Geometry, icetray.I3Frame.Calibration,
               icetray.I3Frame.DetectorStatus]
    tray.Add("I3Writer", filename=outfile, Streams=streams)

    tray.Execute()

    print("Done")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='GCD creation with SPE correction')
    parser.add_argument('-r', '--run', type=int, required=True,
                        help='Run ID')
    parser.add_argument('-s','--spefile', type=str, required=True,
                        help='Input SPE correction filename')
    parser.add_argument('-o', '--outfile', type=str, required=True,
                        help='Output GCD i3 filename')
    parser.add_argument('--skip_audit', default=True, action='store_false',
                        help='Skip auditor')
    args = parser.parse_args()

    run(**vars(args))

if __name__ == "__main__":
    main()