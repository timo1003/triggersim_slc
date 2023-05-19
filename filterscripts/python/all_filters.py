from icecube import icetray, dataclasses
from icecube.filterscripts import filter_globals
from icecube.icetray import I3Units

import os.path

# Bring all the filters together.  A single segment to use
#    offline or online...

@icetray.traysegment
def OnlineFilter(tray, name, simulation=False, decode = False, If=lambda f: True,
        SplineRecoAmplitudeTable = None,
        SplineRecoTimingTable = None,
        PathToCramerRaoTable = None,
        GFUBDTUpPath = None,
        GFUBDTDownPath = None,
        sdstarchive = False,
        slop_split_enabled = True,
        vemcal_enabled=True, 
        gfu_enabled=True,
        needs_wavedeform_spe_corr = True,
        alert_followup=True,
        alert_followup_omit_GCD_diff=False,
        alert_followup_base_GCD_path="",
        alert_followup_base_GCD_filename=None,
        forceOnlineL2BadDOMList=None,
        ic79_geometry = False
        ):

    from icecube.phys_services.which_split import which_split

    # import all the actual worker segments....
    from icecube.filterscripts.baseproc import BaseProcessing
    from icecube.filterscripts.minbiasfilters import MinBiasFilters
    from icecube.filterscripts.minbiasfilters import ScintMinBiasFilters
    from icecube.filterscripts.dstfilter import DSTFilter
    from icecube.filterscripts.muonfilter import MuonFilter
    from icecube.filterscripts.cosmicrayfilter import CosmicRayFilter
    from icecube.filterscripts.cascadefilter import CascadeFilter
    from icecube.filterscripts.onlinel2filter import OnlineL2Filter
    from icecube.filterscripts.shadowfilter import ShadowFilter
    from icecube.filterscripts.deepcorefilter import DeepCoreFilter
    from icecube.filterscripts.fssfilter import FSSFilter
    from icecube.filterscripts.ehefilter import EHEFilter
    from icecube.filterscripts.lowupfilter import LowUpFilter
    from icecube.filterscripts.veffilter import VEFFilter
    from icecube.filterscripts.slopfilter import SLOPFilter
    from icecube.filterscripts.slopfilter import SLOPSplitter
    from icecube.filterscripts.fpfilter import FPFilter
    from icecube.filterscripts.fixedratefilter import FixedRateTrigFilter
    from icecube.filterscripts.hesefilter import HeseFilter
    from icecube.filterscripts.highqfilter import HighQFilter
    from icecube.filterscripts.mesefilter import MeseFilter
    from icecube.filterscripts.ehealertfilter import EHEAlertFilter
    from icecube.filterscripts.monopolefilter import MonopoleFilter
    from icecube.filterscripts.icetop2station import IceTopTwoStationFilter
    from icecube.filterscripts.estresfilter import ESTReSFilter
    from icecube.filterscripts.iceactsmtfilter import IceActTrigFilter
    from icecube.filterscripts.alerteventfollowup import AlertEventFollowup
    from icecube.filterscripts.grecofilter import GRECOOnlineFilter

    
    # Get the spline paths sorted.
    # This is used by Online L2 and ESTReS
    if (SplineRecoAmplitudeTable is None) or (SplineRecoTimingTable is None):
        domain = filter_globals.getDomain()
        if (domain == filter_globals.Domain.SPS) or (domain == filter_globals.Domain.SPTS):
            SplineDir                = '/opt/cvmfs/current/data/photon-tables/splines/'
            SplineRecoAmplitudeTable = os.path.join(SplineDir, 'InfBareMu_mie_abs_z20a10.fits')
            SplineRecoTimingTable    = os.path.join(SplineDir, 'InfBareMu_mie_prob_z20a10.fits')
        elif domain == filter_globals.Domain.ACCESS:
            SplineDir                = '/opt/cvmfs/current/data/photon-tables/splines/'
            SplineRecoAmplitudeTable = os.path.join(SplineDir, 'InfBareMu_mie_abs_z20a10.fits')
            SplineRecoTimingTable    = os.path.join(SplineDir, 'InfBareMu_mie_prob_z20a10.fits')
        else:
            SplineDir                = "/cvmfs/icecube.opensciencegrid.org/data/photon-tables/splines/"
            SplineRecoAmplitudeTable = os.path.join(SplineDir, 'InfBareMu_mie_abs_z20a10_V2.fits')
            SplineRecoTimingTable    = os.path.join(SplineDir, 'InfBareMu_mie_prob_z20a10_V2.fits')


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

## base processing requires:  GCD and frames being fed in by reader or Inlet
## base processing include:  decoding, TriggerCheck, Bad Dom cleaning, calibrators,
##     Feature extraction, pulse cleaning (seeded RT, and Time Window),
##     PoleMuonLineit, PoleMuonLlh, Cuts module and Mue on PoleMuonLlh

    if sdstarchive:
        tray.AddSegment(BaseProcessing, "BaseProc",
                        pulses=filter_globals.CleanedMuonPulses,
                        decode=decode,simulation=False,
                        needs_calibration=False, needs_superdst=False,
                        needs_maskmaker=True,
                        do_slop = slop_split_enabled,
                        needs_trimmer=False, seededRTConfig=seededRTConfig
                        )
    else:
        tray.AddSegment(BaseProcessing, "BaseProc",
                        pulses=filter_globals.CleanedMuonPulses,
                        decode=decode,simulation=simulation,
                        do_slop = slop_split_enabled,
                        seededRTConfig=seededRTConfig,
                        needs_wavedeform_spe_corr = needs_wavedeform_spe_corr
                        )

## Todo:  Check with IceTop group has this changed?
## Note: simulation doesn't run VEMCAL
    if vemcal_enabled:
        from icecube.filterscripts.vemcal import IceTopVEMCal
        tray.AddSegment(IceTopVEMCal, "VEMCALStuff")

## Filters that use the InIce Trigger splitting
    tray.AddSegment(MuonFilter, "MuonFilter",
                    pulses = filter_globals.CleanedMuonPulses,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )

## In the FSS segment the "pulses" are used for finiteReco, after customized hit
## cleaning which is not optimized for track fitting but rather for vetoing
## downgoing muons in top & side layers. So: do *not* provide pulses that are
## already e.g. SRT cleaned, such as CleanedMuonPulses.
    tray.AddSegment(FSSFilter, "FSSFilter",
                    pulses = filter_globals.SplitUncleanedInIcePulses,
                    If = which_split(split_name=filter_globals.InIceSplitter),
                    ic79_geometry = ic79_geometry
                    )

    tray.AddSegment(CascadeFilter, "CascadeFilter",
                    pulses = filter_globals.CleanedMuonPulses,
                    muon_llhfit_name=filter_globals.muon_llhfit,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )
    tray.AddSegment(VEFFilter, "VEF",
                    pulses = filter_globals.CleanedMuonPulses,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )

    tray.AddSegment(LowUpFilter, "LowUpFilter",
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )

    # High Q filter
    tray.AddSegment(HighQFilter, "HighQFilter",
                    pulses = filter_globals.SplitUncleanedInIcePulses,
                    If =  (which_split(split_name= filter_globals.InIceSplitter))
                    )

    # HESE veto (VHESelfVeto)
    tray.AddSegment(HeseFilter, "HeseFilter",
                    pulses = filter_globals.SplitUncleanedInIcePulses,
                    If =  (which_split(split_name= filter_globals.InIceSplitter))
                    )

    # MESE veto (Jakob van Santen's veto)
    tray.AddSegment(MeseFilter, "MeseFilter",
                    pulses = filter_globals.SplitUncleanedInIcePulses,
                    If =  (which_split(split_name= filter_globals.InIceSplitter))
                    )

    # OnlineL2, used by HESE and GFU
    tray.AddSegment(OnlineL2Filter, "OnlineL2",
                    pulses = filter_globals.CleanedMuonPulses,
                    linefit_name = filter_globals.muon_linefit,
                    llhfit_name = filter_globals.muon_llhfit,
                    SplineRecoAmplitudeTable = SplineRecoAmplitudeTable,
                    SplineRecoTimingTable = SplineRecoTimingTable,
                    PathToCramerRaoTable = PathToCramerRaoTable,
                    forceOnlineL2BadDOMList=forceOnlineL2BadDOMList,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )

    if (simulation):
        # sim data
        tray.AddSegment(ShadowFilter, "MoonAndSun",mcseed=424242,
                        If = which_split(split_name=filter_globals.InIceSplitter)
                        )
    else:
        # exp data
        tray.AddSegment(ShadowFilter, "MoonAndSun",
                        If = which_split(split_name=filter_globals.InIceSplitter)
                        )

    tray.AddSegment(ESTReSFilter,"ESTReSFilter",
                    pulsesname=filter_globals.SplitUncleanedInIcePulses,
                    base_processing_fit = filter_globals.muon_llhfit,
                    SplineRecoAmplitudeTable = SplineRecoAmplitudeTable,
                    SplineRecoTimingTable = SplineRecoTimingTable,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )


    tray.AddSegment(DeepCoreFilter,"DeepCoreFilter",
                    pulses = filter_globals.SplitUncleanedInIcePulses,
                    seededRTConfig = seededRTConfig,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )

    tray.AddSegment(GRECOOnlineFilter, "GRECOOnlineFilter",
                    uncleaned_pulses = filter_globals.SplitUncleanedInIcePulses,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )
                    
    #EHE, now on the InIce!
    tray.AddSegment(EHEFilter, "EHEFilter",
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )

    ## Filters on the Null split

    tray.AddSegment(MinBiasFilters, "MinBias",
                    If = which_split(split_name=filter_globals.NullSplitter)
                    )
    tray.AddSegment(FixedRateTrigFilter, "FixedRate",
                    If = which_split(split_name=filter_globals.NullSplitter)
                    )
    tray.AddSegment(ScintMinBiasFilters, "ScintMinBias",
                    If = which_split(split_name=filter_globals.NullSplitter)
                    )
    tray.AddSegment(IceActTrigFilter, "IceActFilters",
                    If = which_split(split_name=filter_globals.NullSplitter)
    )

    tray.AddSegment(DSTFilter, "DSTFilter",
                    dstname  = filter_globals.dst,
                    pulses   = filter_globals.CleanedMuonPulses,
                    If = which_split(split_name=filter_globals.InIceSplitter))
    ## SLOP filter
    if slop_split_enabled:
        tray.AddSegment(SLOPFilter, "SLOPFilter",
                        use_pulses=sdstarchive,
                        If = which_split(split_name=filter_globals.SLOPSplitter))

    ##FP filter
    tray.AddSegment(FPFilter,"FPFilter",
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )
    
    
    ## Filters on the CR split
    tray.AddSegment(CosmicRayFilter, "CosmicRayFilter",
                    Pulses = filter_globals.CleanedHLCTankPulses,
                    If = which_split(split_name=filter_globals.IceTopSplitter)
                    )
    tray.AddSegment(IceTopTwoStationFilter, "TwoStationFilter",
                    If = which_split(split_name=filter_globals.IceTopSplitter)
                    )

    ## Gamma-Ray Follow-Up
    if gfu_enabled:
        from icecube.filterscripts.gfufilter import GammaFollowUp
        tray.AddSegment(GammaFollowUp, "GammaFollowUp",
                        OnlineL2SegmentName = "OnlineL2",
                        BDTUpFile = GFUBDTUpPath,
                        BDTDownFile = GFUBDTDownPath,
                        angular_error = True,
                        If = which_split(split_name=filter_globals.InIceSplitter)
                        )

    ## EHE Online Alert Follow-up
    tray.AddSegment(EHEAlertFilter, "EHEAlertFilter",
                    If= which_split(split_name=filter_globals.InIceSplitter)
    )
    ## Monopole filter
    tray.AddSegment(MonopoleFilter, "MonopoleFilter",
                    pulses = filter_globals.SplitUncleanedInIcePulses,
                    seededRTConfig = seededRTConfig,
                    If = which_split(split_name=filter_globals.InIceSplitter)
                    )
    # Alert followup
    if alert_followup:
        tray.AddSegment(AlertEventFollowup, "AlertFollowup",
                        omit_GCD_diff = alert_followup_omit_GCD_diff,
                        base_GCD_path=alert_followup_base_GCD_path,
                        base_GCD_filename=alert_followup_base_GCD_filename,
                        If = (which_split(split_name= filter_globals.InIceSplitter))
                        )
