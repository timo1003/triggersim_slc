#include "filterscripts/TriggerReducer.h"

#include <dataclasses/TriggerKey.h>
#include <dataclasses/physics/I3Trigger.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>
#include <icetray/I3Frame.h>
#include <vector>
#include <algorithm>

I3_MODULE(TriggerReducer);
using namespace std;

using namespace I3TriggerHierarchyUtils;

TriggerReducer::TriggerReducer(const I3Context& context) 
  : I3ConditionalModule(context),
    I3TriggerHierarchy_("I3TriggerHierarchy"),
    OutTriggerHierarchy_("OutTriggerHierarchy")
{
  AddOutBox("OutBox");
  AddParameter("I3TriggerHierarchy",
	       "Name of I3TriggerHierarchy to take as input from the frame",
	       I3TriggerHierarchy_);
  AddParameter("OutTriggerHierarchy",
	       "Name of I3TriggerHierarchy to ouput to the frame",
	       OutTriggerHierarchy_);
  AddParameter("TriggerConfigIDList",
	      "Vector of Ints, containing the ConfigIDs of triggers to keep",
	      match_keys_);
}

void TriggerReducer::Configure()
{
  GetParameter("I3TriggerHierarchy",
	       I3TriggerHierarchy_);
  GetParameter("OutTriggerHierarchy",
	       OutTriggerHierarchy_);
  GetParameter("TriggerConfigIDList",
	       match_keys_);
  
}

void TriggerReducer::Physics(I3FramePtr frame)
{
  I3TriggerHierarchyConstPtr triggers = 
    frame->Get<I3TriggerHierarchyConstPtr>(I3TriggerHierarchy_);
  
  if(!triggers)
    {
      //decrement to log_info later
      log_debug("No I3TriggerHierarchy found!  Carry on");
      PushFrame(frame,"OutBox");
      //Give up and take our toys home.
      return;
    }

  // Generate a new trigger TH
  I3TriggerHierarchyPtr saved_triggers(new I3TriggerHierarchy);

  I3TriggerHierarchy::iterator th_iter;
  
  for(th_iter = triggers->begin() ;
      th_iter != triggers->end() ;
      th_iter++)
    {

      if(th_iter->GetTriggerKey().CheckConfigID())
 	{
	  /* 	  log_warn("Got trigger %s %s %i",
		   TriggerKey::GetSourceString(th_iter->GetTriggerKey().GetSource()),
		   TriggerKey::GetTypeString(th_iter->GetTriggerKey().GetType()),
		   th_iter->GetTriggerKey().GetConfigID());*/
	  int mycount;
	  mycount = (int) count(match_keys_.begin(),match_keys_.end(),
			th_iter->GetTriggerKey().GetConfigID());
	  if (mycount > 0)
	    {
	      log_debug("Found match %i",th_iter->GetTriggerKey().GetConfigID());
	      saved_triggers->insert(saved_triggers->begin(), *th_iter);
	    }
 	}
      
    }
  if (saved_triggers->size() > 0){
    frame->Put(OutTriggerHierarchy_,saved_triggers);
  }
  PushFrame(frame,"OutBox");
  
}
