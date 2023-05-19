from icecube import icetray

## Import the 2.4 compatibility helpers for SPS/SPTS python
from icecube.icetray.pycompat import *

from icecube.filterscripts import filter_globals

@icetray.traysegment
def DAQTrimmer(tray, name, SuperDST='I3SuperDST',
               Pulses=filter_globals.UncleanedInIcePulses,
               Waveforms='CalibratedWaveforms', Errata='CalibrationErrata',
               Output='I3DAQDataTrimmed', ChiThreshold=1e3, 
               ChargeThreshold=1e1):
    """
    Strip launches that were well-represented out of the DAQ payload, leaving
    only SuperDST for these readouts.  Save in 'Output' the less-well
    represented raw readouts.
    """
    
    from icecube import dataclasses, payload_parsing, wavereform, DomTools
    icetray.load("filterscripts",False)

    flags = [Errata]

    # Reconstruct and test the waveforms from SuperDST pulses,
    # flagging DOMs where there was a large mismatch
    tag = "%s_%s_%s" % (name, SuperDST, Waveforms)
    flags.append(tag+"_Borked")
    tray.AddModule('I3Wavereform', name + '_wavereform',
                   Waveforms=Waveforms, Pulses=SuperDST,
                   Chi=tag+"_Chi", ChiThreshold=ChiThreshold,
                   Flag=tag+"_Borked",
                   )  

    # Flag any launches with more than one ATWD channel active
    channel_flag = name+"_MultiChannel"
    flags.append(channel_flag)
    tray.AddModule(wavereform.DOMFlagger, channel_flag,
                   Key=Waveforms, Flag=channel_flag,
                   Condition=lambda waveforms: \
                       any([wf.channel > 0 for wf in waveforms]),
                   )
    
    # Flag any DOMs with a large amount of charge in a 1-microsecond window
    qtot_flag = name+"_HighCharge"
    flags.append(qtot_flag)
    tray.AddModule(wavereform.DOMFlagger, qtot_flag,
                   Key=Pulses, Flag=qtot_flag,
                   Condition=lambda pulses: \
                       wavereform.get_max_charge(pulses, 1e3) > ChargeThreshold,
                   )

    flags.append("FlagSpecialOMKeys")
    def find_specials(frame, Output):
        if "SpecialHits" in frame:
            specials = frame["SpecialHits"]
            spec_oms = dataclasses.I3VectorOMKey()
            for omk in specials.keys():
                spec_oms.append(omk)
            frame[Output] = spec_oms
            
    tray.AddModule(find_specials, name + '_checkspecials',
                   Output = "FlagSpecialOMKeys")
            
    # Unify InIce and IceTop readouts for the DAQ trimmer
    def SmushLaunches(frame, Launches, Output):
        dlsm = dataclasses.I3DOMLaunchSeriesMap()
        for label in Launches:
            for om, launches in frame[label].items():
                dlsm[om] = launches
        frame[Output] = dlsm
                
    tray.AddModule(SmushLaunches, name + '_smushlaunches',
                   Launches=[filter_globals.CleanInIceRawData, 
                             filter_globals.CleanIceTopRawData],
                   Output=name+'_CleanRawData', Streams=[icetray.I3Frame.DAQ])

    # Split launches based on good/bad selection
    tray.AddModule('I3LaunchSelector', name + '_badlaunches',
                   Launches=name + '_CleanRawData',
                   Flags=flags, Invert=True,
                   Output='%s_TrivialLaunches' % name,
                   )

    # Encode a DAQ payload format version of badly represented launches
    # After this step, the reduced DAQ payload contains only:
    # - Header (30 bytes)
    # - 3 size tags (4 bytes each)
    # - ~ few InIce hit records (18 bytes (SLC)/ ~172 bytes (HLC) each)
    tray.AddModule('I3DAQDataTrimmer', name+'_trimgoodies',
                   TrimLaunches='%s_TrivialLaunches' % name, Output=Output,
                   RemoveTriggers=True,
                   )

    tray.AddModule('I3DAQDataTrimmer', name + '_triminice',
                   TrimLaunches = 'InIceRawData',  ## remove all InIce data
                   Output = filter_globals.icetoprawdata,
                   RemoveTriggers = True,
                   )

@icetray.traysegment
def SimTrimmer(tray, name, SuperDST='I3SuperDST',
               Pulses=filter_globals.UncleanedInIcePulses,
               Waveforms='CalibratedWaveforms', Errata='CalibrationErrata',
               ChiThreshold=1e3, ChargeThreshold=1e1):
    """
    Save a flag for events with less-well
    represented raw readouts.
    """

    from icecube import payload_parsing, wavereform, DomTools
    
    flags = [Errata]
    
    # Reconstruct and test the waveforms from SuperDST pulses,
    # flagging DOMs where there was a large mismatch
    tag = "%s_%s_%s" % (name, SuperDST, Waveforms)
    flags.append(tag+"_Borked")
    tray.AddModule('I3Wavereform', name + '_wavereform',
                   Waveforms=Waveforms, Pulses=SuperDST,
                   Chi=tag+"_Chi", ChiThreshold=ChiThreshold,
                   Flag=tag+"_Borked",
                   )

    # Flag any launches with more than one ATWD channel active
    channel_flag = name+"_MultiChannel"
    flags.append(channel_flag)
    tray.AddModule(wavereform.DOMFlagger, channel_flag,
        Key=Waveforms, Flag=channel_flag,
        Condition=lambda waveforms: \
            any([wf.channel > 0 for wf in waveforms]),
    )

    # Flag any DOMs with a large amount of charge in a 1-microsecond window
    qtot_flag = name+"_HighCharge"
    flags.append(qtot_flag)
    tray.AddModule(wavereform.DOMFlagger, qtot_flag,
        Key=Pulses, Flag=qtot_flag,
        Condition=lambda pulses: \
            wavereform.get_max_charge(pulses, 1e3) > ChargeThreshold,
    )
    
    def consolidate_flags(f):
        if any([(k in f and f[k]) for k in flags]):
            f['SimTrimmer'] = icetray.I3Bool(True)
        else:
            f['SimTrimmer'] = icetray.I3Bool(False)
    tray.AddModule(consolidate_flags,name+"_ConsolidateFlags",
                   Streams=[icetray.I3Frame.DAQ])
