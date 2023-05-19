from icecube import icetray
from icecube.icetray import OMKey, I3Units
## Import the 2.4 compatibility helpers for SPS/SPTS python
from icecube.icetray.pycompat import *

from icecube.filterscripts import filter_globals

@icetray.traysegment
def BaseProcessing(tray, name, pulses='MuonPulseSeriesReco',
                   decode=False, simulation = False,
                   needs_calibration=True, needs_superdst=True,
                   needs_maskmaker=True, needs_trimmer=True,
                   needs_wavedeform_spe_corr = True,
                   do_slop = True,
                   llh_name = filter_globals.muon_llhfit,
                   linefit_name = filter_globals.muon_linefit,
                   seededRTConfig=None):
     """
     Decode payloads, calibrate waveforms, extract pulses, and run basic reconstructions.
     """
     # Load dependencies
     from icecube import dataclasses, payload_parsing, lilliput
     from icecube import linefit, STTools, topeventcleaning
     from icecube.common_variables import direct_hits
     from icecube.common_variables import hit_multiplicity

     import icecube.lilliput.segments
     
     icetray.load("filterscripts",False)
     icetray.load("DomTools", False)
     icetray.load("trigger-splitter", False)
     icetray.load("linefit", False)
     icetray.load("mue", False)

     ##
     ##  Import some of the worker segments, in own files to reduce clutter
     ##
     from icecube.filterscripts.baseproc_onlinecalibration import OnlineCalibration
     from icecube.filterscripts.baseproc_onlinecalibration import DOMCleaning
     from icecube.filterscripts.baseproc_daqtrimmer import DAQTrimmer
     from icecube.filterscripts.baseproc_daqtrimmer import SimTrimmer
     from icecube.filterscripts.baseproc_superdst import SuperDST
     from icecube.filterscripts.baseproc_superdst import Unify, MaskMaker
     from icecube.filterscripts.topological_splitter import TopologicalSplitting
     from icecube.phys_services.which_split import which_split
     from icecube.filterscripts.slopfilter import SLOPSplitter
     from icecube.filterscripts.flaringDOMFilter import FlaringDOMFilter


     # Raw Data
     # If needded will decode I3DAQData to IceTopRawData, InIceRawData
     #         I3EventHeader, I3TriggerHierarchy 
     if decode:
          tray.AddSegment(payload_parsing.I3DOMLaunchExtractor, 
                          name + '_launches',
			  MinBiasID = 'MinBias',
			  FlasherDataID = 'Flasher',
                          CPUDataID = "BeaconHits",
                          SpecialDataID = "SpecialHits",
                          ## location of scintillators and IceACT
                          SpecialDataOMs = [OMKey(0,1),
                                            OMKey(12,65),
                                            OMKey(12,66),
                                            OMKey(62,65),
                                            OMKey(62,66)],
			  )
     def MissingITCheck(frame):
	     if "IceTopRawData" not in frame:
		     itrd = dataclasses.I3DOMLaunchSeriesMap()
		     frame["IceTopRawData"] = itrd
     if simulation:
	     tray.AddModule(MissingITCheck,name +'_AddIceTopPulses',
			    Streams=[icetray.I3Frame.DAQ])

     tray.AddSegment(DOMCleaning, name + '_DOMCleaning')
     if needs_calibration:
        tray.AddSegment(OnlineCalibration, name + '_Calibration', 
                        simulation = simulation, WavedeformSPECorrections = needs_wavedeform_spe_corr,
                        Harvesting = filter_globals.do_harvesting)

     if needs_superdst:
        tray.AddSegment(SuperDST, name + '_SuperDST',
                        InIcePulses=filter_globals.UncleanedInIcePulses, 
                        IceTopPulses='IceTopPulses',
                        Output = filter_globals.DSTPulses
                        )
     DAQ = [icetray.I3Frame.DAQ]
     if needs_maskmaker:
        # Set up masks for normal access
        tray.AddModule(MaskMaker, name + '_superdst_aliases',
                       Output = filter_globals.DSTPulses,
                       Streams=DAQ
                       )

     if needs_trimmer:
        if not simulation:
            tray.AddSegment(DAQTrimmer, name +'_DAQTrimmer')
        else:
            tray.AddSegment(SimTrimmer, name +'_SimTrimmer')

     # call the trigger something else for the Q frame
     tray.AddModule("Rename", name + '_trigrename', 
                    keys=[filter_globals.triggerhierarchy,
			  filter_globals.qtriggerhierarchy]
                    )

     # I3TriggerSplitter.  
     #  This is a splitter module Q-> P frames based on triggers
     #   in the I3TriggerHierarchy.  It splits looking for 
     #   'quiet' times between triggers
     # Params:  Take input triggerHeirarchy in Q frame: QTriggerHierarchy
     #   results in an 'I3TriggerHierarchy' in each P frame.
     #   input pulses come from wavedeform:  WavedeformPulses
     #   output pulses in frame as WavedeformSplitPulses in P frame (as mask)
     # Note:  the Instance name matters, it's the name of the substream

     # Note: 2 inice splitters below, only 1 can be active

     ###
     # Standard InIce splitter from 2014
     ##
     tray.AddModule('I3TriggerSplitter',name + '_' + filter_globals.InIceSplitter,
                    SubEventStreamName=filter_globals.InIceSplitter,
                    TrigHierName=filter_globals.qtriggerhierarchy,
     		    # Note: taking the SuperDST pulses
     		            TriggerConfigIDs = [filter_globals.deepcoreconfigid,
                                        filter_globals.inicesmtconfigid,
                                        filter_globals.inicestringconfigid,
                                        filter_globals.volumetriggerconfigid,
                                        filter_globals.faintparticleconfigid],
                    InputResponses=[filter_globals.InIceDSTPulses],
                    OutputResponses=[filter_globals.SplitUncleanedInIcePulses],
     		    WriteTimeWindow = True  # Needed for EHE
     )

     
     #IceTop Splitting and reco
     tray.AddModule('I3TankPulseMerger', 'IceTopTankPulseMerger_HLC',
                     InputVEMPulses   = 'IceTopHLCVEMPulses',
                     OutputTankPulses = filter_globals.HLCTankPulses,
                     BadTankList   = filter_globals.IcetopBadTanks,
                     BadDomList = filter_globals.IceTopBadDoms,
                     ExcludedTanks = filter_globals.TankPulseMergerExcludedTanks,
                     MaxHGLGTimeDiff  = 40.0 * I3Units.ns,               # Default
                     If               = lambda frame: filter_globals.IceTopPulses_HLC in frame
                   )

     tray.AddModule('I3TankPulseMerger', 'IceTopTankPulseMerger_SLC',
                     InputVEMPulses   = 'IceTopSLCVEMPulses',
                     OutputTankPulses = filter_globals.SLCTankPulses,
                     BadTankList   = filter_globals.IcetopBadTanks,
                     BadDomList = filter_globals.IceTopBadDoms,
                     ExcludedTanks = 'TankPulseMergerExcludedTanksSLC',
                     MaxHGLGTimeDiff  = 40.0 * I3Units.ns,               # Default
                     If               = lambda frame: filter_globals.IceTopPulses_SLC in frame
                   )

     tray.AddModule('I3TopHLCClusterCleaning', name + '_' + filter_globals.IceTopSplitter,
                     SubEventStreamName        = filter_globals.IceTopSplitter,
                     InputPulses               = filter_globals.HLCTankPulses,
                     OutputPulses              = filter_globals.CleanedHLCTankPulses,
                     BadTankList               = filter_globals.TankPulseMergerExcludedTanks,
                     ExcludedTanks             = filter_globals.ClusterCleaningExcludedTanks,
                     InterStationTimeTolerance = 200.0 * I3Units.ns,              # Default
                     IntraStationTimeTolerance = 200.0 * I3Units.ns,              # Default
                     If                        = lambda frame: filter_globals.IceTopPulses_HLC in frame
                   )
     #####
     ## SLOP Splitter.  Give the SLOP guys a P frame...
     if do_slop:
         tray.AddSegment(SLOPSplitter, filter_globals.SLOPSplitter,
                         InputPulses=filter_globals.InIceDSTPulses)

     ##
     ## Null split -> filter_globals.NullSplitter
     ##  Used by min bias filters (2013)
     tray.AddModule("I3NullSplitter", filter_globals.NullSplitter,
                    SubEventStreamName=filter_globals.NullSplitter)

     class PhysicsCopyTriggers(icetray.I3ConditionalModule):
	     from icecube import dataclasses
	     def __init__(self, context):
		     icetray.I3ConditionalModule.__init__(self, context)
		     self.AddOutBox("OutBox")
	     def Configure(self):
		     pass
	     def Physics(self, frame):
		     if frame.Has(filter_globals.qtriggerhierarchy):
			     myth = frame.Get(filter_globals.qtriggerhierarchy)
			     if frame.Has(filter_globals.triggerhierarchy):
				     print("ERROR:  PhysicsCopyTriggers: triggers in frame, already run??")
			     else:
				     frame.Put(filter_globals.triggerhierarchy, myth)
		     else:
			     print("Error:  PhysicsCopyTriggers: Missing QTriggerHierarchy input")
		     self.PushFrame(frame)

     # Null split and IceTop split need the triggerHeirarchy put back in P frame

     tray.AddModule(PhysicsCopyTriggers,name + '_IceTopTrigCopy',
		    If = which_split(split_name=filter_globals.IceTopSplitter) 
		    )

     tray.AddModule(PhysicsCopyTriggers,name + '_nullTrigCopy',
		    If = which_split(split_name=filter_globals.NullSplitter) 
		    )

     # TriggerCheck module:  handles the complexity of the IceCube
     #  trigger system (Source,TriggerID,ConfigID, and boils things down
     #  to a set of I3Bool in the frame for easy reference.
     #      InIceSMTFlag -> True if the SMT 8 trigger fired
     #      DeepCoreSMTFlag -> True if the DeepCore SMT trigger fired
     #      etc....
     #  These are used later by individual filters that want to 
     #    select on specific triggers.
     # will run on ALL splits.
     tray.AddModule("TriggerCheck_13",name + "_Trigchecker",
		    I3TriggerHierarchy=filter_globals.triggerhierarchy,
		    InIceSMTFlag=filter_globals.inicesmttriggered,
		    IceTopSMTFlag=filter_globals.icetopsmttriggered,
		    InIceStringFlag=filter_globals.inicestringtriggered,
		    DeepCoreSMTFlag=filter_globals.deepcoresmttriggered,
		    DeepCoreSMTConfigID=filter_globals.deepcoreconfigid,
		    VolumeTriggerFlag=filter_globals.volumetrigtriggered,
		    SlowParticleFlag=filter_globals.slowparticletriggered,
		    FaintParticleFlag=filter_globals.faintparticletriggered,
		    FixedRateTriggerFlag=filter_globals.fixedratetriggered,
                    ScintMinBiasTriggerFlag=filter_globals.scintminbiastriggered,
                    IceTopVolumeTriggerFlag=filter_globals.icetopvolumetriggered,
                    ScintMinBiasConfigID=filter_globals.scintminbiasconfigid,
                    IceActSMTConfigID =filter_globals.iceactsmtconfigid
		    )


     # SeededRT is usually a good option before recos.
     # These are the settings from last season, only the non-standard 
     # settings are specified.  
     # Input pulses = WavedeformSplitPulses
     # Output pulses is the 'pulses' argument. Will be used by recos, etc.
     # InIce Split only
     tray.AddModule('I3SeededRTCleaning_RecoPulseMask_Module', name + '_seededrt',
            InputHitSeriesMapName  = filter_globals.SplitUncleanedInIcePulses,
            OutputHitSeriesMapName = filter_globals.SplitRTCleanedInIcePulses,
            STConfigService        = seededRTConfig,
            SeedProcedure          = 'HLCCoreHits',
            NHitsThreshold         = 2,
            MaxNIterations         = 3,
            Streams                = [icetray.I3Frame.Physics],
            If = which_split(split_name=filter_globals.InIceSplitter)
     )

     #  TimeWindowCleaning - select the window (6 usec) with best number
     #      of hits.
     tray.AddModule("I3TimeWindowCleaning<I3RecoPulse>", "TimeWindowCleaning",
		    InputResponse = filter_globals.SplitRTCleanedInIcePulses,
		    OutputResponse = pulses,
		    TimeWindow = 6000*I3Units.ns,
		    If = which_split(split_name=filter_globals.InIceSplitter)
		    )

     #
     # Flary DOM checker, will alert I3Live when they're found
     #
     tray.AddModule(FlaringDOMFilter, name + '_flaringDomCheck',
                    pulsesName = pulses,
                    errataName = 'LIDErrata',
                    #maxNonCausalHits=6, minChargeFraction=0.2, ## for testing
		    If = which_split(split_name=filter_globals.InIceSplitter)
                    )


     tray.AddSegment(linefit.simple, name + "_imprv_LF", 
		     inputResponse= pulses, 
		     fitName = linefit_name,
		     If = which_split(split_name=filter_globals.InIceSplitter)
		     )
     
     ## Muon LLH SimpleFitter from GulliverSuite with LineFit seed.
     #  uses the seededrtcleaned pulses
     tray.AddSegment(lilliput.segments.I3SinglePandelFitter, llh_name,
                     seeds   = [linefit_name],
                     pulses  = pulses,
                     fitname = llh_name,
		     If = which_split(split_name=filter_globals.InIceSplitter)
                     )

     # CutsModule
     tray.AddModule("I3FirstPulsifier", name+"_first-pulsify",
		    InputPulseSeriesMapName = pulses,
		    OutputPulseSeriesMapName = 'FirstPulseMuonPulses',
		    KeepOnlyFirstCharge = False,   # default
		    UseMask = False,               # default
		    If = which_split(split_name=filter_globals.InIceSplitter)
            )
     
     ##Common Variables
     dh_defs = direct_hits.get_default_definitions()
     tray.AddSegment(direct_hits.I3DirectHitsCalculatorSegment, name + '_directhits',
		     DirectHitsDefinitionSeries       = dh_defs,
		     PulseSeriesMapName               = 'FirstPulseMuonPulses',
		     ParticleName                     = llh_name,
		     OutputI3DirectHitsValuesBaseName = llh_name+'DirectHitsBase',
		     BookIt                           = False,
		     If = which_split(split_name=filter_globals.InIceSplitter)
		     )

     tray.AddSegment(hit_multiplicity.I3HitMultiplicityCalculatorSegment, name + '_hitmultiplicity',
		     PulseSeriesMapName                = 'FirstPulseMuonPulses',
		     OutputI3HitMultiplicityValuesName = 'MuonPulsesHitMultiplicityBase',
		     BookIt                            = False,
		     If = which_split(split_name=filter_globals.InIceSplitter)
		     )

     # Mue Calculation, used by DST module  Same settings as 2011/IC86
     tray.AddModule("I3mue", name + '_mue',
                    RecoPulseSeriesNames = [pulses],
                    RecoResult = llh_name,
                    RecoIntr = 1,
                    OutputParticle = llh_name + 'MuE',
		    If = which_split(split_name=filter_globals.InIceSplitter)
		    )
