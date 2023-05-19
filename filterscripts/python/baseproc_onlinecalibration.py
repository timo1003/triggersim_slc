from icecube import icetray

## Import the 2.4 compatibility helpers for SPS/SPTS python
from icecube.icetray.pycompat import *

from . import filter_globals

@icetray.traysegment
def DOMCleaning(tray, name,
    CleanInIceRawData=filter_globals.CleanInIceRawData,
    CleanIceTopRawData=filter_globals.CleanIceTopRawData):
	"""
	Apply DOMLaunch cleaning with permanent bad doms
	"""
	from icecube.icetray import OMKey
	icetray.load("DomTools", False)
	#  DOMLaunch cleaning.
	#  default inputs :InIceRawData and IceTopRawData
	#  default outputs: CleanInIceRawData and CleanIceTopRawData
	#  other important defaults:  FirstLaunchCleaning==False
	bad_doms = [OMKey(1,46),     # Dovhjort
		    OMKey(7,34),     # Grover
		    OMKey(7,44),     # Ear_Muffs
		    OMKey(22,49),    # Les_Arcs
		    OMKey(33, 6),    # Skorpionen
		    OMKey(38,59),    # Blackberry
		    OMKey(60,55),    # Schango
		    OMKey(68,42)     # Krabba
		    ]
	tray.AddModule("I3DOMLaunchCleaning", name + '_baddomclean',
		       CleanedKeys=bad_doms,
		       InIceOutput=CleanInIceRawData,
		       IceTopOutput=CleanIceTopRawData
		       )

        
@icetray.traysegment
def OnlineCalibration(tray, name, simulation = False,
    WavedeformSPECorrections = True,
    CleanInIceRawData=filter_globals.CleanInIceRawData,
    CleanIceTopRawData=filter_globals.CleanIceTopRawData,
    InIcePulses=filter_globals.UncleanedInIcePulses,
    IceTopPulses='IceTopPulses',
    Harvesting = False):
	"""
	Apply the Waveform calibration and pulse extraction.
	"""
	from icecube import dataclasses, WaveCalibrator
	from icecube.icetray import I3Units
	from icecube.filterscripts.baseproc_superdst import Unify
	icetray.load("DomTools", False)
	icetray.load("wavedeform", False)
	icetray.load("tpx", False)
	icetray.load("topeventcleaning", False)
	
	# InIce WaveCalibrator.
	# and Feature Extraction: wavedform
	if not simulation:
		print(('Wavecalibrator for data selected, SPE_corr: ', WavedeformSPECorrections))
		tray.AddModule('I3WaveCalibrator', name + '_wavecal',
			       Launches=CleanInIceRawData,
			       )
		tray.AddModule('I3PMTSaturationFlagger', name + '/saturationflagger')
		tray.AddModule('I3Wavedeform', name + '_wavedeform',
		       ApplySPECorrections = WavedeformSPECorrections,
		       Output=InIcePulses)
	else:
		tray.AddModule('I3WaveCalibrator', name + '_wavecal',
				Launches=CleanInIceRawData,
				)
		tray.AddModule('I3PMTSaturationFlagger', name + '/saturationflagger')
		tray.AddModule('I3Wavedeform', name + '_wavedeform',
		       ApplySPECorrections = WavedeformSPECorrections,
		       Output=InIcePulses)

        # For calibration harvesting run, split the waveform series
        # and run wavedeform on FADC and ATWD separately, with deweight FADC turned off
        # for FADC and SPE correction turned off for all
	if Harvesting:
            tray.AddModule('I3WaveformSplitter', name + 'harvestsplitter',
			   SplitATWDChannels = True,
			   HLC_ATWD = 'HarvestCalATWD',
			   HLC_FADC = 'HarvestCalFADC'
			   )
            tray.AddModule('I3Wavedeform', name + 'harvest_wd_atwd',
			   Waveforms = 'HarvestCalATWD_0',
			   Output = 'HarvestingPulses_ATWD',
			   ApplySPECorrections = False
			   )
            tray.AddModule('I3Wavedeform', name + 'harvest_wd_fadc',
			   Waveforms = 'HarvestCalFADC',
			   Output = 'HarvestingPulses_FADC',
			   ApplySPECorrections = False,
			   DeweightFADC = False
			   )
            tray.AddModule('I3Wavedeform', name + 'harvest_wd',
			   Waveforms = 'CalibratedWaveforms',
			   Output = 'HarvestingPulses',
			   ApplySPECorrections = False
			   )


	# IceTop processing-> sanity checks (bad doms...) during GCD generation?;
	# calibrate, split, feature extract.
	#
	#Find a better name for the variables here?

	tray.AddModule("I3WaveCalibrator", name+"_WaveCalibrator_IceTop",
		       Launches=CleanIceTopRawData,
		       Waveforms="IceTopCalibratedWaveforms", 
		       Errata="IceTopErrata",
		       WaveformRange='IceTopCalibratedWaveformRange')
	tray.AddModule('I3WaveformSplitter', name+'_WaveformSplitter_IceTop',
		       Force=True, Input='IceTopCalibratedWaveforms',
		       PickUnsaturatedATWD=True, HLC_ATWD='CalibratedIceTopATWD_HLC',
		       HLC_FADC='CalibratedIceTopFADC_HLC', SLC='CalibratedIceTopATWD_SLC')
	tray.AddModule('I3TopHLCPulseExtractor', 'tpx_hlc',
		       Waveforms='CalibratedIceTopATWD_HLC', PEPulses=filter_globals.IceTopPulses_HLC,
		       PulseInfo='IceTopHLCPulseInfo', VEMPulses='IceTopHLCVEMPulses',
		       MinimumLeadingEdgeTime = -100.0*I3Units.ns, BadDomList=filter_globals.IceTopBadDoms)
	tray.AddModule('I3TopSLCPulseExtractor', 'tpx_slc',
		       Waveforms='CalibratedIceTopATWD_SLC', PEPulses=filter_globals.IceTopPulses_SLC,
		       VEMPulses='IceTopSLCVEMPulses', 
           BadDomList=filter_globals.IceTopBadDoms)

	# Combine the all  IceTop RecoPulseSeries into a single RPS, ready for DST
	tray.AddModule(Unify, name+'_unify_icetop',
		       Keys=[filter_globals.IceTopPulses_HLC, filter_globals.IceTopPulses_SLC],
		       Output=IceTopPulses, Streams=[icetray.I3Frame.DAQ])
