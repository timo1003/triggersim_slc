import sys, os, json
from icecube import icetray, dataclasses, dataio, STTools, linefit, static_twc, fill_ratio, lilliput
from icecube.icetray import I3Units

from icecube.load_pybindings import load_pybindings
    
from icecube.dataclasses import I3Particle, I3MapStringDouble
from icecube import static_twc, STTools
from icecube.DeepCore_Filter import DOMS
from icecube.STTools.seededRT.configuration_services import I3DOMLinkSeededRTConfigurationService
from icecube import full_event_followup

from icecube.lilliput import segments
from icecube.pybdtmodule import PyBDTModule

from . import grecovariables, filter_globals

# #############################
# Filter conditions
# #############################
def TestForFilter(frame, 
                  PassedFilterNames = [filter_globals.DeepCoreFilter,],
                  FailedFilterNames = [filter_globals.SlopFilter,
                                       filter_globals.HighQFilter,
                                       filter_globals.FixedRateFilterName],):    
    if not frame['I3EventHeader'].sub_event_stream == filter_globals.InIceSplitter:
        return False
        
    if not filter_globals.deepcoresmttriggered in frame:
        return False
    if not frame[filter_globals.deepcoresmttriggered].value:
        return False

    for key in FailedFilterNames:
        if key in frame.keys():
            if frame[key].value: return False

    for key in PassedFilterNames:
        if key in frame.keys():
            return frame[key].value

    return False

# #############################
# Noise cleaning
# #############################
def nchannel_cut(frame, name,
                 pulsename = 'SRTTWSplitInIcePulsesDC', # This one uses HLCCore
                 spe_pulses = 'SRTTW_SplitInIcePulses_DC', # This one uses AllHLCHits, but a narrower time window. Legacy names
                 fillratio_name = "GRECO_FillRatio"):
    if not name + pulsename in frame.keys(): return False
    if not name + spe_pulses in frame.keys(): return False
    if not name + fillratio_name in frame.keys(): return False
    
    hitmapA = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, name + pulsename)
    hitmapB = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, name + spe_pulses)
    fillratio = frame[name + fillratio_name].fill_ratio_from_mean
    return ( (len(hitmapA.keys()) >= 8 and fillratio > 0.05) or \
             (len(hitmapA.keys()) > 11)) and (len(hitmapB) > 3)

# #############################
# Apply the cut?
# #############################
def TestForLevel3(frame, name):
    if 'IC2018_LE_L3_bools' in frame.keys():
        return frame['IC2018_LE_L3_bools']['IC2018_LE_L3_Full'] & nchannel_cut(frame, name)
    else:
        return False
    
# #############################
# The GRECO V2 selection
# #############################
@icetray.traysegment
def GRECOOnlineFilter(tray, name,
                      uncleaned_pulses = filter_globals.SplitUncleanedInIcePulses,
                      bdt = os.path.expandvars("$I3_SRC/filterscripts/resources/data/bdt_greco_online.bdt"),
                      bdt_cut = 0.13,
                      If = lambda frame: True):

    # #############################
    # Hit cleaning
    # #############################
    Pulses = uncleaned_pulses
    TWSplitInIcePulsesDC = name + 'TWSplitInIcePulsesDC'
    SRTTWSplitInIcePulsesDC = name + 'SRTTWSplitInIcePulsesDC'

    cleaned_srttw_ps = name + "SRTTW_SplitInIcePulses"
    cleaned_tw_ps = name + "TWSplitInIcePulses"

    cleaning_if = lambda frame: TestForFilter(frame) & If(frame)

    
    # Create the hit series needed for Fill-Ratio and the nchannel cuts
    tray.AddModule("I3StaticTWC<I3RecoPulseSeries>", name+"_static_twc_withsrt",
                   InputResponse  = uncleaned_pulses,
                   OutputResponse = cleaned_tw_ps,
                   TriggerName    = filter_globals.triggerhierarchy,
                   TriggerConfigIDs = [filter_globals.deepcoreconfigid,],
                   WindowMinus = 3500,
                   WindowPlus = 4000,
                   If = cleaning_if,
                   )

    # Get the pulses series from STTools
    seededRTConfigService_nodust = I3DOMLinkSeededRTConfigurationService(        
        useDustlayerCorrection  = False,
        dustlayerUpperZBoundary = 0*I3Units.m,
        dustlayerLowerZBoundary = -150*I3Units.m,
        ic_ic_RTTime           = 1000*I3Units.ns,
        ic_ic_RTRadius         = 150*I3Units.m,
    )

    tray.AddModule("I3SeededRTCleaning_RecoPulse_Module", name+"_SeededRTCleaning_DC_STTools_all",
                   AllowNoSeedHits = False,
                   InputHitSeriesMapName = cleaned_tw_ps,   
                   OutputHitSeriesMapName = cleaned_srttw_ps,
                   STConfigService = seededRTConfigService_nodust,
                   MaxNIterations = -1,
                   SeedProcedure = "AllHLCHits",
                   If = cleaning_if,
                   )
        
    DOMList = DOMS.DOMS( "IC86")
    tray.AddModule( "I3OMSelection<I3RecoPulseSeries>", name+"_uncleaned_DCCFidPulses",
                    selectInverse     = True,
                    InputResponse     = cleaned_srttw_ps,
                    OutputResponse    = cleaned_srttw_ps + "_DC",
                    OutputOMSelection = name+"BadOM_DCFid",
                    OmittedKeys       = DOMList.DeepCoreFiducialDOMs,
                    If = cleaning_if,
                    )


    # ###############################
    # Create a more loosely defined
    # TW cleaning + SRT with HLCCore
    # to be used with some of the variables
    # ###############################
    tray.AddModule('I3StaticTWC<I3RecoPulseSeries>', name + '_StaticTWC_DC',
                   InputResponse = uncleaned_pulses,
                   OutputResponse = TWSplitInIcePulsesDC,
                   TriggerConfigIDs = [filter_globals.deepcoreconfigid],                
                   TriggerName = filter_globals.triggerhierarchy,
                   WindowMinus = 5000,
                   WindowPlus = 4000,
                   If = cleaning_if
    )
    
    # Get the pulses series from STTools
    seededRTConfigService_nodust = I3DOMLinkSeededRTConfigurationService(        
        useDustlayerCorrection  = False,
        dustlayerUpperZBoundary = 0*I3Units.m,
        dustlayerLowerZBoundary = -150*I3Units.m,
        
        ic_ic_RTTime           = 1000*I3Units.ns,
        ic_ic_RTRadius         = 150*I3Units.m,
    )

    tray.AddModule("I3SeededRTCleaning_RecoPulse_Module", name+"_SeededRTCleaning_DC_STTools_core",
                   AllowNoSeedHits = False,
                   InputHitSeriesMapName = TWSplitInIcePulsesDC, # ! Name of input pulse series
                   OutputHitSeriesMapName = SRTTWSplitInIcePulsesDC,      # ! Name of output pulse series
                   STConfigService = seededRTConfigService_nodust,
                   MaxNIterations = 3,
                   SeedProcedure = "HLCCoreHits",
                   If = cleaning_if,
    )

    # #############################
    # Fill-ratio
    # #############################
    def FirstHit(frame, hitmap):
        hits = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, hitmap)
        x, y, z, t, q = grecovariables.GetHitInformation(frame['I3Geometry'], hits, 1)

        position = dataclasses.I3Position(x[0], y[0], z[0])
        direction = dataclasses.I3Direction(0, 0)
        p = dataclasses.I3Particle(position, direction, t[0])
        p.fit_status = dataclasses.I3Particle.OK
        frame[name + 'GRECO_FirstHit'] = p
        return
        
    tray.AddModule(FirstHit, name+"GRECO_FirstHit",
                   hitmap = cleaned_srttw_ps,
                   If = cleaning_if,
               )
    
    tray.AddModule("I3FillRatioModule", name+"GRECO_FillRatio_precut",
                   RecoPulseName  = cleaned_srttw_ps,
                   ResultName     = name + "GRECO_FillRatio",
                   SphericalRadiusMean = 1.6,
                   VertexName          = name + "GRECO_FirstHit",
                   If = cleaning_if,
               )

    # #############################
    # LowEn Level 3 processing
    # #############################
    tray.Add(grecovariables.DeepCoreCuts, name,
             splituncleaned=uncleaned_pulses,
             year='13', 
             If=lambda frame: nchannel_cut(frame, name,
                                           fillratio_name = 'GRECO_FillRatio'))

    # #############################
    # Basic reconstructions
    # #############################
    tray.AddSegment(linefit.simple, name+"_iLineFit",
                    inputResponse = cleaned_srttw_ps,
                    fitName       = name + "GRECO_iLineFit",
                    If = lambda frame: TestForLevel3(frame, name),
                )

    tray.AddSegment( lilliput.segments.I3IterativePandelFitter, name+"_GRECO_SPEFit11",
                     fitname   = "GRECO_SPEFit11",
                     pulses    = cleaned_srttw_ps + "_DC",
                     n_iterations = 11,
                     seeds        = ['PoleMuonLlhFit', name + 'GRECO_iLineFit'],
                     If = lambda frame: TestForLevel3(frame, name),
                 )

    # #############################
    # Variables for the BDT
    # #############################
    def GRECO_Vars(frame, 
                   hitmap=cleaned_srttw_ps,
                   hitmap_uncleaned=uncleaned_pulses,
                   hitmap_dc=cleaned_srttw_ps + "_DC"):
        # Extract information from the hit series first
        results = {}
        hits = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, hitmap)
        x, y, z, t, q = grecovariables.GetHitInformation(frame['I3Geometry'], hits, 1)

        # Formerly L4
        results['iLineFit_speed'] = frame[name + 'GRECO_iLineFit'].speed
        results['QR6'] = grecovariables.ChargeRatio(t, q, 600, 0, True)
        results['C2QR6'] = grecovariables.ChargeRatio(t, q, 600, 2, True)
        results['FirstHitZ'] = z[0] # bdt_srttw_pulses

        # Formerly L5
        results['FirstHitRho'] = ((x[0]-46.29)**2 + (y[0]+34.88)**2)**0.5        
        results['zTravel'] = grecovariables.ZTravel(z, q, False)
        results['SPEFit11_zenith'] = frame['GRECO_SPEFit11'].dir.zenith

        # Formerly L6
        results['FillRatio'] = frame[name + "GRECO_FillRatio"].fill_ratio_from_mean

        # Experimental
        results['AvgDistHits'] = grecovariables.AverageDistance(x, y, z)
        results['NR6'] = grecovariables.ChargeRatio(t, q, 600, 0, False) 
        results['C2NR6'] = grecovariables.ChargeRatio(t, q, 600, 2, False) 
        results['MeanZ'] = grecovariables.MeanZ(z, q, False)

        # Requires an uncleaned hit series extracted pulse-by-pulse
        hits = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, hitmap_uncleaned)
        x, y, z, t, q = grecovariables.GetHitInformation(frame['I3Geometry'], hits, 0)
        results['VetoCausalCharge'] = grecovariables.VetoCausalHits(x, y, z, t, q, 
                                                                    frame[filter_globals.triggerhierarchy], 
                                                                    [filter_globals.deepcoreconfigid], True)
        results['VetoCausalHits'] = grecovariables.VetoCausalHits(x, y, z, t, q, 
                                                                  frame[filter_globals.triggerhierarchy], 
                                                                  [filter_globals.deepcoreconfigid], False)

        # Extract the uncleaned hit series module-by-module
        hits = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, hitmap_uncleaned)
        x, y, z, t, q = grecovariables.GetHitInformation(frame['I3Geometry'], hits, 1)
        results['QAbove200'] = grecovariables.NAboveTrigger(z, t, q, 
                                                            frame[filter_globals.triggerhierarchy], 
                                                            [filter_globals.deepcoreconfigid,],
                                                            -2000, 0, 
                                                            -200, True)
        results['NAbove200'] = grecovariables.NAboveTrigger(z, t, q, 
                                                            frame[filter_globals.triggerhierarchy], 
                                                            [filter_globals.deepcoreconfigid,],
                                                            -2000, 0, 
                                                            -200, False)

        # These use a different cleaned hit series
        hits = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, hitmap_dc)
        x, y, z, t, q = grecovariables.GetHitInformation(frame['I3Geometry'], hits, 1)
        results['nchannel'] = len(x)

        # Put it into the frame.
        frame['GRECO_Variables'] = dataclasses.I3MapStringDouble(results)
        return

    tray.Add(GRECO_Vars, name+"_RunGRECOVariables",
             hitmap_dc = SRTTWSplitInIcePulsesDC,
             hitmap_uncleaned = uncleaned_pulses,
             Streams = [icetray.I3Frame.Physics],
             If = lambda frame: TestForLevel3(frame, name))

    # #############################
    # Run the BDT and store the score
    # #############################
    tray.Add(PyBDTModule, name+"_pybdt",
             BDTFilename = bdt,
             varsfunc = lambda frame: frame['GRECO_Variables'],
             OutputName = 'GRECO_bdt_2019',
             If = lambda frame: TestForLevel3(frame, name),
             )

    def greco_decision(frame,
                       scorename = 'GRECO_bdt_2019',
                       signal_cut = bdt_cut):
        if not frame.Has(scorename):
            frame['PassGrecoOnline'] = icetray.I3Bool(False)
            return
        else:
            score = frame[scorename].value 
            frame['PassGrecoOnline'] = icetray.I3Bool(score >= signal_cut)
            #if score >= signal_cut: print 'found GRECO online...'
    tray.Add(greco_decision,name+'_checkgreco')    

    # actual filter decision
    tray.AddModule("I3FilterModule<I3BoolFilter>", name+"_GRECOOnlineFilter2019",
            DiscardEvents = False,
            Boolkey       = 'PassGrecoOnline',
            DecisionName  = filter_globals.GRECO_OnlineFilter,
            If = lambda f: If(f)
        )



    # #############################
    # Set up the messaging for online
    # Based heavily off of the code from ESTReS
    # #############################
    # whitelist of keys to send via I3MS for immediate followup
    send_keys = ["DSTTriggers",
                 "I3EventHeader",
                 "QI3EventHeader",
                 "I3SuperDST",
                 "SplitUncleanedInIcePulses",
                 "SplitUncleanedInIcePulsesTimeRange",
                 "GRECO_SPEFit11",
                 filter_globals.GRECO_OnlineFilter,

                 # these are externally provided (HESEFollowup right now)
                 #"I3GeometryDiff",
                 #"I3CalibrationDiff",
                 #"I3DetectorStatusDiff"
             ] + filter_globals.greco_reco_keeps

    streams = [icetray.I3Frame.Geometry,
               icetray.I3Frame.Calibration,
               icetray.I3Frame.DetectorStatus,
               icetray.I3Frame.DAQ,
               icetray.I3Frame.Physics,
           ]


    def followup_condition(frame):
        if filter_globals.deepcoresmttriggered not in frame:
            icetray.logging.log_fatal("SMT3 trigger bool expected in frame", "GRECO_Online")
            return False            
        if not frame[filter_globals.deepcoresmttriggered].value: return False
        if filter_globals.GRECO_OnlineFilter not in frame: return False
        return frame[filter_globals.GRECO_OnlineFilter].value


    def create_event_id(run_id, event_id):
        return "run{0:08d}.evt{1:012d}.GRECO_Online".format(run_id, event_id)

    # send a small record  with only the most important information
    # for GRECO Online events.  No pulses here, this is the alert summary
    def generate_small_GRECO_followup_message(frame, Name="GRECO_Online_Followup"):
        icetray.logging.log_notice("injecting followup message into frame for run {0}, event {1}".format(frame["I3EventHeader"].run_id,frame["I3EventHeader"].event_id), "GRECO_Online")

        event_unique_id = create_event_id(frame["I3EventHeader"].run_id, frame["I3EventHeader"].event_id)
        message = {
            'unique_id'     : event_unique_id,
            'bdt_score'     : round(frame['GRECO_bdt_2019'].value, 5),
            'eventtime'     : str(frame["I3EventHeader"].start_time.date_time),
            'event_id'      : frame["I3EventHeader"].event_id,
            'run_id'        : frame["I3EventHeader"].run_id,
        }

        frame[Name] = dataclasses.I3String(json.dumps(message))

    tray.Add(generate_small_GRECO_followup_message, name+'_send_small_followup',
        Name=filter_globals.greco_short_followup_message, 
        If = lambda f: If(f) and followup_condition(f))

    # add a dummy list of "alerts" to help I3Live indexing, like std alerts
    def add_greco_list(frame, listname='GRECONames'):
        alertsPassed = []
        alertsPassed.append('GRECO')
        frame[listname] = dataclasses.I3VectorString(alertsPassed)
    tray.Add(add_greco_list, name + '_alertlister',
             listname = filter_globals.greco_candidate_list,
             If = lambda f: If(f) and followup_condition(f))


    # I3FullEventFollowupWriter cannot handle Q-frame objects shadowed
    # by P-frame objects of the same name (i.e. I3EventHeader) - 
    # make a copy and send that instead
    def unhide_QEventHeader(frame):
        frame["QI3EventHeader"] = frame["I3EventHeader"]
    tray.Add(unhide_QEventHeader, Streams=[icetray.I3Frame.DAQ])

    # send full events 
    tray.Add(full_event_followup.I3FullEventFollowupWriter, name+'_send_full_followup',
        Keys = send_keys,
        WriterCallback = full_event_followup.followup_writer_callback_to_I3String(frame_object_name=filter_globals.greco_full_followup_message,
          short_message_name=filter_globals.greco_short_followup_message),
        Streams = streams,
        If = lambda f: If(f) and followup_condition(f))

    def cleaup_QEventHeader(frame):
        del frame["QI3EventHeader"]
    tray.Add(cleaup_QEventHeader, Streams=[icetray.I3Frame.DAQ])


    # #############################
    # Be friendly and clean up the frame
    # #############################
    tray.AddModule("Delete", name+"_GRECO_cleanup",
                   Keys = ["TWSplitInIcePulses", 
                           "SRTTW_SplitInIcePulses", 
                           "SRTTW_SplitInIcePulses_DC", 
                           "GRECO_iLineFit", 
                           "GRECO_SPEFit11", 

                           'BadOM_DCFid', 
                           'GRECO_FillRatio', 
                           'GRECO_FirstHit', 
                           'GRECO_SPEFit11FitParams', 
                           'GRECO_iLineFitParams', 
                           'SRTTW_SplitInIcePulses_DCCleanedKeys', 

                           'SRTTWOfflinePulsesDC',
                           'SRTTWOfflinePulsesDCTimeRange',
                           'SRTTWSplitInIcePulsesDC',
                           'SRTTWSplitInIcePulsesDCHitStatistics',
                           'TWSplitInIcePulsesTimeRange', 

                           name + 'TWSplitInIcePulsesDC',
                           name + 'SRTTWSplitInIcePulsesDC',

                           name + "SRTTW_SplitInIcePulses",
                           name + "TWSplitInIcePulses",

                           "BadOMSelection",
                           "NoiseEngine_bool",
                           "SplitInIcePulses_STW_ClassicRT_grecoNoiseEngine",
                           "SplitInIcePulses_STW_grecoNoiseEngine",
                           "SplitInIcePulses_STW_grecoNoiseEngineTimeRange",
                           "grecoBadOM_DCFgrecoGRECO_SPEFit11",
                           "grecoGRECO_iLineFit",
                           "grecoGRECO_iLineFitParams",
                           "grecoIC2018_LE_L3_Vars",
                           "grecoNChAbove200",
                           "grecoNoiseEngineNoCharge_bool",
                           "grecoSRTTW_SplitInIcePulses_DC",
                           "grecoSRTTW_SplitInIcePulses_DCCleanedKeys",
                           "grecoSplitInIcePulsesHitStatistics",
                           "grecoTWRTVetoSeries",
                           "grecoTWSplitInIcePulsesDCTimeRang",
                           "grecoTWSplitInIcePulsesTimeRange",
                           "grecogrecoSRTTWSplitInIcePulsesDCHitStatistics",
                           "grecoGRECO_FillRatio",
                           "grecoGRECO_FirstHit",
                           ]
                   )

    return

