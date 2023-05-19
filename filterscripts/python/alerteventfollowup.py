from icecube import icetray
import math

#
# A single place to generate alert candidate messages for I3MS transmission.
#
#  Currently:  EHE, HESE, GFU-neutrino, ESTrES
#

@icetray.traysegment
def CompressGCD(tray,name, base_GCD_path, base_GCD_filename):
    """
    Use frame_object_diff to generate compressed versions of the GCD objects.
    """
    # If we add more filters that use this functionality we might need to move
    # this out of here to a higher level.
    
    from icecube.frame_object_diff.segments import compress
    
    tray.Add(compress, name+"_GCD_diff",
             inline_compression=False, # keep the original objects
             base_path=base_GCD_path,
             base_filename=base_GCD_filename)


@icetray.traysegment
def AlertEventFollowup(tray,name,
                       omit_GCD_diff=False,
                       base_GCD_path=None,
                       base_GCD_filename=None,
                       If = lambda f: True):

    if not omit_GCD_diff:
        if base_GCD_path is None:
            raise ValueError("need to set the base_GCD_path parameter")
        if base_GCD_filename is None:
            raise ValueError("need to set the base_GCD_filename parameter")

    # load needed libs, the "False" suppresses any "Loading..." messages
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)
    from icecube import dataclasses, phys_services
    from icecube import full_event_followup
    from icecube.common_variables import track_characteristics
    from icecube import gulliver, paraboloid
    
    import json
    import numpy as np
    
    if not omit_GCD_diff:
        # compress the GCD data. This generates
        # "Diff" objects (I3GeometryDiff, ...)
        tray.Add(CompressGCD, name+"_compress",
                 base_GCD_path=base_GCD_path,
                 base_GCD_filename=base_GCD_filename)

    ## Add a list of alert filters that passed
    def alerts_passed_lister(frame, ListName='AlertNamesPassed'):
        alertsPassed = []
        if filter_globals.HESEFilter in frame:
            if frame[filter_globals.HESEFilter].value:
                alertsPassed.append("HESE")
        if filter_globals.EstresAlertFilter in frame:
            if frame[filter_globals.EstresAlertFilter].value:
                alertsPassed.append("ESTRES")
        if filter_globals.EHEAlertFilter in frame:
            if frame[filter_globals.EHEAlertFilter].value:
                alertsPassed.append("EHE")
        if filter_globals.GFUFilter in frame:
            if frame[filter_globals.GFUFilter].value:
                alertsPassed.append("neutrino")
        frame[ListName] = dataclasses.I3VectorString(alertsPassed)

    tray.Add(alerts_passed_lister, name + '_alertlist',
             ListName = filter_globals.alert_candidate_list)
    
    def send_full_followup_check(frame, List = 'Candidates'):
        if List not in frame:
            return False
        myalerts = frame[List]
        sends_full = ['HESE','ESTRES','EHE']
        if any(analert in myalerts for analert in sends_full):
            return True
        elif 'neutrino' in myalerts:
            # Send GCD diff interesting "neutrino" candidates
            up_cut = 4.8
            #up_cut = 3.0   # Testing value
            down_coeff = [  -2.23928,  -7.34434,  -7.94114,   3.12003 ]
            if all(var in frame for var in [ 'OnlineL2_SplineMPE',
                                             'OnlineL2_SplineMPE_TruncatedEnergy_AllDOMS_Muon',
                                             'OnlineL2_HitStatisticsValuesIC' ]):
                sinDec  = math.sin(frame['OnlineL2_SplineMPE'].dir.zenith - math.pi/2.)
                logE    = math.log10(frame['OnlineL2_SplineMPE_TruncatedEnergy_AllDOMS_Muon'].energy)
                logQtot = math.log10(frame['OnlineL2_HitStatisticsValuesIC'].q_tot_pulses)
                return ( (sinDec >= math.radians(-8.)) and (logE    >= up_cut) ) \
                     | ( (sinDec <  math.radians(-8.)) and (logQtot >= np.polyval(down_coeff, sinDec)))
            return False
        else:
            return False
    

    # whitelist of keys to send via I3MS for immediate followup
    send_keys = [
        "DSTTriggers",
        "I3EventHeader",
        "QI3EventHeader",
        "I3SuperDST",
        "InIceDSTPulses",
        "SplitUncleanedInIcePulses",
        "SplitUncleanedInIcePulsesTimeRange",
        "CalibrationErrata",
        "SaturationWindows",
        "OnlineL2_SplineMPE",
        "OnlineL2_BestFit",
        "PoleEHESummaryPulseInfo",
        "PoleEHEOpheliaParticle_ImpLF",
        "OnlineL2_BestFit_CramerRao_cr_zenith",
        "OnlineL2_BestFit_CramerRao_cr_azimuth",
        "OnlineL2_SplineMPEFitParams",
        "OnlineL2_SplineMPE_Characteristics",
        "OnlineL2_SplineMPE_Bootstrap_Angular",
        "OnlineL2_SplineMPE_ParaboloidFitParams",
        filter_globals.alert_candidate_short_message,
        ] + filter_globals.hese_reco_keeps + filter_globals.estres_reco_keeps

    gcd_send_keys = [
        "I3GeometryDiff",
        "I3CalibrationDiff",
        "I3DetectorStatusDiff",
        ]
    streams = [
        icetray.I3Frame.Geometry,
        icetray.I3Frame.Calibration,
        icetray.I3Frame.DetectorStatus,
        icetray.I3Frame.DAQ,
        icetray.I3Frame.Physics,
    ]

    def followup_condition(frame):
        # this item has to exist if we got here, complain if it doesn't
        if filter_globals.alert_candidate_list not in frame:
            icetray.logging.log_fatal("AlertFollowup needs to run after alerts listed", "AlertFollowup")
            return False

        ##if list is not empty, we've got alerts
        if frame[filter_globals.alert_candidate_list]:
            return True
        else:
            return False

        
    def get_dir_track_length_safe(frame, trackname):
        if trackname in frame:
            return round(frame[trackname].dir_track_length,5)
        else:
            return None


    def get_track_length_in_detector_safe(frame, trackname):
        if trackname not in frame:
            return None
        surf = phys_services.Cylinder(1000., 500.)
        intersect = surf.intersection(frame[trackname].pos, frame[trackname].dir)
        if np.isfinite(intersect.first) and np.isfinite(intersect.second):
            return max(intersect.second, 0.) - max(intersect.first, 0.)
        else:
            return 0.


    # send a small record  with only the most important information
    # for all alert candidate events.  No pulses here, this is the alert summary
    def generate_small_followup_message(frame, MsgName="AlertEventFollowup"):
        icetray.logging.log_notice("injecting followup message into frame for run {0}, event {1}".format(frame["I3EventHeader"].run_id,frame["I3EventHeader"].event_id), "AlertEventFollowup")

        alerts = frame[filter_globals.alert_candidate_list]
        # precalcs
        event_unique_id = full_event_followup.create_event_id(frame["I3EventHeader"].run_id, frame["I3EventHeader"].event_id)

        if "OnlineL2_SplineMPE_Characteristics" in frame:
            trk_smth = round(frame["OnlineL2_SplineMPE_Characteristics"].track_hits_distribution_smoothness,5)
        else:
            trk_smth = None

        if "OnlineL2_SplineMPEFitParams" in frame:
            splinempe_logl = round(frame["OnlineL2_SplineMPEFitParams"].logl,5)
            splinempe_rlogl = round(frame["OnlineL2_SplineMPEFitParams"].rlogl,5)
        else:
            splinempe_logl = None
            splinempe_rlogl = None
            
        if 'OnlineL2_BestFit_MuEx' in frame:
            mpe_muex = frame["OnlineL2_BestFit_MuEx"].energy
        else:
            mpe_muex = None
        if filter_globals.estres_fit_name+"FitParams" in frame:
            splineestres_logl = round(frame[filter_globals.estres_fit_name+"FitParams"].logl,5)
            splineestres_rlogl = round(frame[filter_globals.estres_fit_name+"FitParams"].rlogl,5)
        else:
            splineestres_logl = None
            splineestres_rlogl = None
        if 'OnlineL2_HitMultiplicityValuesIC' in frame:
            l2_nch = frame['OnlineL2_HitMultiplicityValuesIC'].n_hit_doms
            l2_npulses = frame['OnlineL2_HitMultiplicityValuesIC'].n_pulses
        else:
            l2_nch = None
            l2_npulses = None
        if 'OnlineL2_HitStatisticsValuesIC' in frame:
            l2_qtot = round(frame['OnlineL2_HitStatisticsValuesIC'].q_tot_pulses, 5)
        else:
            l2_qtot = None


        ## Interrogate the QTriggerHierarchy to see if there's an IceTop trigger
        ice_top_triggered = False
        if filter_globals.qtriggerhierarchy in frame:
            qtrigs = frame[filter_globals.qtriggerhierarchy]
            for trig in qtrigs:
                if (trig.key.source == dataclasses.SourceID.ICE_TOP and \
                    trig.key.type == dataclasses.TypeID.SIMPLE_MULTIPLICITY):
                    ice_top_triggered = True
        # error estimators don't always run, so be careful...
        bootstrap_name  = 'OnlineL2_SplineMPE_Bootstrap_Angular'
        paraboloid_name = 'OnlineL2_SplineMPE_ParaboloidFitParams'

        pb_ok = frame.Has(paraboloid_name) and \
                (frame[paraboloid_name].pbfStatus == paraboloid.I3ParaboloidFitParams.PBF_SUCCESS)
        pb_err1 = round(frame[paraboloid_name].pbfErr1,5) if pb_ok else None
        pb_err2 = round(frame[paraboloid_name].pbfErr2,5) if pb_ok else None
        bs_est  = frame[bootstrap_name].value if frame.Has(bootstrap_name) else None
        # BDT scores depend on the zenith
        bdt_up   = round(frame['GammaFollowUp_BDT_Score_Up'].value,5)   if frame.Has('GammaFollowUp_BDT_Score_Up')   else None
        bdt_down = round(frame['GammaFollowUp_BDT_Score_Down'].value,5) if frame.Has('GammaFollowUp_BDT_Score_Down') else None
        truncatedEnergyName = 'OnlineL2_SplineMPE_TruncatedEnergy_AllDOMS_Muon'
        truncatedEnergy = round(frame[truncatedEnergyName].energy,5) if frame.Has(truncatedEnergyName) else None

        reco_message = {}
        if any(x in alerts for x in ['EHE','HESE','neutrino']):   ## these use onlineL2, providing SplineMPE
               reco_message["splinempe"] = {
                   'zen'       : round(frame["OnlineL2_SplineMPE"].dir.zenith, 5),
                   'azi'       : round(frame["OnlineL2_SplineMPE"].dir.azimuth, 5),
                   'fit_stat'  : int(frame["OnlineL2_SplineMPE"].fit_status),
                   'llh'       : splinempe_logl,
                   'rllh'      : splinempe_rlogl,
                   'dir_hits_a': get_dir_track_length_safe(frame, "OnlineL2_SplineMPE_DirectHitsA"),
                   'dir_hits_b': get_dir_track_length_safe(frame, "OnlineL2_SplineMPE_DirectHitsB"),
                   'dir_hits_c': get_dir_track_length_safe(frame, "OnlineL2_SplineMPE_DirectHitsC"),
                   'dir_hits_d': get_dir_track_length_safe(frame, "OnlineL2_SplineMPE_DirectHitsD"),
                   'dir_hits_e': get_dir_track_length_safe(frame, "OnlineL2_SplineMPE_DirectHitsE"),
                   'track_len':  get_track_length_in_detector_safe(frame, "OnlineL2_SplineMPE"),
                   'trk_smth'  : trk_smth,
                   'cr_zen'    : round(frame['OnlineL2_SplineMPE_CramerRao_cr_zenith'].value, 5),
                   'cr_azi'    : round(frame['OnlineL2_SplineMPE_CramerRao_cr_azimuth'].value, 5),
                   'pb_err1'   : pb_err1,
                   'pb_err2'   : pb_err2,
                   'bs_est'    : bs_est,
                   'it_slc_cnt': frame[filter_globals.IceTop_SLC_InTime].value,
                   'it_hlc_cnt': frame[filter_globals.IceTop_HLC_InTime].value,
               }
               reco_message["spefit2"] = {
                   'zen'       : round(frame["OnlineL2_SPE2itFit"].dir.zenith, 5),
                   'azi'       : round(frame["OnlineL2_SPE2itFit"].dir.azimuth, 5),
                   'fit_stat'  : int(frame["OnlineL2_SPE2itFit"].fit_status),
                   'ndof'      : frame['OnlineL2_SPE2itFitFitParams'].ndof,
                   'llh'       : round(frame['OnlineL2_SPE2itFitFitParams'].logl, 5),
                   'rllh'      : round(frame['OnlineL2_SPE2itFitFitParams'].rlogl, 5),
               }
               reco_message["onlineL2_bestfit"] = {
                   'zen'       : round(frame['OnlineL2_BestFit'].dir.zenith, 5),
                   'azi'       : round(frame['OnlineL2_BestFit'].dir.azimuth, 5),
                   'name'      : frame['OnlineL2_BestFit_Name'].value,
                   'cr_zen'    : round(frame['OnlineL2_BestFit_CramerRao_cr_zenith'].value, 5),
                   'cr_azi'    : round(frame['OnlineL2_BestFit_CramerRao_cr_azimuth'].value, 5),
               }
               reco_message["energy"] = {
                   'mpe_muex'      : round(mpe_muex, 5),
                   'spline_mue'    : round(frame['OnlineL2_SplineMPE_MuE'].energy, 5),
                   'spline_muex'   : round(frame['OnlineL2_SplineMPE_MuEx'].energy, 5),
                   'truncated'     : truncatedEnergy,
               }
                   
        if 'HESE' in alerts:
               reco_message['cscd_llh'] = {
                   'zen'       : round(frame["HESE_CascadeLlhVertexFit"].dir.zenith, 5),
                   'azi'       : round(frame["HESE_CascadeLlhVertexFit"].dir.azimuth, 5),
                   'fit_stat'  : int(frame["HESE_CascadeLlhVertexFit"].fit_status),
                   'llh'       : round(frame['HESE_CascadeLlhVertexFitParams'].NegLlh, 5),
                   'rllh'      : round(frame['HESE_CascadeLlhVertexFitParams'].ReducedLlh, 5),
               }
        if 'EHE' in alerts:
               reco_message['imp_linefit'] = {
                   'zen'       : round(frame['PoleEHEOpheliaParticle_ImpLF'].dir.zenith, 5),
                   'azi'       : round(frame['PoleEHEOpheliaParticle_ImpLF'].dir.azimuth, 5),
                   'fit_stat'  : int(frame['PoleEHEOpheliaParticle_ImpLF'].fit_status),
                   }
        if 'ESTRES' in alerts:
               reco_message['estres_splinempe'] = {
                   'zen'       : round(frame[filter_globals.estres_fit_name].dir.zenith, 5),
                   'azi'       : round(frame[filter_globals.estres_fit_name].dir.azimuth, 5),
                   'fit_stat'  : int(frame[filter_globals.estres_fit_name].fit_status),
                   'llh'       : splineestres_logl,
                   'rllh'      : splineestres_rlogl,
                   }

        ## generate message
        message = {
            'unique_id'     : event_unique_id,
            'eventtime'     : str(frame["I3EventHeader"].start_time.date_time),
            'event_id'      : frame["I3EventHeader"].event_id,
            'run_id'        : frame["I3EventHeader"].run_id,
            'nch'           : l2_nch,
            'npulses'       : l2_npulses,
            'qtot'          : l2_qtot,
            'it_trig'       : ice_top_triggered}
        message['reco'] = reco_message
        ## Add selection specific dicts
        if "HESE" in alerts:
            message['hese'] = {
                'causalqtot'    : round(frame["HESE_CausalQTot"].value, 5),
                'qtot'          : round(frame["HESE_HomogenizedQTot"].value, 5),
                ## OLD llh ratio:  cscd llh to spefit2
                'llh_ratio'     : round(frame["HESE_llhratio"].value, 5),
            }

        if "EHE" in alerts:
            message['ehe'] = {
                'portia_npe' : round(frame['PoleEHESummaryPulseInfo'].GetTotalBestNPEbtw(), 5),
            }

        if "neutrino" in alerts:
            message['neutrino'] = {
                'bdt_up':    bdt_up,
                'bdt_down':  bdt_down,
            }

        if "ESTRES" in alerts:
            message['estres'] = {
                'causalqtot'    : round(frame["Estres_CausalQTot"].value, 5),
                'qtot'          : round(frame[filter_globals.estres_homogenized_qtot].value, 5),
                'p_miss'        : round(math.log10(frame["Estres_p_miss"].value),5),
                'dir_length'    : round(frame["Estres_direct_length"].value,5),
            }

        frame[MsgName] = dataclasses.I3String(json.dumps(message))

    # send small message is qtot>1500
    tray.Add(generate_small_followup_message, name+'_small_followup',
        MsgName=filter_globals.alert_candidate_short_message,
        If = lambda f: If(f) and followup_condition(f))

    # I3FullEventFollowupWriter cannot handle Q-frame objects shadowed
    # by P-frame objects of the same name (i.e. I3EventHeader) - 
    # make a copy and send that instead
    def unhide_QEventHeader(frame):
        frame["QI3EventHeader"] = frame["I3EventHeader"]
    tray.Add(unhide_QEventHeader, Streams=[icetray.I3Frame.DAQ])

    tray.Add(full_event_followup.I3FullEventFollowupWriter, name+'_send_full_followup',
             Keys = send_keys + gcd_send_keys,
             WriterCallback = full_event_followup.followup_writer_callback_to_I3String(frame_object_name=filter_globals.alert_candidate_full_message,
                 short_message_name=filter_globals.alert_candidate_short_message),
             Streams = streams,
             If = lambda f: If(f) and followup_condition(f) and send_full_followup_check(f,List=filter_globals.alert_candidate_list)
    )

    tray.Add(full_event_followup.I3FullEventFollowupWriter, name+'_send_frame_followup',
             Keys = send_keys,
             WriterCallback = full_event_followup.followup_writer_callback_to_I3String(frame_object_name=filter_globals.alert_candidate_full_message,
                 short_message_name=filter_globals.alert_candidate_short_message),
             Streams = streams,
             If = lambda f: If(f) and followup_condition(f) and (not send_full_followup_check(f,List=filter_globals.alert_candidate_list))
    )
             
    def cleaup_QEventHeader(frame):
        del frame["QI3EventHeader"]
    tray.Add(cleaup_QEventHeader, Streams=[icetray.I3Frame.DAQ])
