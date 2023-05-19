from icecube import icetray, payload_parsing
from icecube.icetray import OMKey
from icecube.filterscripts.baseproc_daqtrimmer import DAQTrimmer
from icecube.filterscripts.baseproc_superdst import SuperDST, MaskMaker
from icecube.filterscripts.baseproc_onlinecalibration import OnlineCalibration, DOMCleaning
from icecube.filterscripts import filter_globals

@icetray.traysegment
def raw_to_sdst(tray, name):
    """PFRaw to SDST, the first part of L1"""
    tray.AddSegment(
        payload_parsing.I3DOMLaunchExtractor, "decode",
        MinBiasID = 'MinBias',
        FlasherDataID = 'Flasher',
        CPUDataID = "BeaconHits",
        SpecialDataID = "SpecialHits",
        ## location of scintillators and IceACT
        SpecialDataOMs = [OMKey(0,1),
                          OMKey(12,65),
                          OMKey(12,66),
                          OMKey(62,65),
                          OMKey(62,66)]
    )

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

    tray.AddSegment(DOMCleaning, "_DOMCleaning")

    tray.AddSegment(OnlineCalibration, 'Calibration', 
                    simulation=False, WavedeformSPECorrections=True,
                    Harvesting=filter_globals.do_harvesting)
    tray.AddSegment(SuperDST, 'SuperDST',
        InIcePulses=filter_globals.UncleanedInIcePulses, 
        IceTopPulses='IceTopPulses',
        Output = filter_globals.DSTPulses
    )

    # Set up masks for normal access
    tray.AddModule(MaskMaker, '_superdst_aliases',
                   Output=filter_globals.DSTPulses,
                   Streams=[icetray.I3Frame.DAQ]
    )

    tray.AddSegment(DAQTrimmer, 'DAQTrimmer')