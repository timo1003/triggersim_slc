from icecube import icetray
from icecube.filterscripts import filter_globals

dst_header_prescale = 1000

@icetray.traysegment
def DSTFilter(tray, name, 
    dstname      = "I3DST16",
    pulses       = filter_globals.CleanedMuonPulses,
    llh_name     = filter_globals.muon_llhfit,
    linefit_name = filter_globals.muon_linefit,
    trigger_name = filter_globals.triggerhierarchy,
    If = lambda f: True):
    
    """
    Record in compact form limited information from reconstructions, triggers and cut
    parameters for every triggered event.
    """

    from icecube import dataclasses, dst
    from I3Tray import I3Units
    healpix_nside = 1024
    tray.AddModule("I3DSTModule16", name +"_dst",
               DSTName = dstname,
               DSTHeaderName = dstname+"Header",
               HealPixNSide=healpix_nside,
               EventHeaderName = "I3EventHeader",
               RecoSeriesName = pulses, 
               RecoList = [linefit_name,llh_name],
               LLHFitParamsName = llh_name + "FitParams", 
               EnergyEstimate = llh_name + 'MuE',
               LaunchMapSource = filter_globals.CleanInIceRawData,
               DetectorCenterX = 0.*I3Units.meter,
               DetectorCenterY = 0.*I3Units.meter,
               DetectorCenterZ = 0.*I3Units.meter,
               TriggerIDList = [filter_globals.inicesmtconfigid ,
                    filter_globals.volumetriggerconfigid,
                    filter_globals.slowparticleconfigid,
                    filter_globals.faintparticleconfigid,
                    filter_globals.inicestringconfigid,
                    filter_globals.deepcoreconfigid,
                    filter_globals.icetopsmtconfigid,
                    filter_globals.fixedrateconfigid],
               DSTHeaderPrescale = dst_header_prescale,
               If = If
               )
    
