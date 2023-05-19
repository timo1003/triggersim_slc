#include <filterscripts/I3MeseFilter_15.h>

#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3MeseFilter_15>);



I3MeseFilter_15::I3MeseFilter_15(const I3Context& context) :
  I3JEBFilter(context)
{

}

void I3MeseFilter_15::Configure()
{

}

bool I3MeseFilter_15::KeepEvent(I3Frame& frame)
{
    I3BoolConstPtr veto = frame.Get<I3BoolConstPtr>("MESEVeto_Bool");
    
    //check if "MESEVeto" exists in frame: event had less than 250 PE and VHESelfVeto could not be evaluated
    if(!veto){
        return false;
    }
    // if MESEVeto==true: event was vetoed, i.e. it had hits in the veto layer
    if(veto->value){
        return false;
    // we want to keep the events that were not vetoed, i.e. MESEVeto==false
    }else{
        return true;
    }
}

void I3MeseFilter_15::Finish()
{
  log_info("MeseFilter Rate *************************");
  log_info("   ");
}
