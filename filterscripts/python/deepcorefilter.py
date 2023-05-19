from icecube import icetray
from icecube.filterscripts import filter_globals

# 2013 DeepCoreFilter segment
# James Pepper <japepper@crimson.ua.edu>

@icetray.traysegment
def DeepCoreFilter(tray, name, pulses, seededRTConfig, If=lambda f: True):

    from icecube import dataclasses, DeepCore_Filter, STTools, DomTools
    # Import DeepCore string/DOM definitions
    from icecube.DeepCore_Filter import DOMS
    
    def deep_core_trigger_check(frame):
        if frame.Has(filter_globals.deepcoresmttriggered) and \
          frame.Stop == icetray.I3Frame.Physics:
            deep_core_bool = frame.Get(filter_globals.deepcoresmttriggered)
            return deep_core_bool.value
        else:
            return 0
   

    def twolayer_deep_core_trigger_check(frame):
        if (frame.Has(filter_globals.deepcoresmttriggered) or \
            frame.Has(filter_globals.inicesmttriggered) or \
            frame.Has(filter_globals.volumetrigtriggered)) and \
            frame.Stop == icetray.I3Frame.Physics:
            return (frame[filter_globals.deepcoresmttriggered].value or \
                    frame[filter_globals.inicesmttriggered].value or \
                    frame[filter_globals.volumetrigtriggered].value)
        else:
            return 0    

    # Perform SeededRT using HLC instead of HLCCore.
    tray.AddModule('I3SeededRTCleaning_RecoPulseMask_Module', name + 'SeededRT',
                   InputHitSeriesMapName  = pulses,
                   OutputHitSeriesMapName = pulses+'SRT',
                   STConfigService        = seededRTConfig,
                   SeedProcedure          = 'AllHLCHits',
                   MaxNIterations         = -1,
                   Streams                = [icetray.I3Frame.Physics],
                   If = lambda f: If(f) and twolayer_deep_core_trigger_check(f)
    )        
    
    dlist = DOMS.DOMS("IC86EDC")
    tldlist = DOMS.DOMS("IC86TwoLayVeto")
    
    tray.AddModule("I3OMSelection<I3RecoPulseSeries>",name+'selectICVetoDOMS',
                   OmittedKeys = dlist.DeepCoreVetoDOMs,
                   OutputOMSelection = 'GoodSelection_ICVeto',
                   InputResponse = pulses+'SRT',
                   OutputResponse = 'SRTPulseICVeto',
                   SelectInverse = True,
                   If = lambda f: If(f) and deep_core_trigger_check(f)
                   )

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>",name+'selectDCFidDOMs',
                   OmittedKeys= dlist.DeepCoreFiducialDOMs,
                   SelectInverse = True,
                   InputResponse = pulses+'SRT',
                   OutputResponse = 'SRTPulseDCFid',
                   OutputOMSelection = 'GoodSelection_DCFid',
                   If = lambda f: If(f) and deep_core_trigger_check(f)
                   )

    tray.AddModule("I3DeepCoreVeto<I3RecoPulse>",name+'deepcore_filter',
                   ChargeWeightCoG = False,
                   DecisionName = 'DeepCore_Filter_Bool_2013',
                   FirstHitOnly = True,
                   InputFiducialHitSeries = 'SRTPulseDCFid',
                   InputVetoHitSeries = 'SRTPulseICVeto',
                   If = lambda f: If(f) and deep_core_trigger_check(f)
                   )

    tray.AddModule("I3FilterModule<I3BoolFilter>",name+"DeepCoreFilter",
                   DecisionName = filter_globals.DeepCoreFilter ,
                   DiscardEvents = False,
                   Boolkey = "DeepCore_Filter_Bool_2013",
                   TriggerEvalList = [filter_globals.deepcoresmttriggered],
                   If = lambda f: If(f) and deep_core_trigger_check(f)
                   )
                   
    ### TwoLayer DeepCore Filter ###
    
    tray.AddModule("I3LCPulseCleaning","I3LCCleaning_Pulses_TLDCV",
                   If = lambda f: If(f) and twolayer_deep_core_trigger_check(f),
                   Input = filter_globals.SplitUncleanedInIcePulses,
                   OutputHLC = "InIcePulses_HLC",
                   OutputSLC = "InIcePulses_SLC"
                   )

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>",'FiducialHLCRequirement',
                   If = lambda f: If(f) and twolayer_deep_core_trigger_check(f),
                   OmittedKeys=tldlist.DeepCoreFiducialDOMs,
                   SelectInverse = True,
                   InputResponse = "InIcePulses_HLC",
                   OutputResponse = 'HLC_DCFID',
                   OutputOMSelection = 'HLC_DCFIDSelection',
                   )


    def FiducialTrig(frame):
      if If(frame) and twolayer_deep_core_trigger_check(frame):
        if not deep_core_trigger_check(frame):
          return len(frame['HLC_DCFID'])>3
        else:
          return True
      else:
        return False

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>",name+'selectTwoLayICVetoDOMS',
                   OmittedKeys = tldlist.DeepCoreVetoDOMs,   
                   OutputOMSelection = 'GoodSelection_TwoLayICVeto',
                   InputResponse = pulses+'SRT',
                   OutputResponse = 'TwoLaySRTPulseICVeto',
                   SelectInverse = True,
                   If = lambda f: If(f) and FiducialTrig(f)
                   )

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>",name+'selectTwoLayDCFidDOMs',
                   OmittedKeys= tldlist.DeepCoreFiducialDOMs,
                   SelectInverse = True,
                   InputResponse = pulses+'SRT',
                   OutputResponse = 'TwoLaySRTPulseDCFid',
                   OutputOMSelection = 'GoodSelection_TwoLayDCFid',
                   If = lambda f: If(f) and FiducialTrig(f)
                   )

    tray.AddModule("I3DeepCoreVeto<I3RecoPulse>",name+'twolaydeepcore_filter',
                   ChargeWeightCoG = False,
                   DecisionName = 'TwoLayerVetoDecision',
                   FirstHitOnly = True,
                   InputFiducialHitSeries = 'TwoLaySRTPulseDCFid',
                   InputVetoHitSeries = 'TwoLaySRTPulseICVeto',
                   If = lambda f: If(f) and FiducialTrig(f)
                   )

#    tray.AddModule("I3FilterModule<I3BoolFilter>",name+"TwoLayerDeepCoreFilter",
#                   DecisionName = filter_globals.DeepCoreFilter_TwoLayerBranch,
#                   DiscardEvents = False,
#                   Boolkey = "TwoLayerVetoDecision",
#                   TriggerEvalList = [filter_globals.deepcoresmttriggered,
#                                      filter_globals.volumetrigtriggered,
#                                      filter_globals.inicesmttriggered],
#                   If = lambda f: If(f) and FiducialTrig(f)
#        )

    tray.AddModule("Delete",'dumpleftovers',
                   Keys=['DeepCore_Filter_Bool_2013',
                         'GoodSelection_ICVeto',
                         'GoodSelection_DCFid',
                         'SRTPulseDCFid',
                         'SRTPulseDCFidCleanedKeys',
                         'SRTPulseICVeto',
                         'SRTPulseICVetoCleanedKeys'],
                   If = lambda f: If(f) and deep_core_trigger_check(f)
                   )

    tray.AddModule("Delete",'dump_TLV_leftovers',
                   Keys=['TwoLaySRTPulseICVetoCleanedKeys',
                         'GoodSelection_TwoLayDCFid',
                         'GoodSelection_TwoLayICVeto',
                         'InIcePulses_SLC',
                         'HLC_DCFID',
                         'HLC_DCFIDCleanedKeys',
                         'HLC_DCFIDSelection',
                         'InIcePulses_HLC',
                         'TwoLaySRTPulseDCFidCleanedKeys',
                         'TwoLaySRTPulseDCFid',
                         'TwoLaySRTPulseICVeto',
                         'SplitUncleanedInIcePulsesSRT',
                         'TwoLayerVetoDecision'],
                   If = lambda f: If(f) and twolayer_deep_core_trigger_check(f) 
                   )
