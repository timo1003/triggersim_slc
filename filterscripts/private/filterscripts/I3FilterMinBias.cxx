#include <filterscripts/I3FilterMinBias.h>

#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3FilterMinBias>);



I3FilterMinBias::I3FilterMinBias(const I3Context& context) :
  I3JEBFilter(context)
{

}

void I3FilterMinBias::Configure()
{

}

bool I3FilterMinBias::KeepEvent(I3Frame& frame)
{
  //This filter will always return true. The prescaling happens later
  return true;
}

void I3FilterMinBias::Finish()
{
  log_info("FilterMinBias Rate *************************");
  log_info("   ");
}
