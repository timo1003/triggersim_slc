#include <filterscripts/I3HighQFilter_17.h>

#include <iostream>

#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3HighQFilter_17>);

#include <icetray/I3Bool.h>
#include <dataclasses/I3Double.h>

I3HighQFilter_17::I3HighQFilter_17(const I3Context& context) :
  I3JEBFilter(context)
{
  minimumCharge_ = 1000.;
  AddParameter("MinimumCharge", "charge threshold", minimumCharge_);

  chargeName_ = "Homogenized_QTot";
  AddParameter("ChargeName", "name of charge I3Double", chargeName_);
}

void I3HighQFilter_17::Configure()
{
  GetParameter("MinimumCharge", minimumCharge_);
  GetParameter("ChargeName", chargeName_);

}

bool I3HighQFilter_17::KeepEvent(I3Frame& frame)
{
    I3DoubleConstPtr qtot = frame.Get<I3DoubleConstPtr>(chargeName_);

    // Make sure qtot exists in the frame....
    if (!qtot) {
      return false;
    }

    if (qtot->value >= minimumCharge_) {
      return true;
    } else {
      return false;
    }
}

void I3HighQFilter_17::Finish()
{
  log_info("HighQFilter Rate *************************");
  log_info("   ");
}
