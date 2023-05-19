from icecube import icetray

@icetray.traysegment
def EHECalibration(tray, name, If=lambda f:True):
    """
    Run WaveCalibrator w/o droop correction. DeepCore DOMs are omitted. 
    Split waveforms up into two maps FADC and ATWD (highest-gain unsaturated channel)
    """

    from icecube import dataclasses, WaveCalibrator
    from icecube.filterscripts import filter_globals
    icetray.load("DomTools", False)

    # take CleanInIceRawData from OnlineCalibration
    # and skip DeepCoreStrings
    tray.AddModule('I3OMSelection<I3DOMLaunchSeries>', 'skip_DeepCore',
                   InputResponse =filter_globals.CleanInIceRawData,
                   OmittedStrings=[79, 80, 81, 82, 83, 84, 85, 86],
                   OutputResponse='CleanInIceRawData_noDC',
                   If = If
                   )

    #define HLC and SLC-only DOMLaunches
    tray.AddModule( 'I3LCCleaning', 'CleaningSLC',
                    InIceInput ='CleanInIceRawData_noDC',
                    InIceOutput='HLCCleanInIceRawData_noDC',#! Name of HLC-only DOMLaunches
                    InIceOutputSLC='SLCCleanInIceRawData_noDC', #! Name of the SLC-only DOMLaunches
                    If = If)

    # no droop correction for the EHEFilter 
    tray.AddModule('I3WaveCalibrator', 'EHEWaveCalibrator',
                   CorrectDroop= False,
                   Launches ='HLCCleanInIceRawData_noDC',
                   Waveforms='EHECalibratedWaveforms',
                   Errata = 'CalibrationErrata_' + name,
                   WaveformRange = 'CalibratedWaveformRange' + name,
                   If = If
                   )

    # write ATWD and FADC waveforms into two separate maps 
    # pick the highest-gain ATWD-channel that is not saturated 
    tray.AddModule('I3WaveformSplitter', 'EHEWaveformSplitter',
                   Input   ='EHECalibratedWaveforms',
                   PickUnsaturatedATWD=True,
                   HLC_ATWD='EHECalibratedATWD',
                   HLC_FADC='EHECalibratedFADC',
                   SLC     ='EHECalibratedGarbage',
                   Force   =True,
                   If = If
                   )

@icetray.traysegment
def EHEFilter(tray, name,  If=lambda f: True, QIf=lambda f:True):

    """
    EHEFilter
    """

    from icecube.icetray import I3Units
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts" , False)
    icetray.load("portia" , False)
    
    tray.AddSegment(EHECalibration, name+'_calibration', If=QIf)


    #***********************************************************                    
    # portia splitter                                             
    # This module takes the splitted start time and end time and makes split DOM map
    #***********************************************************
    tray.AddModule("I3PortiaSplitter", name + "EHE-SplitMap-Maker",
                   DataReadOutName="HLCCleanInIceRawData_noDC",
                   SplitDOMMapName="splittedDOMMap",
                   SplitLaunchTime=True,
                   TimeWindowName = "TriggerSplitterLaunchWindow",
                   If = If,)


    #***************************************************************  
    #     Portia Pulse process  with the spllit DOM map for SeededRT seed 
    #***************************************************************
    tray.AddModule("I3Portia", name + "pulseSplitted",
                   SplitDOMMapName = "splittedDOMMap",
                   OutPortiaEventName = "PoleEHESummaryPulseInfo",
                   ReadExternalDOMMap=True,
                   MakeIceTopPulse=False,
                   ATWDPulseSeriesName = "EHEATWDPulseSeries",
                   ATWDPortiaPulseName = "EHEATWDPortiaPulse",
                   ATWDWaveformName = "EHECalibratedATWD",
                   ATWDBaseLineOption = "eheoptimized",
                   FADCBaseLineOption = "eheoptimized",
                   ATWDThresholdCharge = 0.1*I3Units.pC,
                   ATWDLEThresholdAmplitude = 1.0*I3Units.mV,
                   UseFADC = True,
                   FADCPulseSeriesName = "EHEFADCPulseSeries",
                   FADCPortiaPulseName = "EHEFADCPortiaPulse",
                   FADCWaveformName = "EHECalibratedFADC",
                   FADCThresholdCharge = 0.1*I3Units.pC,
                   FADCLEThresholdAmplitude = 1.0*I3Units.mV,
                   MakeBestPulseSeries = True,
                   BestPortiaPulseName = "EHEBestPortiaPulse",
                   PMTGain = 10000000,
                   If = If )


    # Check on the Null split
    tray.AddModule("I3FilterModule<I3EHEFilter_13>","EHEfilter",
                   TriggerEvalList=[filter_globals.inicesmttriggered],
                   DecisionName    = filter_globals.EHEFilter,
                   DiscardEvents   = False,
                   PortiaEventName = 'PoleEHESummaryPulseInfo',
                   Threshold       = pow(10,3.0),
                   If = If
                   )


    tray.AddModule("Delete", "EHE_Cleanup",
                   keys=['CleanInIceRawData_noDC', 
                         'HLCCleanInIceRawData_noDC',
                         'SLCCleanInIceRawData_noDC',
                         'EHECalibratedWaveforms',
                         'CalibrationErrata_'+name,
                         'CalibratedWaveformRange'+name,
                         'EHECalibratedATWD',
                         'EHECalibratedFADC',
                         'EHECalibratedGarbage',
                         #'splittedDOMMap',
                         'EHEATWDPulseSeries',
                         'EHEATWDPortiaPulse',
                         'EHEFADCPulseSeries',
                         'EHEFADCPortiaPulse',
                         #'EHEBestPortiaPulse'
                         ])
    
