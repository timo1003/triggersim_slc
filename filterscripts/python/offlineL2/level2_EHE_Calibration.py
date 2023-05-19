from icecube import icetray, dataclasses, DomTools, ophelia, WaveCalibrator
from icecube.icetray import OMKey

@icetray.traysegment
def EHECalibration(tray, name, inPulses = 'CleanInIceRawData',
                   outATWD = 'EHECalibratedATWD_Wave', outFADC = 'EHECalibratedFADC_Wave',
                   If = lambda f: True,):
    #**************************************************************
    ### Run WaveCalibrator w/o droop correction. DeepCore DOMs are omitted.
    ### Split waveforms up into two maps FADC and ATWD (highest-gain unsaturated channel) 
    #**************************************************************

    # temporal. should not be needed in the actual script
    #tray.AddModule("I3EHEEventSelector", name + "inicePframe",setCriteriaOnEventHeader = True, If=If)

    # This may not be needed if the frame have HLCOfflineCleanInIceRawData
    # Actually, we like to have the bad dom cleaned launches here
    tray.AddModule( "I3LCCleaning", name + "OfflineInIceLCCleaningSLC",
                    InIceInput = inPulses, 
                    InIceOutput = "HLCOfflineCleanInIceRawData",  # ! Name of HLC-only DOMLaunches
                    InIceOutputSLC = "SLCOfflineCleanInIceRawData",  # ! Name of the SLC-only DOMLaunches
                    If = If,)

    #**************************************************************
    # removing Deep Core strings
    #**************************************************************
    tray.AddModule("I3DOMLaunchCleaning", name + "LaunchCleaning",
                   InIceInput = "HLCOfflineCleanInIceRawData",
                   InIceOutput = "HLCOfflineCleanInIceRawDataWODC",
                   CleanedKeys = [OMKey(a,b) for a in range(79, 87) for b in range(1, 61)],
		   IceTopInput = "CleanIceTopRawData", #nk: Very important! otherwise it re-cleans IT!!!
		   IceTopOutput = "CleanIceTopRawData_EHE", #nk: okay so this STILL tries to write out IceTop.. give different name
                   If = If,)
    
    #***********************************************************
    # Calibrate waveforms without droop correction
    #***********************************************************
    tray.AddModule("I3WaveCalibrator", name + "calibrator",
                   Launches="HLCOfflineCleanInIceRawDataWODC",
                   Waveforms="EHEHLCCalibratedWaveforms",
                   ATWDSaturationMargin=123, # 1023-900 == 123
                   FADCSaturationMargin=0,
                   CorrectDroop=False,
		   WaveformRange="", #nk: don't write out Calibrated Waveform Range... already written with default name by Recalibration.py
                   If = If, )

    tray.AddModule("I3WaveformSplitter", name + "split",
                   Input="EHEHLCCalibratedWaveforms",
                   HLC_ATWD = outATWD,
                   HLC_FADC = outFADC,
                   Force=True,
                   PickUnsaturatedATWD=True,
                   If = If, )

    tray.AddModule("Delete",name + "EHE_Cleanup",
                   keys=['HLCOfflineCleanInIceRawData', 'SLCOfflineCleanInIceRawData',
                         'EHEHLCCalibratedWaveforms','CleanIceTopRawData_EHE'])
