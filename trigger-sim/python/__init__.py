from icecube.load_pybindings import load_pybindings
load_pybindings(__name__, __path__)

from icecube import icetray, dataclasses
from icecube.trigger_sim.InjectDefaultDOMSets import InjectDefaultDOMSets

@icetray.traysegment
def TriggerSim(tray,
               name,
               gcd_file,
               run_id = None,
               prune = True,
               time_shift = True,
               time_shift_args = dict(),
               filter_mode = True ):
    """
    Configure triggers according to the GCD file.

    NB: This segment no longer supports the ULEE trigger, so now only
    IC59 and later configurations.
    
    Parameters:

    * tray - Standard for segments.
    * name - Standard for segments.
    * gcd_file - The GCD (I3File) that contains the trigger configuration.
      Note the segment figures out from the GCD file which trigger
      modules need to be loaded and configures them accordingly. 
    * prune - Whether to remove launches outside the readout windows.
      Nearly everyone will want to keep this set at True.  It makes
      simulation look more like data.
    * time_shift - Whether to time shift time-like frame objects.
      Nearly everyone will want to keep this set at True.
      It makes simulation look more like data.
    * time_shift_args - dict that's forwarded to the I3TimeShifter module.
    * filter_mode - Whether to filter frames that do not trigger.    

    This ignores AMANDA triggers and only supports the following modules:

    * SimpleMajorityTrigger
    * ClusterTrigger
    * CylinderTrigger
    * SlowMonopoleTrigger

    This segment also includes the I3GlobalTriggerSim as well as the
    I3Pruner and I3TimeShifter.  Its job is to make simulation look
    like data that the pole filters get.
    """

    if run_id == None :
        icetray.logging.log_fatal("You have to set run_id to a valid number.")

    from icecube.trigger_sim.modules.time_shifter import I3TimeShifter

    # get the trigger status
    fr = gcd_file.pop_frame()
    while "I3DetectorStatus" not in fr :
        fr = gcd_file.pop_frame()
    tsmap = fr.Get("I3DetectorStatus").trigger_status

    # loop through the trigger status map and configure what we can
    # we still need to do this for STRING and SIMPLE_MULTIPLICITY
    # triggers since there can be multiple trigger configurations
    # of this type.  With the smarter trigger-sim modules we *only*
    # need to specify the configID though since that's unique for
    # each trigger.
    key_to_module = {dataclasses.SIMPLE_MULTIPLICITY : "SimpleMajorityTrigger" ,
                         dataclasses.STRING : "ClusterTrigger",
                         dataclasses.VOLUME : "CylinderTrigger",
                         dataclasses.SLOW_PARTICLE : "SlowMonopoleTrigger",
                         dataclasses.FAINT_PARTICLE : "FaintParticleTrigger"}
                        
    for tkey, ts in tsmap :
        # skip any triggers we don't have simulation modules for
        if (tkey.source != dataclasses.IN_ICE and \
          tkey.source != dataclasses.ICE_TOP) or\
           tkey.type not in key_to_module:
            continue
        
        # If we find a ULEE configuration in the GCD file
        # alert the user that this is no longer supported.
        if tkey.type == dataclasses.STRING :
            if "maxLength" in ts.trigger_settings and \
              "multiplicity" in ts.trigger_settings and \
              "string" in ts.trigger_settings and \
              "timeWindow" in ts.trigger_settings :
                icetray.logging.log_warn("ULEE found in GCD but is no longer supported.")            
                continue

        # Load the appropriate module with its TriggerConfigID.  All trigger
        # modules should be able to configure themselves solely from the
        # trigger config ID.
        tray.Add(key_to_module[tkey.type], TriggerConfigID = tkey.config_id)

    tray.AddModule("I3GlobalTriggerSim",name + "_global_trig",
                   RunID = run_id,
                   FilterMode = filter_mode)
    if prune :
        tray.AddModule("I3Pruner")

    if time_shift :
        tray.AddModule(I3TimeShifter, **time_shift_args)
                       
