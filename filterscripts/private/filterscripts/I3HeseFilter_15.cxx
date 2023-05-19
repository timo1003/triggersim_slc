#include <filterscripts/I3HeseFilter_15.h>

#include <iostream>

#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3HeseFilter_15>);

#include <icetray/I3Bool.h>
#include <dataclasses/I3Double.h>

I3HeseFilter_15::I3HeseFilter_15(const I3Context& context) :
  I3JEBFilter(context)
{
  minimumCharge_ = 1500.;
  AddParameter("MinimumCharge", "charge threshold", minimumCharge_);
  
  vetoName_ = "VHESelfVeto";
  AddParameter("VetoName", "name of veto I3Bool", vetoName_);

  chargeName_ = "CausalQTot";
  AddParameter("ChargeName", "name of charge I3Double", chargeName_);

}

void I3HeseFilter_15::Configure()
{
  GetParameter("MinimumCharge", minimumCharge_);
  GetParameter("VetoName", vetoName_);
  GetParameter("ChargeName", chargeName_);
}

bool I3HeseFilter_15::KeepEvent(I3Frame& frame)
{
    I3BoolConstPtr veto = frame.Get<I3BoolConstPtr>(vetoName_);
    I3DoubleConstPtr qtot_causal = frame.Get<I3DoubleConstPtr>(chargeName_);

    // check if "VHESelfVeto" exists in frame: event had less than 250 PE and VHESelfVeto could not be evaluated
    if (!veto) {
        return false;
    }

    // if VHESelfVeto==true: event was vetoed, i.e. it had hits in the veto layer
    if (veto->value) {
        return false;
    } else {
        // we want to keep the events that were not vetoed, i.e. VHESelfVeto==false
        if (qtot_causal->value >= minimumCharge_) {
            return true;
        } else {
            return false;
        }
    }
}

void I3HeseFilter_15::Finish()
{
  log_info("HeseFilter Rate *************************");
  log_info("   ");
}
