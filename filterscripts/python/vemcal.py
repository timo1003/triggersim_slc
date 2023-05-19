#
# modules used for vemcal  processing
#

from icecube import icetray

#**************************************************
#              IceTop VEM calibration stuff
#**************************************************

@icetray.traysegment
def IceTopVEMCal(tray, name):
     
     from icecube import dataio, WaveCalibrator
     from icecube.icetray import OMKey, I3Units
     from icecube.filterscripts import filter_globals
     icetray.load('tpx', False)
     icetray.load('vemcal', False)
     
     # Calibrate all IceTopMinBias hits
     tray.AddModule("I3WaveCalibrator", name + "_wavecal_minbias",
                    Launches="IceTopMinBias",
                    Waveforms="CalibratedWaveforms_minbias",
                    ATWDSaturationMargin=123, # 1023-900 == 123
                    FADCSaturationMargin=0,
                    Errata = 'CalibrationErrata_' + name, 
		    WaveformRange='VEMCalibratedWaveformRange',
                    If = lambda f: 'IceTopMinBias' in f
                    )
     
     tray.AddModule("I3WaveformSplitter", name + "_split_minbias",
                    Input="CalibratedWaveforms_minbias",
                    HLC_ATWD="IceTopMinBiasCalATWD",
                    HLC_FADC="CalibratedFADC_minbias",  # not used by icetop
                    SLC="CalibratedSLC_minbias",        # not used by icetop
                    PickUnsaturatedATWD=True
                    )
     
     tray.AddModule("I3TopHLCPulseExtractor", name + "_tpx_minbias",
                    Waveforms="IceTopMinBiasCalATWD",
                    PEPulses="IceTopMinBiasPulses",
                    VEMPulses="",
                    PulseInfo="IceTopMinBiasPulsesInfo",
                    MinimumLeadingEdgeTime=-100.0*I3Units.ns,
                    BadDomList=filter_globals.IceTopBadDoms
                    )
     
     tray.AddModule("I3HGLGPairSelector", name + "_hglg_selector",
                    InputPulses = filter_globals.IceTopPulses_HLC,
                    OutputPulseMask = "IceTopHGLGPulses"
                    )
     
    #              IceTop VEMCalExtractor
     tray.AddModule("I3VEMCalExtractor", name + "_vemcal_extract",
                    IceTopMinBiasPulsesName = "IceTopMinBiasPulses",
                    IceTopPulsesName        = "IceTopHGLGPulses",
                    ShowerVeto              = filter_globals.CleanIceTopRawData,
                    VEMCalDataName          = filter_globals.icetop_vemcal
                    )
     
    #              IceTop MuonCalibration Filter
     def IceTopMuonCalibrationFilter(frame):
          decision = icetray.I3Bool(filter_globals.icetop_vemcal in frame)
          frame['IceTopMuonCalibration_13'] = decision
          return True
     
     tray.AddModule(IceTopMuonCalibrationFilter, name + "_vemcal_filter",
                    Streams = [icetray.I3Frame.DAQ])
