/**
 * copyright  (C) 2008
 * the IceCube collaboration
 * Version $Id: $
 * Author: Redl
 */


#include "filterscripts/TriggerCheck_13.h"

#include <icetray/I3Bool.h>
#include <dataclasses/TriggerKey.h>
#include <dataclasses/physics/I3Trigger.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>
#include <icetray/I3Frame.h>

I3_MODULE(TriggerCheck_13);

using namespace I3TriggerHierarchyUtils;

TriggerCheck_13::TriggerCheck_13(const I3Context& context) 
  : I3Module(context),
    I3TriggerHierarchy_("I3TriggerHierarchy"),
    inice_smt_bool_("InIceSMTTriggered"),
    icetop_smt_bool_("IceTopSMTTriggered"),
    deepcore_smt_bool_("DeepCoreSMTTriggered"),
    inice_string_bool_("InIceStringTriggered"),
    physics_min_bias_bool_("PhysMinBiasTriggered"),
    volume_trigger_bool_("VolumeTrigTriggered"),
    slow_particle_bool_("SlowParticleTriggered"),
    faint_particle_bool_("FaintParticleTriggered"),
    fixed_rate_trigger_bool_("FixedRateTriggered"),
    scint_min_bias_bool_("ScintMinBiasTriggered"),
    icetop_volume_bool_("IceTopVolumeTriggered"),
    iceact_smt_bool_("IceActSMTTriggered")
    
{
  AddOutBox("OutBox");

  AddParameter("I3TriggerHierarchy",
	       "Name of I3TriggerHierarchy in ze frame",
	       I3TriggerHierarchy_);
  AddParameter("InIceSMTFlag",
	       "Name of bool to use when IN_ICE::SMT Trigger present",
	       inice_smt_bool_);
  AddParameter("IceTopSMTFlag",
	       "Name of bool to use when ICE_TOP::SMT Trigger present",
	       icetop_smt_bool_);
  AddParameter("DeepCoreSMTFlag",
	       "Name of bool to use when IN_ICE::SMT DeepCore Trigger present",
	       deepcore_smt_bool_);
  AddParameter("InIceStringFlag",
	       "Name of bool to use when IN_ICE::String Trigger present",
	       inice_string_bool_);
  AddParameter("PhysMinBiasFlag",
	       "Name of bool to use when IN_ICE::MinBias (PhysMinBias) Trigger present",
	       physics_min_bias_bool_);
  AddParameter("VolumeTriggerFlag",
	       "Name of bool to use when IN_ICE::VOLUME Trigger present",
	       volume_trigger_bool_);
  AddParameter("SlowParticleFlag",
  	       "Name of bool to use when IN_ICE::SLOW_PARTICLE Trigger present",
  	       slow_particle_bool_);
  AddParameter("FaintParticleFlag",
  	       "Name of bool to use when IN_ICE::FAINT_PARTICLE Trigger present",
  	       faint_particle_bool_);
  AddParameter("FixedRateTriggerFlag",
  	       "Name of bool to use when IN_ICE::UNBIASED Trigger present",
  	       fixed_rate_trigger_bool_);
  AddParameter("ScintMinBiasTriggerFlag",
  	       "Name of bool to use when IN_Top::MinBias Scintillator Trigger present",
  	       scint_min_bias_bool_);
  AddParameter("IceActSMTTriggerFlag",
  	       "Name of bool to use when IceTop::SMT IceAct MB Trigger is present",
  	       iceact_smt_bool_);
  AddParameter("IceTopVolumeTriggerFlag",
  	       "Name of bool to use when IN_Top::Volume (2 station trigger) Trigger present",
  	       icetop_volume_bool_);
  physics_min_bias_confid_ = 99999;
  AddParameter("PhysMinBiasConfigID",
	       "The config ID used for PhysicsMinBias Trigger events",
	       physics_min_bias_confid_);
  deepcore_smt_confid_ = 99999;
  AddParameter("DeepCoreSMTConfigID",
	       "The config ID used for DeepCore SMT Trigger events",
	       deepcore_smt_confid_);
  scint_min_bias_config_ = 99999;
  AddParameter("ScintMinBiasConfigID",
	       "The config ID used for IceTop Min Bias Scintillator Trigger events",
	       scint_min_bias_config_);
  iceact_smt_config_ = 99999;
  AddParameter("IceActSMTConfigID",
	       "The config ID used for IceAct SMT MB passthru trigger",
	       iceact_smt_config_);

}

 void TriggerCheck_13::Configure()
{

  GetParameter("I3TriggerHierarchy",
	       I3TriggerHierarchy_);
  GetParameter("InIceSMTFlag",
	       inice_smt_bool_);
  GetParameter("IceTopSMTFlag",
	       icetop_smt_bool_);
  GetParameter("DeepCoreSMTFlag",
	       deepcore_smt_bool_);
  GetParameter("InIceStringFlag",
	       inice_string_bool_);
  GetParameter("PhysMinBiasFlag",
	       physics_min_bias_bool_);
  GetParameter("VolumeTriggerFlag",
	       volume_trigger_bool_);
  GetParameter("SlowParticleFlag",
  	       slow_particle_bool_);
   GetParameter("FaintParticleFlag",
  	       faint_particle_bool_);
  GetParameter("FixedRateTriggerFlag",
  	       fixed_rate_trigger_bool_);
  GetParameter("ScintMinBiasTriggerFlag",
  	       scint_min_bias_bool_);
  GetParameter("IceTopVolumeTriggerFlag",
  	       icetop_volume_bool_);
  GetParameter("IceActSMTTriggerFlag",
	       iceact_smt_bool_);
  GetParameter("PhysMinBiasConfigID",
	       physics_min_bias_confid_);
  GetParameter("DeepCoreSMTConfigID",
	       deepcore_smt_confid_);
  GetParameter("ScintMinBiasConfigID",
	       scint_min_bias_config_);
  GetParameter("IceActSMTConfigID",
	       iceact_smt_config_);
}

void TriggerCheck_13::Physics(I3FramePtr frame)
{
  
  I3TriggerHierarchyConstPtr triggers = 
    frame->Get<I3TriggerHierarchyConstPtr>(I3TriggerHierarchy_);
  
  I3TriggerHierarchy::iterator I3_iter;
  
  if(!triggers)
    {
      //decrement to log_info later
      log_error("No I3TriggerHierarchy found!");
      PushFrame(frame,"OutBox");
      //Give up and take our toys home.
      return;
    }
  // Useful for exploring triggers, not needed for general use.
/**
  for(I3_iter = triggers->begin() ;
      I3_iter != triggers->end() ;
      I3_iter++)
    {
      if(I3_iter->GetTriggerKey().CheckConfigID())
 	{
 	  log_warn("Got trigger %s %s %i",
		   TriggerKey::GetSourceString(I3_iter->GetTriggerKey().GetSource()),
		   TriggerKey::GetTypeString(I3_iter->GetTriggerKey().GetType()),
		   I3_iter->GetTriggerKey().GetConfigID()
		   );
 	}
      else
	{
	  log_warn("Got trigger %s %s NA",
		   TriggerKey::GetSourceString(I3_iter->GetTriggerKey().GetSource()),
      		   TriggerKey::GetTypeString(I3_iter->GetTriggerKey().GetType())
      		   );
      	}
    }
**/

  unsigned int slow_part = Count(*triggers,TriggerKey::IN_ICE,TriggerKey::SLOW_PARTICLE);
  //If the slow particle is setoff, abort all other checks and just flag as SP
  I3BoolPtr SlowPart_boolPtr(new I3Bool(false));
  if (slow_part){
    SlowPart_boolPtr->value = true;
    log_trace("Slow particle TRUE");
  }
    
  unsigned int frt_count = Count(*triggers,TriggerKey::IN_ICE,TriggerKey::UNBIASED);
  I3BoolPtr FRT_boolPtr(new I3Bool(false));
  if (frt_count){
    FRT_boolPtr->value = true;
    log_trace("Fixed rate trigger TRUE");
  }
  
  unsigned int inice_smt = Count(*triggers,TriggerKey::IN_ICE,TriggerKey::SIMPLE_MULTIPLICITY);
  unsigned int icetop_smt = Count(*triggers,TriggerKey::ICE_TOP,TriggerKey::SIMPLE_MULTIPLICITY);
  unsigned int inice_string = Count(*triggers,TriggerKey::IN_ICE,TriggerKey::STRING);  
  unsigned int inice_volume = Count(*triggers,TriggerKey::IN_ICE,TriggerKey::VOLUME);  
  unsigned int icetop_volume = Count(*triggers,TriggerKey::ICE_TOP,TriggerKey::VOLUME);  
  unsigned int faint_part = Count(*triggers,TriggerKey::IN_ICE,TriggerKey::FAINT_PARTICLE);

  log_trace("Found:  IISMT: %i ITSMT: %i, IISTRING: %i\n",
	    inice_smt,icetop_smt,inice_string);


  unsigned int DeepCoreSMT_trigger = Count(*triggers,
					   TriggerKey(TriggerKey::IN_ICE,
						      TriggerKey::SIMPLE_MULTIPLICITY,
						      deepcore_smt_confid_));
			      
  unsigned int PhysMinBias_trigger = Count(*triggers,
					   TriggerKey(TriggerKey::IN_ICE,
						      TriggerKey::MIN_BIAS,
						      physics_min_bias_confid_));

  unsigned int ScintMinBias_trigger = Count(*triggers,
					   TriggerKey(TriggerKey::ICE_TOP,
						      TriggerKey::MIN_BIAS,
						      scint_min_bias_config_));

  unsigned int IceActSMT_trigger = Count(*triggers,
					 TriggerKey(TriggerKey::ICE_TOP,
						    TriggerKey::SIMPLE_MULTIPLICITY,
						    iceact_smt_config_));

  // Subtract DeepCore SMT from generic InIce SMT count, otherwise double counted
  if(DeepCoreSMT_trigger > 0)
    inice_smt = inice_smt - DeepCoreSMT_trigger;
  // Ditto for IceAct SMT
  if(IceActSMT_trigger  > 0)
    icetop_smt = icetop_smt - IceActSMT_trigger;
  
  I3BoolPtr InIceSMT_boolPtr(new I3Bool(false));
  I3BoolPtr IceTopSMT_boolPtr(new I3Bool(false));
  I3BoolPtr InIceString_boolPtr(new I3Bool(false));
  I3BoolPtr VolumeTrig_boolPtr(new I3Bool(false));
  I3BoolPtr PhysMinBias_boolPtr(new I3Bool(false));
  I3BoolPtr DeepCoreSMT_boolPtr(new I3Bool(false));
  I3BoolPtr ScintMinBias_boolPtr(new I3Bool(false));
  I3BoolPtr IceTopVolume_boolPtr(new I3Bool(false));
  I3BoolPtr IceACTSMT_boolPtr(new I3Bool(false));
  I3BoolPtr FaintPart_boolPtr(new I3Bool(false));


  if (inice_smt)
     {
       InIceSMT_boolPtr->value = true;
       log_trace("InIceSMT True");
     }
   frame->Put(inice_smt_bool_, InIceSMT_boolPtr); 
   if (icetop_smt)
     {
       IceTopSMT_boolPtr->value = true;
       log_trace("IceTopSMT True");
     }
   frame->Put(icetop_smt_bool_, IceTopSMT_boolPtr); 
   if (inice_string)
     {
       InIceString_boolPtr->value = true;
       log_trace("InIceString True");
     }
   frame->Put(inice_string_bool_, InIceString_boolPtr); 
   if (inice_volume)
     {
       VolumeTrig_boolPtr->value = true;
       log_trace("VolumeTrig True");
     }
   frame->Put(volume_trigger_bool_, VolumeTrig_boolPtr); 
   if (icetop_volume)
     {
       IceTopVolume_boolPtr->value = true;
       log_trace("IceTop VolumeTrig True");
     }
   frame->Put(icetop_volume_bool_, IceTopVolume_boolPtr); 
   if (PhysMinBias_trigger)
     {
       PhysMinBias_boolPtr->value = true;
       log_trace("PhysMinBias True");
     }
   frame->Put(physics_min_bias_bool_, PhysMinBias_boolPtr);

   if (ScintMinBias_trigger)
     {
       ScintMinBias_boolPtr->value = true;
       log_trace("ScintMinBias True");
     }
   frame->Put(scint_min_bias_bool_, ScintMinBias_boolPtr);

   if (DeepCoreSMT_trigger)
     {
       DeepCoreSMT_boolPtr->value = true;
       log_trace("DeepCore True");
     }
   frame->Put(deepcore_smt_bool_, DeepCoreSMT_boolPtr);
   if (IceActSMT_trigger)
     {
       IceACTSMT_boolPtr->value = true;
       log_trace("IceACTSMT True");
     }
    if (faint_part){
        FaintPart_boolPtr->value = true;
        log_trace("Faint particle TRUE");
      }
   frame->Put(iceact_smt_bool_,IceACTSMT_boolPtr);
   
   frame->Put(slow_particle_bool_, SlowPart_boolPtr); 
   frame->Put(faint_particle_bool_, FaintPart_boolPtr);
   frame->Put(fixed_rate_trigger_bool_, FRT_boolPtr); 

   PushFrame(frame,"OutBox");
}
