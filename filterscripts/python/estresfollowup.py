from icecube import icetray
import math

@icetray.traysegment
def ESTReSFollowup(tray, name, If = lambda f: True):

    # load needed libs, the "False" suppresses any "Loading..." messages
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)
    from icecube import dataclasses

    from icecube import full_event_followup
    
    import json
    
    # whitelist of keys to send via I3MS for immediate followup
    send_keys = [
        "DSTTriggers",
        "I3EventHeader",
        "QI3EventHeader",
        "I3SuperDST",
        "SplitUncleanedInIcePulses",
        "SplitUncleanedInIcePulsesTimeRange",
        # these are externally provided (HESEFollowup right now)
        "I3GeometryDiff",
        "I3CalibrationDiff",
        "I3DetectorStatusDiff"
        ] + filter_globals.estres_reco_keeps

    '''
    Not sure this will be relevant
    # send even more objects over the SPADE/SCP channel
    send_keys_low_prio = send_keys + [
        "I3DAQData",
        "UncleanedInIcePulses",
        "CalibratedWaveformRange",
        "UncleanedInIcePulsesTimeRange",
    ]
    '''
    streams = [
        icetray.I3Frame.Geometry,
        icetray.I3Frame.Calibration,
        icetray.I3Frame.DetectorStatus,
        icetray.I3Frame.DAQ,
        icetray.I3Frame.Physics,
    ]

    def followup_condition(frame):
        if filter_globals.inicesmttriggered not in frame:
            icetray.logging.log_fatal("SMT8 trigger bool expected in frame", "ESTReSFollowup")
            return False
            
        # needs to have triggered SMT8 (otherwise would not have been considered by filter)
        if not frame[filter_globals.inicesmttriggered].value:
            return False
        
        # this item has to exist if we got here, complain if it doesn't
        if filter_globals.EstresAlertFilter not in frame:
            return False
        
        if not frame[filter_globals.EstresAlertFilter].value:
            # failed the ESTReS filter
            return False
        else:
            return True        

    def create_event_id(run_id, event_id):
        return "run{0:08d}.evt{1:012d}.ESTReS".format(run_id, event_id)

    # send a small record  with only the most important information
    # for ESTReS events.  No pulses here, this is the alert summary
    def generate_small_ESTReS_followup_message(frame, Name="EstreSFollowup"):
        icetray.logging.log_notice("injecting followup message into frame for run {0}, event {1}".format(frame["I3EventHeader"].run_id,frame["I3EventHeader"].event_id), "ESTReSFollowup")

        event_unique_id = create_event_id(frame["I3EventHeader"].run_id, frame["I3EventHeader"].event_id)
        if filter_globals.estres_fit_name+"FitParams" in frame:
            splinempe_logl = frame[filter_globals.estres_fit_name+"FitParams"].logl
            splinempe_rlogl = frame[filter_globals.estres_fit_name+"FitParams"].rlogl
        else:
            splinempe_logl = math.nan
            splinempe_rlogl = math.nan
            
        message = {
            'unique_id'     : event_unique_id,
            'reco' : {
              'splinempe' : {
                'zen'       : round(frame[filter_globals.estres_fit_name].dir.zenith, 5),
                'azi'       : round(frame[filter_globals.estres_fit_name].dir.azimuth, 5),
                'fit_stat'  : int(frame[filter_globals.estres_fit_name].fit_status),
                'llh'       : round(splinempe_logl, 5),
                'rllh'      : round(splinempe_rlogl, 5),
              },
            },
            'causalqtot'    : round(frame["Estres_CausalQTot"].value, 5),
            'qtot'          : round(frame[filter_globals.estres_homogenized_qtot].value, 5),
            'p_miss'        : round(math.log10(frame["Estres_p_miss"].value),5),
            'd'             : round(frame["Estres_direct_length"].value,5),
            'eventtime'     : str(frame["I3EventHeader"].start_time.date_time),
            'event_id'      : frame["I3EventHeader"].event_id,
            'run_id'        : frame["I3EventHeader"].run_id,
        }

        frame[Name] = dataclasses.I3String(json.dumps(message))

    tray.Add(generate_small_ESTReS_followup_message, name+'_send_small_followup',
        Name=filter_globals.estres_short_followup_message, 
        If = lambda f: If(f) and followup_condition(f))

    # I3FullEventFollowupWriter cannot handle Q-frame objects shadowed
    # by P-frame objects of the same name (i.e. I3EventHeader) - 
    # make a copy and send that instead
    def unhide_QEventHeader(frame):
        frame["QI3EventHeader"] = frame["I3EventHeader"]
    tray.Add(unhide_QEventHeader, Streams=[icetray.I3Frame.DAQ])

    # send full events as high priority
    tray.Add(full_event_followup.I3FullEventFollowupWriter, name+'_send_full_followup',
        Keys = send_keys,
        WriterCallback = full_event_followup.followup_writer_callback_to_I3String(frame_object_name=filter_globals.estres_full_followup_message),
        Streams = streams,
        If = lambda f: If(f) and followup_condition(f))

    def cleaup_QEventHeader(frame):
        del frame["QI3EventHeader"]
    tray.Add(cleaup_QEventHeader, Streams=[icetray.I3Frame.DAQ])
