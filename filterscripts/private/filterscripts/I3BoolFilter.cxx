#include <filterscripts/I3BoolFilter.h>

#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3BoolFilter>);

#include <icetray/I3Bool.h>

I3BoolFilter::I3BoolFilter(const I3Context& context) :
  I3JEBFilter(context),
  boolkey_("FilterDecision")
{
  AddParameter("BoolKey",
	       "Key of the boolean that will tell us to keep the event or not.",
	       boolkey_);
}

void I3BoolFilter::Configure()
{
  GetParameter("Boolkey",boolkey_);
}

bool I3BoolFilter::KeepEvent(I3Frame& frame)
{
  I3BoolConstPtr thebool = frame.Get<I3BoolConstPtr>(boolkey_);
  if(thebool) return thebool->value;
  return false;
}

void I3BoolFilter::Finish()
{
  log_info("BoolFilter Rate *************************");
  log_info("Parameters:");
  log_info("  TheBool:  %s",boolkey_.c_str());
  log_info("  MyInstance:  %s",GetName().c_str());
  log_info("   ");
}
