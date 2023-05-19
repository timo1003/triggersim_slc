/**
 * copyright  (C) 2008
 * the IceCube collaboration
 * Version $Id: $
 * @author: Redl
 */


#ifndef JEBFILTER_TRIGGERCHECK13_H_INCLUDED
#define JEBFILTER_TRIGGERCHECK13_H_INCLUDED

#include <icetray/I3Module.h>
#include <icetray/OMKey.h>
#include <dataclasses/physics/I3Trigger.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>

class TriggerCheck_13 : public I3Module
{
 public:
  TriggerCheck_13(const I3Context& context);

  void Configure();

  void Physics(I3FramePtr frame);

  std::string I3TriggerHierarchy_;
  std::string inice_smt_bool_;
  std::string icetop_smt_bool_;
  std::string deepcore_smt_bool_;
  std::string inice_string_bool_;
  std::string physics_min_bias_bool_;
  std::string volume_trigger_bool_;
  std::string slow_particle_bool_;
  std::string faint_particle_bool_;
  std::string fixed_rate_trigger_bool_;
  std::string scint_min_bias_bool_;
  std::string icetop_volume_bool_;
  std::string iceact_smt_bool_;
  unsigned int physics_min_bias_confid_;
  unsigned int deepcore_smt_confid_;
  unsigned int scint_min_bias_config_;
  unsigned int iceact_smt_config_;
};

#endif
