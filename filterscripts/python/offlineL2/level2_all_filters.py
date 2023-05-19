from icecube import icetray, dataclasses
from icecube.icetray import I3Units

from icecube.filterscripts.offlineL2 import Globals
from icecube.filterscripts.offlineL2.Globals import (deepcore_wg, 
    muon_wg, wimp_wg, cascade_wg, 
    fss_wg, fss_wg_finiteReco, ehe_wg, ehe_wg_Qstream, monopole_wg)
from icecube.filterscripts.offlineL2.Rehydration import Rehydration, Dehydration
from icecube.filterscripts.offlineL2.level2_IceTop_CalibrateAndExtractPulses import CalibrateAndExtractIceTop
from icecube.filterscripts.offlineL2.level2_EHE_Calibration import EHECalibration
from icecube.filterscripts.offlineL2.level2_HitCleaning_IceTop import IceTopCoincTWCleaning
from icecube.filterscripts.offlineL2.level2_HitCleaning_DeepCore import DeepCoreHitCleaning
from icecube.filterscripts.offlineL2.level2_HitCleaning_WIMP import WimpHitCleaning
from icecube.filterscripts.offlineL2.level2_HitCleaning_Cascade import CascadeHitCleaning
from icecube.filterscripts.offlineL2.PhotonTables import InstallTables
from icecube.filterscripts.offlineL2.level2_Reconstruction_Muon import OfflineMuonReco
from icecube.filterscripts.offlineL2.level2_HitCleaning_EHE import HitCleaningEHE
from icecube.filterscripts.offlineL2.level2_Reconstruction_IceTop import ReconstructIceTop
from icecube.filterscripts.offlineL2.level2_Reconstruction_DeepCore import OfflineDeepCoreReco
from icecube.filterscripts.offlineL2.level2_Reconstruction_WIMP import WimpReco
from icecube.filterscripts.offlineL2.level2_Reconstruction_Cascade import OfflineCascadeReco
from icecube.filterscripts.offlineL2.level2_Reconstruction_SLOP import SLOPLevel2
from icecube.filterscripts.offlineL2.level2_Reconstruction_EHE import ReconstructionEHE
from icecube.filterscripts.offlineL2.level2_Reconstruction_Monopole import MonopoleL2
from icecube.filterscripts.offlineL2.ClipStartStop import ClipStartStop
from icecube.phys_services.which_split import which_split

@icetray.traysegment
def OfflineFilter(tray, name,
                  dstfile = None,
                  mc = False,
                  pass2 = False,
                  doNotQify = False,
                  photonicsdir = None,
                  If = lambda f: True,
                  ):
    ##################################################################
    #########  Level 1                                     ###########
    #########  IF SIM, do L1 that was done on PnF          ###########
    #########  IF DATA, Rehydrate, recalibrate             ###########
    #########  FOR BOTH,  recal, resplit IT                ###########
    ##################################################################

    tray.AddModule(ClipStartStop, 'clipstartstop')

    #if mc:
    #    tray.AddSegment(Dehydration, 'dehydrator')
    
    # Rehydration includes recalibration of both II and IT pulses
    ## Only resplit II, IT has own splitting later, nobody uses 
    ## NullSplit anymore. Give SLOP it's own split stream since
    ## FRT sometimes merges multiple SLOPs.
    tray.AddSegment(Rehydration, 'rehydrator',
        dstfile=dstfile,
        mc=mc,
        doNotQify=doNotQify,
        pass2=pass2,
    )

    ## relic of redoing pole fits. That got taken out.
    ## but need to keep doing SRT cleaning for all the filters
    # Create a SeededRT configuration object with the standard RT settings.
    # This object will be used by all the different SeededRT modules, i.e. the
    # modules use the same causial space and time conditions, but can use
    # different seed algorithms.
    from icecube.STTools.seededRT.configuration_services import I3DOMLinkSeededRTConfigurationService
    seededRTConfig = I3DOMLinkSeededRTConfigurationService(
                         ic_ic_RTRadius              = 150.0*I3Units.m,
                         ic_ic_RTTime                = 1000.0*I3Units.ns,
                         treat_string_36_as_deepcore = False,
                         useDustlayerCorrection      = False,
                         allowSelfCoincidence        = True
                     )
    tray.AddModule('I3SeededRTCleaning_RecoPulseMask_Module', 'North_seededrt',
        InputHitSeriesMapName  = 'SplitInIcePulses',
        OutputHitSeriesMapName = 'SRTInIcePulses',
        STConfigService        = seededRTConfig,
        SeedProcedure          = 'HLCCoreHits',
        NHitsThreshold         = 2,
        MaxNIterations         = 3,
        Streams                = [icetray.I3Frame.Physics],
        If = which_split(split_name='InIceSplit') & (lambda f: (
                         deepcore_wg(f) or wimp_wg(f)    or
                         muon_wg(f)     or cascade_wg(f) or
                         ehe_wg(f)      or fss_wg(f) ))
    )

    ## IceTop pules calibration
    tray.AddSegment(CalibrateAndExtractIceTop, 'CalibrateAndExtractIceTop',
        Pulses='IceTopPulses'
    )

    ## EHE Calibration
    tray.AddSegment(EHECalibration, 'ehecalib',
        inPulses='CleanInIceRawData',
        outATWD='EHECalibratedATWD_Wave',
        outFADC='EHECalibratedFADC_Wave',
        If=lambda f: ehe_wg_Qstream(f)
    )

    ###################################################################
    ########### HIT CLEANING    #######################################
    ###################################################################
    # icetop hitcleaning & splitting #
    tray.AddSegment(IceTopCoincTWCleaning, 'IceTopCoincTWCleaning',
        VEMPulses = 'CleanedHLCTankPulses',
        OfflinePulses = 'InIcePulses'
    )

    # deepcore hitcleaning #
    tray.AddSegment(DeepCoreHitCleaning,'DCHitCleaning', 
        If=which_split(split_name='InIceSplit') & (lambda f: deepcore_wg(f))
    )

    # wimp & FSS hitcleaning #
    # commented at request of BSM WG for 2019 runstart
    # tray.AddSegment(WimpHitCleaning, "WIMPstuff",
    #     seededRTConfig = seededRTConfig,
    #     If=which_split(split_name='InIceSplit') & (lambda f: (
    #                    wimp_wg(f) or fss_wg_finiteReco(f))),
    #     suffix='_WIMP', 
    # )

    # cascade hit cleaning #
    tray.AddSegment(CascadeHitCleaning,'CascadeHitCleaning', 
        If=which_split(split_name='InIceSplit') & (lambda f: cascade_wg(f)),
    )

    # ehe hit cleaning #
    tray.AddSegment(HitCleaningEHE, 'eheclean',
        inATWD='EHECalibratedATWD_Wave', inFADC = 'EHECalibratedFADC_Wave',
        If=which_split(split_name='InIceSplit') & (lambda f: ehe_wg(f))
    )

    ###################################################################
    ########### RECONSTRUCTIONS/CALCULATIONS ##########################
    ###################################################################
    # load tables #
    if photonicsdir is not None:
        tray.AddSegment(InstallTables, 'InstallPhotonTables',
            PhotonicsDir=photonicsdir
        )
    else:
        tray.AddSegment(InstallTables, 'InstallPhotonTables')

    # muon, cascade, wimp, fss #
    tray.AddSegment(OfflineMuonReco, 'OfflineMuonRecoSLC',
        Pulses = "SRTInIcePulses",
	If = which_split(split_name='InIceSplit') & (lambda f: (
	                 muon_wg(f) or cascade_wg(f) or
	                 wimp_wg(f) or fss_wg(f))),
        suffix = "", #null? copied from level2_globals supplied
    )

    # icetop #
    tray.AddSegment(ReconstructIceTop, 'ReconstructIceTop',

        Pulses      = 'CleanedHLCTankPulses',
        CoincPulses = 'CleanedCoincOfflinePulses',
        If = which_split(split_name=Globals.filter_globals.IceTopSplitter)#'ice_top')
    )

    # deepcore #
    tray.AddSegment(OfflineDeepCoreReco,'DeepCoreL2Reco',
        pulses='SRTTWOfflinePulsesDC',
        If=which_split(split_name='InIceSplit') & (lambda f: deepcore_wg(f)),
        suffix='_DC'
    )

    # wimp, fss #
    # commented at request of BSM WG for 2019 runstart
    # tray.AddSegment(WimpReco, "WIMPreco",
    #     If=which_split(split_name='InIceSplit') & (lambda f: (
    #                    wimp_wg(f) or fss_wg_finiteReco(f))),
    #     suffix='_WIMP',
    # )

    # cascade #
    tray.AddSegment(OfflineCascadeReco,'CascadeL2Reco',
        SRTPulses='SRTInIcePulses',
        Pulses='TWOfflinePulsesHLC',
        TopoPulses = 'OfflinePulsesHLC',
        If=which_split(split_name='InIceSplit') & (lambda f: cascade_wg(f)),
        suffix='_L2'
    )

    # slop #
    tray.AddSegment(SLOPLevel2, "slop_me", 
        If = which_split(split_name='SLOPSplit')
    )

    # ehe #
    tray.AddSegment(ReconstructionEHE, 'ehereco',
        Pulses='EHETWCInIcePulsesSRT',
        suffix='EHE', LineFit = 'LineFit',
        SPEFitSingle='SPEFitSingle', SPEFit = 'SPEFit12',
        N_iter=12,
        If=which_split(split_name='InIceSplit') & (lambda f: ehe_wg(f))
    )
    
    tray.AddSegment(MonopoleL2, "monopole",
                    pulses= "SplitInIcePulses",
                    seededRTConfig = seededRTConfig,
                    If = which_split(split_name='InIceSplit') & monopole_wg
    )
    
