import string

from icecube import icetray

# Enhanced Starting Track Realtime Stream (ESTReS) Traysegment 

@icetray.traysegment
def ESTReSFilter(tray, name, 
                 pulsesname = 'RecoPulses',
                 veto_thresh = 0.001,
                 distance_thresh = 400, 
                 homogonized_charge_cut = 450, 
                 zenith_angle_cut = 75, 
                 vertex_charge_cut = 25,
                 base_processing_fit = 'PoleMuonLlhFit',
                 SplineRecoAmplitudeTable=None,
                 SplineRecoTimingTable=None,
                 If = lambda f: True):
    '''
    Traysegment for the Enhanced Starting Track Realtime Stream (ESTReS)
    Default settings are the recommended settings in Table 1 of the TFT proposal
    http://icecube.wisc.edu/~kjero/ESTReS_TFT_Proposal/ESTES_Realtime_Filter_Proposal.pdf
    For a rate around 60 events a day use
    veto_tresh = 10**-5
    distance_tresh = 300.
    homogonized_charge_cut = 250.
    vertex_charge_cut = 25.
    zenith_angle_cut = 180.
    '''

    import sys
    import math
    import os.path
    from icecube.filterscripts import filter_globals

    from icecube import icetray,dataclasses,phys_services
    from icecube import spline_reco,photonics_service,gulliver,gulliver_modules
    from icecube import StartingTrackVeto,VHESelfVeto

    if SplineRecoAmplitudeTable is None or SplineRecoTimingTable is None:
        raise Exception('SplineRecoAmplitudeTable or SplineRecoTimingTable is None')

    # share the spline with SplineMPE and StartingTrackVeto
    PreJitter = 4
    if sys.version_info >= (3, 0):        
        inf_muon_service_name = "BareMuSplineJitter" + str(PreJitter) + SplineRecoAmplitudeTable.translate(str.maketrans("","", string.punctuation)) + SplineRecoTimingTable.translate(str.maketrans("","", string.punctuation))
    else:
        inf_muon_service_name = "BareMuSplineJitter" + str(PreJitter) + SplineRecoAmplitudeTable.translate(string.maketrans("",""), string.punctuation) + SplineRecoTimingTable.translate(string.maketrans("",""), string.punctuation)
        
    existing_services = tray.context.keys()
    if inf_muon_service_name in existing_services:
        inf_muon_service = tray.context[inf_muon_service_name]
    else:
        inf_muon_service = photonics_service.I3PhotoSplineService(
                       amplitudetable = SplineRecoAmplitudeTable,  ## Amplitude tables
                       timingtable = SplineRecoTimingTable,    ## Timing tables
                      timingSigma = PreJitter,   ## Smearing
                       )
        tray.context[inf_muon_service_name] = inf_muon_service

    TriggerEvalList = [filter_globals.inicesmttriggered] # work on SMT8 triggers
    def If_with_triggers(frame):
        if not If(frame):
            return False
        for trigger in TriggerEvalList:
            if frame[trigger].value:
                return True
        return False  
  
    tray.AddModule('HomogenizedQTot', name+'_qtot_total',
        Pulses=pulsesname,
        Output=filter_globals.estres_homogenized_qtot,
        If = If_with_triggers)

    def estres_passes_qtot(frame):
        if filter_globals.estres_homogenized_qtot in frame:
            return frame[filter_globals.estres_homogenized_qtot].value > homogonized_charge_cut
        else:
            return False
    '''
    StartingTrackVeto now takes the empty string ('') as an option for baddoms. In this
    mode it does not know of any bad doms, which is a problem but at least it runs for now.
    def shim_bad_doms(frame):
        frame['Estres_BadDoms'] = dataclasses.I3VectorOMKey()
        frame['Estres_BadDomsSLC'] = dataclasses.I3VectorOMKey()
    tray.AddModule(shim_bad_doms,name + '_shim_estres',
                   Streams = [icetray.I3Frame.DetectorStatus])
    '''    
    
    tray.AddModule('I3LCPulseCleaning',  name+'_cleaning', 
                   OutputHLC='Estres_HLCPulses',
                   OutputSLC='', 
                   Input=pulsesname, 
                   If=lambda f: If_with_triggers(f) and estres_passes_qtot(f))
    tray.AddModule('VHESelfVeto',  name+'_selfveto', 
                   TimeWindow=1500, 
                   VertexThreshold=vertex_charge_cut,
                   VetoThreshold=3, 
                   Pulses='Estres_HLCPulses',
                   OutputBool='Estres_VHESelfVeto',
                   OutputVertexTime='Estres_VHESelfVetoVertexTime',
                   OutputVertexPos='Estres_VHESelfVetoVertexPos',
                   If=lambda f: If_with_triggers(f) and estres_passes_qtot(f))
    tray.AddModule('HomogenizedQTot',  name+'_qtot_causal', 
                   Pulses=pulsesname,
                   Output='Estres_CausalQTot', 
                   VertexTime='Estres_VHESelfVetoVertexTime',
                   If=lambda f: If_with_triggers(f) and estres_passes_qtot(f))

    def estres_check_veto(frame):
        if estres_passes_qtot(frame):
            if 'Estres_CausalQTot' in frame:
                if 'Estres_VHESelfVeto' in frame:
                    if not frame['Estres_VHESelfVeto']:
                        return frame['Estres_CausalQTot'].value > homogonized_charge_cut
        return False

    tray.AddSegment(spline_reco.SplineMPE, name+'SplineMPEdefault',
                    configuration='default', PulsesName=pulsesname,
                    TrackSeedList=[base_processing_fit], BareMuTimingSpline=SplineRecoTimingTable,
                    BareMuAmplitudeSpline=SplineRecoAmplitudeTable,
                    fitname=filter_globals.estres_fit_name,
                    If = lambda f: If_with_triggers(f) and estres_check_veto(f))


    def check_estres_fit(frame):
        if estres_check_veto(frame):
            if filter_globals.estres_fit_name in frame:
                if frame[filter_globals.estres_fit_name].fit_status == 0:  # fit reported success
                    if frame[filter_globals.estres_fit_name].dir.zenith<math.radians(zenith_angle_cut):
                        return True
        return False


    def sign( value ):
        if value < 0:
            return -1
        else:
            return 1

    def make_segment(frame,fit):
        '''
        For veto calculations with segmented spline tables one needs to specify the segments of interest.
        '''
        basep=frame[fit]
        #Shift position to closest approach position to 0,0,0. Adjust time appropriately.
        origin_cap=phys_services.I3Calculator.closest_approach_position(basep,dataclasses.I3Position(0,0,0))
        basep_shift_d=sign(origin_cap.z - basep.pos.z) *\
                      sign(basep.dir.z) *\
                      (origin_cap-basep.pos).magnitude
        basep_shift_t=basep_shift_d/basep.speed
        basep.pos=origin_cap#basep_shift_pos
        basep.time=basep.time+basep_shift_t
        basep.energy=0.01#Set arbirarily
        basep.shape=basep.shape.InfiniteTrack
        basep.length=0
        segments=[basep]
        frame[fit+'_segments']=dataclasses.I3VectorI3Particle(segments)

    tray.AddModule(make_segment,name+'_make_segment',
                   fit=filter_globals.estres_fit_name,
                   If = lambda f: If_with_triggers(f) and check_estres_fit(f))

    def make_pseudobadDOMsList(frame):
        g = frame['I3Geometry'] 
        d = frame['I3DetectorStatus']
        badDOMs = set(g.omgeo.keys()) - set(d.dom_status.keys())
        frame['StartingTrackVeto_pseudobadDOMsList']=dataclasses.I3VectorOMKey(badDOMs)
        frame['StartingTrackVeto_pseudobadDOMsListSLC']=dataclasses.I3VectorOMKey(set())

    tray.AddModule(make_pseudobadDOMsList,name+'_make_pseudobadDOMsList',
                   Streams = [icetray.I3Frame.DetectorStatus],
                   If = lambda f: If_with_triggers(f) and check_estres_fit(f))

    tray.AddModule('StartingTrackVeto',name+'_StartingTrackVeto',
                   Pulses=pulsesname,
                   Photonics_Service=inf_muon_service,
                   Miss_Prob_Thresh=1,
                   Fit=filter_globals.estres_fit_name,
                   Particle_Segments=filter_globals.estres_fit_name+'_segments',
                   Distance_Along_Track_Type='cherdat',
                   Supress_Stochastics=True,
                   Min_CAD_Dist=350,
                   BadDOMs='StartingTrackVeto_pseudobadDOMsList',
                   If = lambda f: If_with_triggers(f) and check_estres_fit(f))
    def check_estres_track_veto_cuts(frame):
        #Check final veto critera, save to frame as a bool
        prob_name=pulsesname+'_'+filter_globals.estres_fit_name+'_prob_obs_0s_cherdat_1'
        p_miss=frame[prob_name].value
        frame["Estres_p_miss"]=frame[prob_name]
        dist_name=pulsesname+'_'+filter_globals.estres_fit_name+'_cherD_1'
        d=frame[dist_name].value
        frame["Estres_direct_length"]=frame[dist_name]
        if d>distance_thresh and p_miss<veto_thresh:
            frame['estres_filter_result'] = icetray.I3Bool(True)
            print("frame['estres_filter_result'] = icetray.I3Bool(True)")
    tray.AddModule(check_estres_track_veto_cuts, name+'check_estres_track_veto_cuts',
                   If = lambda f: If_with_triggers(f) and check_estres_fit(f))

    # actual filter decision
    tray.AddModule('I3FilterModule<I3BoolFilter>', name+'_ESTRES_Filter2018',
                   DiscardEvents = False,
                   Boolkey = 'estres_filter_result',
                   DecisionName = filter_globals.EstresAlertFilter,
                   If = lambda f: If_with_triggers(f) and check_estres_fit(f))


