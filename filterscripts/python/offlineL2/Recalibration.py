# recalibration
from icecube import icetray, dataclasses, tpx, DomTools
from icecube import payload_parsing, WaveCalibrator, wavedeform
from icecube.icetray import I3Units
from icecube.icetray import OMKey
from icecube.filterscripts import filter_globals

@icetray.traysegment
def InIceCalibration(tray, name, InputLaunches='CleanInIceRawData',
                     OutputPulses='ReextractedInIcePulses',
                     WavedeformSPECorrections=False):
    tray.AddModule('I3WaveCalibrator', name + '/wavecalibrator',
        Launches=InputLaunches, If=lambda fr: InputLaunches in fr)
    tray.AddModule('I3WaveformTimeRangeCalculator', name + '/sdsttimerange',
        If=lambda fr: not InputLaunches in fr)
    tray.AddModule('I3PMTSaturationFlagger', name + '/saturationflagger',
        If=lambda fr: InputLaunches in fr)
    tray.AddModule('I3Wavedeform', name + '/wavedeform',
        ApplySPECorrections = WavedeformSPECorrections,
        Output=OutputPulses)
    tray.AddModule('Delete', name+'/deletewaveforms',
        Keys=['CalibratedWaveforms'])

@icetray.traysegment
def IceTopCalibration(tray, name, InputLaunches='CleanIceTopRawData',
                      OutputPulses='ReextractedIceTopPulses'):
    tray.AddModule("I3WaveCalibrator", name+"/WaveCalibrator_IceTop",
        Launches=InputLaunches, If=lambda fr: InputLaunches in fr,
        Waveforms="IceTopCalibratedWaveforms",
        WaveformRange="", Errata="IceTopErrata")
    tray.AddModule('I3WaveformSplitter', name+'/WaveformSplitter_IceTop',
        Force=True, Input='IceTopCalibratedWaveforms',
        PickUnsaturatedATWD=True, HLC_ATWD='CalibratedIceTopATWD_HLC',
        HLC_FADC='CalibratedIceTopFADC_HLC', SLC='CalibratedIceTopATWD_SLC')
    tray.AddModule('I3TopHLCPulseExtractor', name+'/tpx_hlc',
        Waveforms='CalibratedIceTopATWD_HLC', PEPulses=OutputPulses,
        PulseInfo='IceTopHLCPulseInfo', VEMPulses='',
        MinimumLeadingEdgeTime = -100.0*I3Units.ns,
        BadDomList=filter_globals.IceTopBadDoms)
    tray.AddModule('I3TopSLCPulseExtractor', name+'/tpx_slc',
        Waveforms='CalibratedIceTopATWD_SLC', PEPulses=OutputPulses+'_SLC',
        VEMPulses='', BadDomList=filter_globals.IceTopBadDoms)
    tray.AddModule('Delete', name+'/deletewaveforms',
        Keys=['IceTopCalibratedWaveforms', 'CalibratedIceTopATWD_HLC',
        'CalibratedIceTopATWD_SLC', 'CalibratedIceTopFADC_HLC',
        'CalibratedIceTopFADC_SLC'])

@icetray.traysegment
def OfflineCalibration(tray, name, InIceOutput='InIcePulses',
                       IceTopOutput='IceTopPulses',
                       BadDOMList='BadDomsListSLC',
                       WavedeformSPECorrections=False,
                       pass2=False):
    """
    Re-do calibration and feature extraction for those launches that were
    sent in raw form, unifying the results with the pulses sent as SuperDST
    only. Also performs bad-DOM cleaning on the final output pulses.

    :param InIceOutput: Name of output pulse series with in-ice pulses
    :param IceTopOutput: Name of output pulse series with IceTop pulses
    """

    # Extract DOMLaunches and triggers from raw DAQ data
    tray.AddSegment(payload_parsing.I3DOMLaunchExtractor,
        name+'/domlaunchextractor',
        BufferID='I3DAQData',
        TriggerID='I3TriggerHierarchyTrimmed',
        SpecialDataID = "SpecialHits",
        SpecialDataOMs = [OMKey(0,1),
                          OMKey(12,65),
                          OMKey(12,66),
                          OMKey(62,65),
                          OMKey(62,66)]
    )

    # Extract DOMLaunches and triggers from SDST seatbelted raw DAQ data
#    tray.AddModule('I3FrameBufferDecode', name+'/trimmeddecode',
#        BufferID='I3DAQDataTrimmed', If=lambda fr: not 'I3DAQData' in fr)
    tray.AddSegment(payload_parsing.I3DOMLaunchExtractor,
        name+'/domlaunchextractorTrimmedDecode',
        BufferID='I3DAQDataTrimmed',
        TriggerID='I3TriggerHierarchyTrimmed',
        SpecialDataID = "SpecialHits",
        SpecialDataOMs = [OMKey(0,1),
                          OMKey(12,65),
                          OMKey(12,66),
                          OMKey(62,65),
                          OMKey(62,66)],
        If = lambda fr: not 'I3DAQData' in fr
    )


    def cleanuppointlessdaqdata(frame, data):
        if data in frame and len(frame[data]) == 0: del frame[data]
    tray.AddModule(cleanuppointlessdaqdata, name+'/pointlessInIceRawData',
        data='InIceRawData', Streams=[icetray.I3Frame.DAQ])
    tray.AddModule(cleanuppointlessdaqdata, name+'/pointlessIceTopRawData',
        data='IceTopRawData', Streams=[icetray.I3Frame.DAQ])
    if pass2:
        # PFDST files already have the extracted IceTop launches, and they
        # are apparently not included in I3DAQDataTrimmed. 
        # As a result, the code above will have renamed the iceTopRawData
        # to IceTopRawData_orig, extracted a new, empty version, and then
        # deleted the new version for being empty. So, we rename the
        # original back. 
        tray.AddModule("Rename",name+"/restore_PFDST_IceTop_launches",
            Keys=["IceTopRawData_orig","IceTopRawData"],
            If=lambda fr: not 'IceTopRawData' in fr)

    # Reextract pulses if necessary (and calibration errata for
    # reconstructions!)
    tray.AddModule('I3DOMLaunchCleaning', name + '/domlaunchcleaning',
        CleanedKeysList=BadDOMList)
    tray.AddSegment(InIceCalibration, name + '/inicecal',
        InputLaunches='CleanInIceRawData',
        OutputPulses='Reextracted' + InIceOutput,
        WavedeformSPECorrections=WavedeformSPECorrections)
    tray.AddSegment(IceTopCalibration, name + '/icetopcal',
        InputLaunches='CleanIceTopRawData',
        OutputPulses='Reextracted' + IceTopOutput)

    # Make the set of DST-only pulses for merging
    def SuperDSTOnlyPulses(frame, launches, inpulses, outpulses):
        mask = dataclasses.I3RecoPulseSeriesMapMask(frame,
            inpulses, lambda omkey, index, pulse:
            (not launches in frame or not omkey in frame[launches])
            and not omkey in frame[BadDOMList])
        if mask.any():
            frame[outpulses] = mask
    tray.AddModule(SuperDSTOnlyPulses, name + '/inicedstonlypulses',
        launches = 'InIceRawData', inpulses = 'InIceDSTPulses',
        outpulses = 'InIceDSTOnlyPulses', Streams=[icetray.I3Frame.DAQ])
    tray.AddModule(SuperDSTOnlyPulses, name + '/icetopdstonlypulses',
        launches = 'IceTopRawData', inpulses = 'IceTopDSTPulses',
        outpulses = 'IceTopDSTOnlyPulses', Streams=[icetray.I3Frame.DAQ])
    
    # Merge DST-only and offline reconstructed pulses
    def dstofflinemerge(frame, Output='', Input=[]):
        rootpulses = []
        for i in Input:
            if not i in frame:
                continue
            rootpulses.append(i)
        frame[Output] = dataclasses.I3RecoPulseSeriesMapUnion(frame,
            rootpulses)
    tray.AddModule(dstofflinemerge, name + '/dstofflineinicemerge',
        Output=InIceOutput,
        Input=['InIceDSTOnlyPulses', 'Reextracted' + InIceOutput],
        Streams=[icetray.I3Frame.DAQ])
    tray.AddModule(dstofflinemerge, name + '/dstofflineicetopmerge',
        Output=IceTopOutput,
        Input=['IceTopDSTOnlyPulses', 'Reextracted' + IceTopOutput,
         'Reextracted' + IceTopOutput + '_SLC'],
        Streams=[icetray.I3Frame.DAQ])

    # Clean up miscellaneous garbage we either added or inherited from PNF 
    tray.AddModule('Delete', name+'/cleanup',
        Keys=['I3TriggerHierarchyTrimmed', 'DrivingTime',
        'I3EventHeader_orig', 'I3DAQDataTrimmed', 'I3DAQData'])
