#include <filterscripts/I3EHEFilter_13.h>
#include <filterscripts/I3FilterModule.h>
#include "recclasses/I3PortiaEvent.h"

I3_MODULE(I3FilterModule<I3EHEFilter_13>);


#include <dataclasses/physics/I3RecoHit.h>

I3EHEFilter_13::I3EHEFilter_13(const I3Context& context) :
  I3JEBFilter(context),
  threshold_(1000.0),
  responsekey_("EHESummaryPulseInfo")
{
  AddParameter("Threshold",
	       "Minimum NPE threshold.",
	       threshold_);

  AddParameter("PortiaEventName",
	       "Name of the PortiaEvent in the frame.",
	       responsekey_);
}

void I3EHEFilter_13::Configure()
{
  GetParameter("Threshold",threshold_);
  GetParameter("PortiaEventName",responsekey_);
}

bool I3EHEFilter_13::KeepEvent(I3Frame& frame)
{
  I3PortiaEventConstPtr portiaEvent_ptr = frame.Get<I3PortiaEventConstPtr>(responsekey_);
  
  if(portiaEvent_ptr){
    // best NPE with time window cleaning is used
    const double thisBestNPE = portiaEvent_ptr->GetTotalBestNPEbtw();
    if (thisBestNPE>threshold_) {
      log_debug("filtered out event with %f Best NPE, (minimum %f)", 
		thisBestNPE, threshold_);
      return true;
    }
  }
  else{
    log_error("no portia event information found !!");
    return false;
  }
  
  return false;
}

void I3EHEFilter_13::Finish()
{
  log_info("EHEFilter Rate *************************");
  log_info("Parameters:");
  log_info("  NPE Threshold:  %f",threshold_);
  log_info("   ");
}
