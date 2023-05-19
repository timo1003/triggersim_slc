from icecube import icetray

# written by Markus Voge <voge@physik.uni-bonn.de>

@icetray.traysegment
def OpticalFollowUp(tray, name,
        OnlineL2SegmentName='OnlineL2',
        BDTFilePath=None,
        testing=False,
        If = lambda f: True):
    """
    This tray segment is doing the 2014 OpticalFollowUp filtering.

    :param OnlineL2SegmentName:
        Name of OnlineL2 segment is needed to fetch variables using appropriate names.
    :param testing:
        Run this segment in testing mode, not in real Pole conditions.
    :param If:
        Python function to use as conditional execution test for segment modules.
    """

    from os.path import expandvars
    import datetime
    import json
    import numpy as np

    from icecube import dataclasses, phys_services, gulliver
    from icecube.pybdtmodule import PyBDTModule
    # using the CommonVariables: http://icecube.wisc.edu/~mwolf/docs/projects/CommonVariables/
    # for Cuts (NCh, QTot, COG, NDir, LDir, SAll, LEmpty, Separation)
    from icecube.common_variables import direct_hits, hit_multiplicity, hit_statistics, track_characteristics
    from icecube.filterscripts import filter_globals

    # load needed libs, the "False" suppresses any "Loading..." messages
    icetray.load("filterscripts", False)

    #############################
    #  Settings
    #############################

    # BDT file
    if (BDTFilePath is None):
        # try to guess path
        domain = filter_globals.getDomain()
        if domain == filter_globals.Domain.SPS or domain == filter_globals.Domain.SPTS:
            BDTFilePath = "/usr/local/pnf/jeb/filterscripts/resources/data/bdt_ofu_IC86_2.bdt"
        else:
            BDTFilePath = expandvars("$I3_BUILD/filterscripts/resources/data/bdt_ofu_IC86_2.bdt")

    #############################
    #  Helper functions
    #############################

    def BoolUpdater(boolToUpdate, updateWithThisBool):
        def BoolUpdateDo(frame):
            frame.Delete(boolToUpdate)
            if frame.Has(updateWithThisBool):
                frame[boolToUpdate] = frame[updateWithThisBool]
            else:
                frame[boolToUpdate] = icetray.I3Bool(False)
        return BoolUpdateDo

    def get_dict_from_frame(frame):
        if not frame.Has(name+'_BDT_Score'): return True
        bdtscore = frame[name+'_BDT_Score'].value
        if not frame.Has(filter_globals.eventheader): return True
        header = frame[filter_globals.eventheader]
        runid = header.run_id
        eventid = header.event_id
        detectortime = header.start_time
        if not frame.Has(OnlineL2SegmentName+'_BestFit'): return True
        bestevent = frame[OnlineL2SegmentName+'_BestFit']
        zenith = bestevent.dir.zenith
        azimuth = bestevent.dir.azimuth
        if not frame.Has(OnlineL2SegmentName+'_CramerRao_BestFitParams'): return True
        cr_zen = frame[OnlineL2SegmentName+'_CramerRao_BestFitParams'].cramer_rao_theta
        cr_azi = frame[OnlineL2SegmentName+'_CramerRao_BestFitParams'].cramer_rao_phi
        if not frame.Has(OnlineL2SegmentName+'_BestFitDirectHitsC'): return True
        directhits = frame[OnlineL2SegmentName+'_BestFitDirectHitsC']
        ndir = directhits.n_dir_doms
        ldir = directhits.dir_track_length
        if not frame.Has(OnlineL2SegmentName+'_BestFit_MuEx'): return True
        energy = frame[OnlineL2SegmentName+'_BestFit_MuEx'].energy
        if not frame.Has(OnlineL2SegmentName+'_HitMultiplicityValues'): return True
        nch = frame[OnlineL2SegmentName+'_HitMultiplicityValues'].n_hit_doms
        if not frame.Has(OnlineL2SegmentName+'_BestFitFitParams'): return True
        logl = frame[OnlineL2SegmentName+'_BestFitFitParams'].logl
        time = datetime.datetime.utcnow()
        finalstring = json.dumps({'bdt': round(bdtscore, 5),
                                  'runid': runid,
                                  'eventid': eventid,
                                  'eventtime': str(detectortime.date_time),
                                  'proctime': str(time),
                                  'zenith': round(zenith, 5),
                                  'azimuth': round(azimuth, 5),
                                  'crzen': round(cr_zen, 5),
                                  'crazi': round(cr_azi, 5),
                                  'ndir': ndir,
                                  'ldir': round(ldir, 5),
                                  'energy': round(energy, 5),
                                  'nch': nch,
                                  'logl': round(logl, 5)})
        if frame.Has(name+"_valuesdict"): return True
        frame[name+"_valuesdict"] = dataclasses.I3String(finalstring)

    ####################################
    # Helpers for calculateBDTVariables
    ####################################
    def getBestFit(frame, bestfitkey):
        # OnlineL2_BestFit_Zenith
        if not frame.Has(bestfitkey):
            icetray.logging.log_warn("Event has no BestFit named %s, rejecting event." % bestfitkey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return (False, None, None)
        bestFit = frame[bestfitkey]
        bestFit_llh = frame[bestfitkey+'FitParams'].logl
        if not frame.Has(name+'_BestFit_Zenith'):
            frame.Put(name+'_BestFit_Zenith', dataclasses.I3Double(bestFit.dir.zenith))
        if not frame.Has(name+'_BestFit_Azimuth'):
            frame.Put(name+'_BestFit_Azimuth', dataclasses.I3Double(bestFit.dir.azimuth))
        icetray.logging.log_trace("getBestFit passed.")
        return (True, bestFit, bestFit_llh)

    def getPLogL(frame, llh_paramskey, hitmultiplicitykey, subtrahend=3.5):
        # plogl35_llh
        if not frame.Has(llh_paramskey):
            icetray.logging.log_warn("Frame does not have FitParams %s, discarding it." % llh_paramskey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return (False, None)
        llhlogl = frame[llh_paramskey].logl
        if not frame.Has(hitmultiplicitykey):
            icetray.logging.log_warn("Frame does not have HitMultiplicityValues %s for getting NChannel, discarding it." % hitmultiplicitykey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return (False, None)
        nch = frame[hitmultiplicitykey].n_hit_doms
        plogl = llhlogl / (nch - subtrahend)
        if not frame.Has(name+'_PoleMuonLlhFit_plogl_3p5'):
            frame.Put(name+'_PoleMuonLlhFit_plogl_3p5', dataclasses.I3Double(plogl))
        icetray.logging.log_trace("getPLogL passed.")
        return (True, plogl)

    def getSplitZenithes(frame, splitkeys, bestFit):
        #OFU_modified_min_split_zenith
        splitZenithes = []
        for splitkey in splitkeys:
          if not frame.Has(splitkey):
              icetray.logging.log_debug('Frame has no split fit %s' % splitkey)
          else:
              splitZenithes.append(frame[splitkey].dir.zenith)
        noNaNSplitZenithes = [ z for z in splitZenithes if not np.isnan(z) ]
        if len(noNaNSplitZenithes) == 0:
            icetray.logging.log_info("All SplitFit Zenithes are NaN! Event is rejected.")
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return (False, None, None)
        min_split_zenith = np.cos( np.min(noNaNSplitZenithes) )
        modified_min_split_zenith = min_split_zenith - np.cos(bestFit.dir.zenith) - 0.5
        if not frame.Has(name+'_modified_min_split_zenith'):
            frame.Put(name+'_modified_min_split_zenith', dataclasses.I3Double(modified_min_split_zenith))
        #OFU_Max_split_zenith_diff
        max_split_zenith_diff = np.maximum(np.abs(splitZenithes[3] - splitZenithes[2]),
                                               np.abs(splitZenithes[1] - splitZenithes[0]))
        icetray.logging.log_trace("getSplitZenithes passed.")
        return (True, modified_min_split_zenith, max_split_zenith_diff)

    def getLinefit(frame, linefitkey, bestFit):
        #DelAngMPELineFit
        if not frame.Has(linefitkey):
            icetray.logging.log_warn("Event has no Linefit named %s, rejecting event." % linefitkey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return (False, None)
        linefit = frame[linefitkey]
        delAng_MPE_linefit = \
                2. * np.arcsin( \
                    np.sqrt( \
                        np.sin((linefit.dir.zenith - bestFit.dir.zenith) * 0.5)**2. \
                        + np.sin(linefit.dir.zenith) * np.sin(bestFit.dir.zenith) * \
                            np.sin((linefit.dir.azimuth - bestFit.dir.azimuth) * 0.5)**2. \
                    ) \
                )
        # LinefitVelocity
        LinefitVelocity = linefit.speed
        if not frame.Has(name+'_LinefitVelocity'):
            frame.Put(name+'_LinefitVelocity', dataclasses.I3Double(LinefitVelocity))
        icetray.logging.log_trace("getLinefit passed.")
        return (True, delAng_MPE_linefit)

    def getDirects(frame, bestfitdirecthitskey):
        # OnlineL2_BestFit_NDirC
        if not frame.Has(bestfitdirecthitskey):
            icetray.logging.log_warn("Frame does not have BestFit DirectHitValues %s, discarding it." % bestfitdirecthitskey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return (False, None)
        bestDirectHits = frame[bestfitdirecthitskey]
        ndirc = bestDirectHits.n_dir_doms
        if not frame.Has(name+'_BestFit_NDirC'):
            frame.Put(name+'_BestFit_NDirC', dataclasses.I3Double(ndirc))
        # OnlineL2_BestFit_LDirC
        ldirc = bestDirectHits.dir_track_length
        if not frame.Has(name+'_BestFit_LDirC'):
            frame.Put(name+'_BestFit_LDirC', dataclasses.I3Double(ldirc))
        icetray.logging.log_trace("getDirects passed.")
        return (True, ldirc)

    def getSmoothAll(frame, bestfitsallkey):
        # MPEFit_Sall
        if not frame.Has(bestfitsallkey):
            icetray.logging.log_warn("Frame does not have BestFit TrackCharacteristics with SAll %s, discarding it." % bestfitsallkey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return False
        bestCharaWithSAll = frame[bestfitsallkey]
        sall = bestCharaWithSAll.track_hits_distribution_smoothness
        if not frame.Has(name+'_BestFit_Sall'):
            frame.Put(name+'_BestFit_Sall', dataclasses.I3Double(sall))
        icetray.logging.log_trace("getSmoothAll passed.")
        return True

    def getHitStatistics(frame, hitstatisticskey, bestFit):
        # QTot
        if not frame.Has(hitstatisticskey):
            icetray.logging.log_warn("Frame has no HitStatistics called %s, rejecting event.", hitstatisticskey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return False
        QTot = frame[hitstatisticskey].q_tot_pulses
        if not frame.Has(name+'_QTot'):
            frame.Put(name+'_QTot', dataclasses.I3Double(QTot))
        # MPEFit_dist2cog
        dist2cog = phys_services.I3Calculator.closest_approach_distance(bestFit, frame[hitstatisticskey].cog)
        if not frame.Has(name+'_BestFit_dist2cog'):
            frame.Put(name+'_BestFit_dist2cog', dataclasses.I3Double(dist2cog))
        icetray.logging.log_trace("getHitStatistics passed.")
        return True

    def getHitCharacteristics(frame, bestfitcharakey, ldirc):
        # LEmpty_divby_LDirC
        if not frame.Has(bestfitcharakey):
            icetray.logging.log_warn("Frame has no BestFit Characteristics %s, rejecting event.", bestfitcharakey)
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return False
        LEmpty = frame[bestfitcharakey].empty_hits_track_length
        try:
          LEmpty_divby_LDirC = LEmpty / ldirc
        except:
          LEmpty_divby_LDirC = 1.
        if not frame.Has(name+'_LEmpty_divby_LDirC'):
            frame.Put(name+'_LEmpty_divby_LDirC', dataclasses.I3Double(LEmpty_divby_LDirC))
        icetray.logging.log_trace("getHitCharacteristics passed.")
        return True

    def getMuEx(frame, muexkey):
        # OnlineL2_BestFit_MuEx_energy
        if not frame.Has(muexkey):
            icetray.logging.log_warn("Frame has no MuEx, rejecting event.")
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return False
        muex = frame[muexkey].energy
        if not frame.Has(name+'_BestFit_MuEx_energy'):
            frame.Put(name+'_BestFit_MuEx_energy', dataclasses.I3Double(muex))
        icetray.logging.log_trace("getMuEx passed.")
        return True

    def getBayesianFits(frame, bayesianparamskey, bestFit_llh, \
            baytimesplit1paramskey, baytimesplit2paramskey, \
            baygeosplit1paramskey, baygeosplit2paramskey):
        # BayesianMPEllhratio
        if not frame.Has(bayesianparamskey):
            icetray.logging.log_warn("Frame has no Bayesian fit params, rejecting event.")
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return False
        bayesian_llh = frame[bayesianparamskey].logl
        BayesianMPEllhratio = bayesian_llh - bestFit_llh
        if not frame.Has(name+'_Bayesian_MPE_llhratio'):
            frame.Put(name+'_Bayesian_MPE_llhratio', dataclasses.I3Double(BayesianMPEllhratio))
        # split_min_bayes_version1
        for s in (baytimesplit1paramskey, baytimesplit2paramskey, baygeosplit1paramskey, baygeosplit2paramskey):
            if not frame.Has(s):
                icetray.logging.log_warn("Frame has no Bayesian fit params named %s, rejecting event." % s)
                frame.Delete(name+"_Singlet")
                frame[name+"_Singlet"] = icetray.I3Bool(False)
                return False
        BayTimeSplit1_logl = frame[baytimesplit1paramskey].logl
        BayTimeSplit2_logl = frame[baytimesplit2paramskey].logl
        BayGeoSplit1_logl = frame[baygeosplit1paramskey].logl
        BayGeoSplit2_logl = frame[baygeosplit2paramskey].logl
        bay_min_split_llh_ratio = np.minimum(BayTimeSplit1_logl - BayTimeSplit2_logl, BayGeoSplit1_logl - BayGeoSplit2_logl)
        if not frame.Has(name+'_Bayesian_Minimal_Split_llhratio'):
            frame.Put(name+'_Bayesian_Minimal_Split_llhratio', dataclasses.I3Double(bay_min_split_llh_ratio))
        icetray.logging.log_trace("getBayesianFits passed.")
        return True

    ###############################
    ### precuts
    ###############################
    def precuts(frame, bestFit, plogl3p5, \
            modified_min_split_zenith, max_split_zenith_diff, \
            delAng_MPE_linefit):
        if not bestFit.dir.zenith >= 90. * np.pi / 180.:
            icetray.logging.log_trace("Event downgoing")
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return False
        if not plogl3p5 <= 8.3 or not modified_min_split_zenith <= 1 or not max_split_zenith_diff <= 2 or not delAng_MPE_linefit <= 1.5:
            icetray.logging.log_trace("Event does not pass precuts")
            frame.Delete(name+"_Singlet")
            frame[name+"_Singlet"] = icetray.I3Bool(False)
            return False
        else:
            icetray.logging.log_trace("Event passes precuts")
            return True

    #############################
    #  BDT helper functions
    #############################

    # this function puts all the variables needed by the BDT into the frame *AND* applies precuts:
    def calculateBDTVariables(frame):
        # variable name definitions:
        bestfitkey = OnlineL2SegmentName+"_BestFit"
        llh_paramskey = filter_globals.muon_llhfit+"FitParams"
        hitmultiplicitykey = OnlineL2SegmentName+"_HitMultiplicityValues" # for NChannel
        hitstatisticskey = OnlineL2SegmentName+"_HitStatisticsValues" # for QTot, COG
        bestfitdirecthitskey = OnlineL2SegmentName+"_BestFitDirectHitsC" # for NDir, LDir
        bestfitcharakey = OnlineL2SegmentName+"_BestFitCharacteristics" # for LEmpty, Separation
        bestfitsallkey = OnlineL2SegmentName+"_BestFitCharacteristicsWithSAll" # for SAll
        responsekey = "FirstPulseMuonPulses"
        linefitkey = filter_globals.muon_linefit
        splitkeys = [OnlineL2SegmentName+"_SplitGeo1_SPE2itFit", 
                     OnlineL2SegmentName+"_SplitGeo2_SPE2itFit",
                     OnlineL2SegmentName+"_SplitTime1_SPE2itFit", 
                     OnlineL2SegmentName+"_SplitTime2_SPE2itFit"]
        muexkey = OnlineL2SegmentName+"_BestFit_MuEx"
        bayesianparamskey = OnlineL2SegmentName+"_BayesianFitFitParams"
        baytimesplit1paramskey = OnlineL2SegmentName+"_SplitTime1_BayesianFitFitParams"
        baytimesplit2paramskey = OnlineL2SegmentName+"_SplitTime2_BayesianFitFitParams"
        baygeosplit1paramskey = OnlineL2SegmentName+"_SplitGeo1_BayesianFitFitParams"
        baygeosplit2paramskey = OnlineL2SegmentName+"_SplitGeo2_BayesianFitFitParams"

        retVal, bestFit, bestFit_llh = getBestFit(frame, bestfitkey)
        if not retVal:
            return True

        retVal, OFU_PoleMuonLlhFit_plogl_3p5 = getPLogL(frame, llh_paramskey, hitmultiplicitykey, subtrahend=3.5)
        if not retVal:
            return True

        retVal, OFU_modified_min_split_zenith, OFU_Max_split_zenith_diff = \
                getSplitZenithes(frame, splitkeys, bestFit)
        if not retVal:
            return True

        retVal, OFU_DelAng_MPELineFit = getLinefit(frame, linefitkey, bestFit)
        if not retVal:
            return True

        ### precuts
        if not precuts(frame, bestFit, OFU_PoleMuonLlhFit_plogl_3p5, \
                       OFU_modified_min_split_zenith, OFU_Max_split_zenith_diff, \
                       OFU_DelAng_MPELineFit):
            return True

        retVal, OFU_BestFit_LDirC = getDirects(frame, bestfitdirecthitskey)
        if not retVal:
            return True

        if not getSmoothAll(frame, bestfitsallkey):
            return True

        if not getHitStatistics(frame, hitstatisticskey, bestFit):
            return True

        if not getHitCharacteristics(frame, bestfitcharakey, OFU_BestFit_LDirC):
            return True

        if not getMuEx(frame, muexkey):
            return True

        if not getBayesianFits(frame, bayesianparamskey, bestFit_llh, \
                baytimesplit1paramskey, baytimesplit2paramskey, \
                baygeosplit1paramskey, baygeosplit2paramskey):
            return True
    # end calculateBDTVariables

    # helper function for PyBDTModule
    def varsfunc(frame):
        keys_and_names = {
                name+'_PoleMuonLlhFit_plogl_3p5':        'OFU_PoleMuonLlhFit_plogl_3p5',
                name+'_BestFit_Zenith':                  'OFU_BestFit_Zenith',
                name+'_BestFit_NDirC':                   'OFU_BestFit_NDirC',
                name+'_BestFit_LDirC':                   'OFU_BestFit_LDirC',
                name+'_QTot':                            'OFU_QTot',
                name+'_LinefitVelocity':                 'OFU_LinefitVelocity',
                name+'_modified_min_split_zenith':       'OFU_modified_min_split_zenith',
                name+'_LEmpty_divby_LDirC':              'OFU_LEmpty_divby_LDirC',
                name+'_BestFit_Sall':                    'OFU_BestFit_Sall',
                name+'_BestFit_dist2cog':                'OFU_BestFit_dist2cog',
                name+'_BestFit_MuEx_energy':             'OFU_PoleL2MPEFit_MuEx_energy',
                name+'_Bayesian_MPE_llhratio':           'OFU_Bayesian_MPE_llhratio',
                name+'_Bayesian_Minimal_Split_llhratio': 'OFU_Bayesian_Minimal_Split_llhratio',
                }
        Dict = {}
        for key, dname in keys_and_names.items():
            if frame.Has(key):
                Dict[dname] = frame[key].value
            else:
                Dict[dname] = 0.
        return Dict

    class bdtcut(icetray.I3ConditionalModule):
        '''
        Module that takes the name+"_BDT_Score" calculated by PyBDTModule and
        applies a cut on it.  Result written to frame as I3Bool `decisionName'.
        '''
        def __init__(self, context):
            icetray.I3ConditionalModule.__init__(self, context)
            self.AddParameter("cutvalue", "BDT score cut value (events with score >= cut pass)", -1.)
            self.AddParameter("decisionName", "Name of bool in frame with cut result", "BDT")
            self.AddParameter("discardEvents", "Discard the events if not passing cut?", False)
            self.AddOutBox("OutBox")

        def Configure(self):
            self.cutvalue = self.GetParameter("cutvalue")
            self.decisionName = self.GetParameter("decisionName")
            self.discardEvents = self.GetParameter("discardEvents")

        def Physics(self, frame):
            frame.Delete(self.decisionName)
            if not frame.Has(name+'_BDT_Score'):
                frame.Put(self.decisionName, icetray.I3Bool(False))
            else:
                score = frame[name+'_BDT_Score'].value
                frame.Put(self.decisionName, icetray.I3Bool(score >= self.cutvalue))
            if self.discardEvents:
                if not frame[self.decisionName].value:
                    return
            self.PushFrame(frame)

    #############################
    #  Filter functions
    #############################

    # Conditional execution for OFU singlet events
    def ThisEventMightBeOFUSinglet(frame):
        returnVal = False
        if frame.Has(name+"_Singlet"):
            returnVal = frame[name+"_Singlet"].value
        return returnVal

    # Conditional execution for L2 events
    def ThisEventPassedOnlineL2Filter(frame):
        returnVal = False
        if frame.Has(filter_globals.OnlineL2Filter):
            returnVal = frame[filter_globals.OnlineL2Filter].value
        return returnVal

    ############################
    # First module comes here
    ############################

    tray.AddModule(BoolUpdater(name+"_Singlet", filter_globals.OnlineL2Filter),
            name+"_BoolUpdater_OnlineL2Filter",
            If = lambda f: If(f) and ThisEventPassedOnlineL2Filter(f)
            )

    ################################
    # OFU Filter start
    #

    # BDT variables and precuts
    tray.AddModule(calculateBDTVariables, name+"_calculateBDTVariables",
            If = lambda f: If(f) and ThisEventMightBeOFUSinglet(f)
            )

    # Getting BDT score
    tray.AddModule(PyBDTModule, name+'_calculateBDTScore',
            BDTFilename = BDTFilePath,
            varsfunc = varsfunc,
            OutputName = name+'_BDT_Score',
            If = lambda f: If(f) and ThisEventMightBeOFUSinglet(f)
            )

    # alert OFU cuts
    tray.AddModule(bdtcut, name+'_BDTCutModule_OFU',
            cutvalue = 0.1,
            discardEvents = False,
            decisionName = name+"_BDT_Cut",
            If = lambda f: If(f) and ThisEventMightBeOFUSinglet(f)
            )
    tray.AddModule(BoolUpdater(name+"_Singlet", name+"_BDT_Cut"),
            name+"_BoolUpdater_OFU_BDT_Cut",
            If = lambda f: If(f) and ThisEventMightBeOFUSinglet(f)
            )

    ### add your IC86 2014 ofu filter here
    ############################################################################
    tray.AddModule("I3FilterModule<I3BoolFilter>", name+"_OFUFilter2014",
        DiscardEvents = False,
        Boolkey = name+"_Singlet",
        #TriggerEvalList = [filter_globals.slowparticletriggered],
        DecisionName = filter_globals.OFUFilter,
        If = lambda f: If(f) and ThisEventPassedOnlineL2Filter(f)
        )

    tray.AddModule(get_dict_from_frame, name+"_valuesdict",
            If = lambda f: If(f) and ThisEventMightBeOFUSinglet(f)
            )

    # OFU Filter end
    #
    #########################

#######################################
## clean up
#######################################

    leftovers = [
                 name+"_Singlet",
                 name+"_BestFit_Zenith",
                 name+"_BestFit_Azimuth",
                 name+"_BestFit_NDirC",
                 name+"_BestFit_LDirC",
                 name+"_BestFit_Sall",
                 name+"_PoleMuonLlhFit_plogl_3p5",
                 name+"_modified_min_split_zenith",
                 name+"_QTot",
                 name+"_LinefitVelocity",
                 name+"_LEmpty_divby_LDirC",
                 name+"_BestFit_dist2cog",
                 name+"_BestFit_MuEx_energy",
                 name+"_Bayesian_MPE_llhratio",
                 name+"_Bayesian_Minimal_Split_llhratio",
                 name+"_daqmodefilter",
                 name+"_runsummarypflidfilter",
                 name+"_filtermaskypflidfilter",
                 name+"_Moni_BDT_Cut",
                 name+"_BDT_Cut",
                ]

    # Remove all the temporary frame objects
    tray.AddModule("Delete", name+"_delete_ofu_leftovers",
            Keys = leftovers,
            If = lambda f: If(f) and ThisEventPassedOnlineL2Filter(f)
            )


    if testing:
        filter_globals.ofufilter_keeps += [
                filter_globals.OFUFilter,
                ]
    filter_globals.ofufilter_keeps += [
            name+"_valuesdict",
            name+"_BDT_Score",
            ]
