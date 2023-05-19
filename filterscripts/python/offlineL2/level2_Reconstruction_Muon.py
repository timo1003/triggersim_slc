from icecube import icetray, dataclasses
from icecube import linefit, lilliput
from icecube.icetray import I3Units
from icecube.filterscripts.offlineL2.Globals import muon_wg, wimp_wg, fss_wg,fss_wg_energy_reco
from icecube.phys_services.which_split import which_split
import icecube.lilliput.segments

@icetray.traysegment
def SPE(tray, name, Pulses = '', If = lambda f: True, suffix = '',
        LineFit = 'LineFit',
        SPEFitSingle = 'SPEFitSingle',
        SPEFit = 'SPEFit2',
        SPEFitCramerRao = 'SPEFit2CramerRao',
        N_iter = 2,
        ):

    tray.AddSegment( linefit.simple, LineFit+suffix, inputResponse = Pulses, fitName = LineFit+suffix, If = If )

    tray.AddSegment(lilliput.segments.I3SinglePandelFitter, SPEFitSingle+suffix,
                    fitname = SPEFitSingle+suffix,
                    pulses = Pulses,
                    seeds = [LineFit+suffix],
                    If = If
                    )
    
    if N_iter > 1:
        tray.AddSegment(lilliput.segments.I3IterativePandelFitter, SPEFit+suffix,
                        fitname = SPEFit+suffix,
                        pulses = Pulses,
                        n_iterations = N_iter,
                        seeds = [ SPEFitSingle+suffix ],
                        If = If
                        )

    #use only first hits.  Makes sense for an SPE likelihood
    tray.AddModule('CramerRao', name + '_' + SPEFitCramerRao + suffix,
                   InputResponse = Pulses,
                   InputTrack = SPEFit+suffix,
                   OutputResult = SPEFitCramerRao+suffix,
                   AllHits = False, # ! doesn't make sense to use all hit for SPE pdf
                   DoubleOutput = False, # Default
                   z_dependent_scatter = True, # Default
                   If = which_split(split_name='InIceSplit') & (lambda f: muon_wg(f) or fss_wg(f)),
                   ) 

@icetray.traysegment
def MPE(tray, name, Pulses = '', Seed = '', If = lambda f: True, suffix = '',
        MPEFit = 'MPEFit',
        MPEFitCramerRao = 'MPEFitCramerRao',
        ):

    tray.AddSegment(lilliput.segments.I3SinglePandelFitter, MPEFit+suffix,
                    fitname = MPEFit+suffix,
                    pulses = Pulses,
                    seeds = [ Seed+suffix ],
                    domllh = 'MPE',
                    If = If
                    )

    tray.AddModule('CramerRao', name + '_' + MPEFitCramerRao + suffix,
                   InputResponse = Pulses,
                   InputTrack = MPEFit+suffix,
                   OutputResult = MPEFitCramerRao+suffix,
                   AllHits = True, # Default
                   DoubleOutput = False, # ! Default
                   z_dependent_scatter = True, # Default
                   If = If,
                   ) 

@icetray.traysegment
def MuEX(tray, name, Pulses = '', Seed = '', If = lambda f: True, suffix = '',
        MuEX = 'MPEFitMuEX',
        ):

    icetray.load('mue', False)

    # Massive changes in MuEX cause signficant changes in the reconstructed
    # energy distribution respect previous years (< 2015). Therefore, MuEX is
    # used in its compatibility mode that mimics the old behavior. Further
    # investigations are needed.
    tray.AddModule( 'muex', name + '_' + MuEX + suffix,
                    compat = False, # ! Compatibility mode
                    energy = True,
                    pulses = Pulses,  # ! Name of pulses (multi-pulses per DOM)
                    rectrk = Seed, # ! Name of Reconstruction seed used for energy reco
                    result = MuEX+suffix, # ! Name output particle
                    detail = False, # Default
                    lcspan = 0, # Default
                    If = If,
                    )

# nk: copied from l2_muon_2012_CommonVariables.py  
from icecube.common_variables import hit_multiplicity, hit_statistics, track_characteristics, direct_hits
@icetray.traysegment
def add_hit_verification_info_muon_and_wimp(tray, name, pulses = '', If = lambda f: True,
    OutputI3HitMultiplicityValuesName= '',
    OutputI3HitStatisticsValuesName= '',
    suffix='',
):
    """Adds hit information to the frame for verification purposes.
    """
    tray.AddModule(hit_multiplicity.I3HitMultiplicityCalculator, 'I3HitMultiplicityCalculator_'+name,   
        If= If,
        PulseSeriesMapName                     = pulses,
        OutputI3HitMultiplicityValuesName = OutputI3HitMultiplicityValuesName,
    )
    tray.AddModule(hit_statistics.I3HitStatisticsCalculator, 'I3HitStatisticsCalculator_'+name,
        If = If,
        PulseSeriesMapName                    = pulses,
        OutputI3HitStatisticsValuesName = OutputI3HitStatisticsValuesName,
    )

    track_cylinder_radius = 150

    tray.AddSegment(track_characteristics.I3TrackCharacteristicsCalculatorSegment, 'tc_spe2',
        If = If,
        PulseSeriesMapName                     = pulses,
        ParticleName                           = 'SPEFit2'+suffix,
        OutputI3TrackCharacteristicsValuesName = "SPEFit2"+suffix+'Characteristics',
        TrackCylinderRadius                    = track_cylinder_radius,
        BookIt                                 = True
    )


@icetray.traysegment
def add_hit_verification_info_muon_only(tray, name, pulses = '', If = lambda f: True,
    suffix='',
):
    track_cylinder_radius = 150

    tray.AddSegment(track_characteristics.I3TrackCharacteristicsCalculatorSegment, 'tc_mpe',
        If = If,
        PulseSeriesMapName                     = pulses,
        ParticleName                           = 'MPEFit'+suffix,
        OutputI3TrackCharacteristicsValuesName = 'MPEFit'+suffix+'Characteristics',
        TrackCylinderRadius                    = track_cylinder_radius,
        BookIt                                 = True
    )



@icetray.traysegment
def OfflineMuonReco ( tray, name, Pulses = '', If = lambda f: True, suffix = ''):

    tray.AddSegment(SPE, name+'SPE'+suffix, 
                     If = If, #Includes every wg events listed in process.py when OfflineMuonReco is called
                     Pulses = Pulses,
                     suffix = suffix,
                     LineFit = 'LineFit',
                     SPEFitSingle = 'SPEFitSingle',
                     SPEFit = 'SPEFit2',
                     SPEFitCramerRao = 'SPEFit2CramerRao',
                     N_iter = 2)


    tray.AddSegment(MPE, name+'MPE'+suffix, 
		     Pulses = Pulses, 
		     Seed = 'SPEFit2', 
		     If = which_split(split_name='InIceSplit') & (lambda f:muon_wg(f)), 
		     suffix = suffix,
                     MPEFit = 'MPEFit',
                     MPEFitCramerRao = 'MPEFitCramerRao')

    tray.AddSegment(MuEX, name+'MuEX'+suffix, 
		     Pulses = Pulses, 
		     Seed = 'MPEFit', 
		     If = which_split(split_name='InIceSplit') & (lambda f:muon_wg(f)), 
		     suffix = suffix, 
		     MuEX = 'MPEFitMuEX')

    # this is for FSS only
    tray.AddSegment(MuEX, name+'MuEX_FSS', 
		     Pulses = Pulses, 
		     Seed = 'SPEFit2', 
		     If = which_split(split_name='InIceSplit') & (lambda f: fss_wg_energy_reco(f)),
		     suffix = '_FSS', 
		     MuEX = 'SPEFit2MuEX')

    tray.AddSegment(add_hit_verification_info_muon_and_wimp, name+'CommonVariablesMuonAndWimp',
                     Pulses= Pulses, 
                     If = which_split(split_name='InIceSplit') & (lambda f:muon_wg(f) or wimp_wg(f)),
                     OutputI3HitMultiplicityValuesName=  "CVMultiplicity",
                     OutputI3HitStatisticsValuesName= "CVStatistics",
                     suffix = suffix)

    tray.AddSegment(add_hit_verification_info_muon_only, name+'CommonVariablesMuonOnly',
                    Pulses= Pulses, 
                    If = which_split(split_name='InIceSplit') & (lambda f: muon_wg(f)),
                    suffix = suffix)

