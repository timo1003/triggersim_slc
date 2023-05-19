/**
 * copyright  (C) 2008
 * the IceCube collaboration
 * Version $Id: $
 * @author: Blaufuss
 */


#ifndef JEBFILTER_TRIGGERREDUCER_H_INCLUDED
#define JEBFILTER_TRIGGERREDUCER_H_INCLUDED

#include <icetray/I3ConditionalModule.h>
#include "icetray/I3Tray.h"
#include <dataclasses/physics/I3Trigger.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>

class TriggerReducer : public I3ConditionalModule
{
 public:
  TriggerReducer(const I3Context& context);
  ~TriggerReducer() { }

  void Configure();
  
  void Physics(I3FramePtr frame);
  
 private:
  std::string I3TriggerHierarchy_;
  std::string OutTriggerHierarchy_;
  std::vector<int> match_keys_;

};
#endif
