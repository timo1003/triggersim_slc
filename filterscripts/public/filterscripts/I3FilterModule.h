#ifndef JEBFILTER_I3FILTERMODULE_H
#define JEBFILTER_I3FILTERMODULE_H

#include <icetray/I3ConditionalModule.h>
#include <icetray/I3Frame.h>
#include <icetray/I3Tray.h>

#include <dataclasses/physics/I3EventHeader.h>
#include <dataclasses/physics/I3DOMLaunch.h>
#include <dataclasses/physics/I3TWRLaunch.h>
#include <icetray/I3Units.h>
#include <icetray/I3Bool.h>

/**
 * @brief This module will apply a filter to the events it's given.  
 * The code is pretty much copied from IcePick, and the purpose is
 * the same.  When called, this module should be given an I3Filter
 * object as a template.  
 */
template <class FilterModule>

class I3FilterModule : public FilterModule
{
 
public:
  I3FilterModule(const I3Context& context) : 
    FilterModule(context),
    decisionName_(I3::name_of<FilterModule>()),
    discardEvents_(false), 
    firstsec_(0),
    firstnanosec_(0),
    lastsec_(0),
    lastnanosec_(0)
    {
      FilterModule::AddParameter("DecisionName",
		   "Name of the filter decision in the Frame",
		   decisionName_);
      FilterModule::AddParameter("DiscardEvents",
		   "Set to 'true' if we're supposed to "
		   "actually discard events",
		   discardEvents_);
      FilterModule::AddParameter("TriggerEvalList",
		   "List of bools from TriggerCheck that are required for event consideration",
		   executeFilter_);
      FilterModule::AddOutBox("OutBox");
    }

  void Configure()
    {
      FilterModule::GetParameter("DecisionName",
		   decisionName_);
      FilterModule::GetParameter("DiscardEvents",
		   discardEvents_);
      FilterModule::GetParameter("TriggerEvalList",
		   executeFilter_);
      
      FilterModule::Configure();
      number_Events_Picked = 0;
      number_Events_Tossed = 0;
      nEvents = 0;
      nEvents_evald = 0;
    }
 
  
  void Physics(I3FramePtr frame)
    {
      nEvents++;
      I3EventHeaderConstPtr header = frame->template Get<I3EventHeaderConstPtr>();
      if(header)
	{
	  if(firstsec_ == 0)
	    {
	      firstsec_ = header->GetStartTime().GetUTCSec();
	      firstnanosec_ = header->GetStartTime().GetUTCDaqTime() / 10;
	    }
	  else
	    {
	      lastsec_ = header->GetStartTime().GetUTCSec();
	      lastnanosec_ = header->GetStartTime().GetUTCDaqTime() / 10;
	    }
	}

      unsigned int execute = 0; 
      for (unsigned int i = 0;
	   i <  executeFilter_.size(); 
	   i++)
	{
	  I3BoolConstPtr executeBool = frame->Get<I3BoolConstPtr>(executeFilter_[i]);
	  if(executeBool)
	    {
	      if (executeBool->value)
		{
		  execute++;
		  log_trace("Executing because of %s\n",executeFilter_[i].c_str());
		}
	    }
	  else
	    {
	      log_info("Requested trigger bool %s not found",
			executeFilter_[i].c_str());
	    }
	}
      //Only evaluate the filter if we have no list of keys or one is true.
      if (execute || (executeFilter_.size() == 0))
	{
	  nEvents_evald++;
	  I3BoolPtr decision(new I3Bool(FilterModule::KeepEvent(*frame)));
	  if (decisionName_!="") 
	    {
	      frame->Put(decisionName_,decision);
	    }
	  if(!decision->value) 
	    {
	      number_Events_Tossed++;
	    }
	  else
	    {
	      number_Events_Picked++;
	    }
	  if(discardEvents_ && !decision->value)
	    {
	      return;
	    }
	}
      FilterModule::PushFrame(frame,"OutBox");
    }
  
  void Finish(){
    FilterModule::Finish();
    
    //double kpercent = number_Events_Picked * 100.0 / (double) nEvents;
    //double fpercent = number_Events_Tossed * 100.0 / (double) nEvents;
    log_info("   ************    Filter: %s", I3::name_of<FilterModule>().c_str() );
    log_info("       Name: %s", decisionName_.c_str());
    log_info("       Events:  %d",nEvents);
    log_info("       Events evaluated:  %d",nEvents_evald);
    log_info("       Events Kept:  %d",number_Events_Picked);
    //log_info("       Pass Rate:  %f percent",kpercent);
    //log_info("       Filter Rate:  %f percent",fpercent);
    
    double livetime;
    livetime = double(lastnanosec_ - firstnanosec_)/I3Units::second;
    //double erate = nEvents / livetime;
    double prate = number_Events_Picked / livetime;
    log_info("       Livetime:  %f sec",livetime);
    log_info("       Passing Event Rate:  %f Hz",prate);
    //log_info("       Total Event Rate:  %f Hz",erate);  
    //log_info("       Livetime:  %f",livetime);
  }

 private:
  std::string decisionName_;
  bool discardEvents_;
  int number_Events_Picked;
  int number_Events_Tossed;
  int nEvents;
  int nEvents_evald;

  unsigned int firstsec_;
  unsigned long long int firstnanosec_;
  unsigned int lastsec_;
  unsigned long long int lastnanosec_;
  std::vector<std::string> executeFilter_;    

  SET_LOGGER("I3FilterModule");
};

#endif
