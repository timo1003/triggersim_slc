#!/usr/bin/env python3

from I3Tray import *

from icecube import icetray, dataclasses, dataio
from icecube.phys_services import spe_fit_injector

if len(sys.argv)!=4:
	print("Usage: prepare_spe_corrected_gcd.py input_gcd spe_correction_file output_gcd")
	exit(1)

inputfile = sys.argv[1]
spe_file = sys.argv[2]
outputfile = sys.argv[3]

tray = I3Tray()

tray.AddModule("I3Reader", "reader", filenamelist=[inputfile])

# inject the SPE correction data into the C frame
tray.AddModule(spe_fit_injector.I3SPEFitInjector, "fixspe",  Filename = spe_file)

tray.AddModule("I3Writer", filename=outputfile, CompressionLevel=9)
tray.Execute()
