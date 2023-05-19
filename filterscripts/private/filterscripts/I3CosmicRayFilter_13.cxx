#include <filterscripts/I3CosmicRayFilter_13.h>
#include <filterscripts/I3FilterModule.h>

I3_MODULE(I3FilterModule<I3CosmicRayFilter_13>);

#include <dataclasses/geometry/I3Geometry.h>
#include <dataclasses/TriggerKey.h>
#include <dataclasses/physics/I3Trigger.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>

using namespace I3TriggerHierarchyUtils;

I3CosmicRayFilter_13::I3CosmicRayFilter_13(const I3Context& context): I3JEBFilter(context),
								      triggerName_(I3DefaultName<I3TriggerHierarchy>::value()),
								      itPulseMaskName_("CleanedIceTopTankPulses")
{
  AddParameter("TriggerKey",
	       "Name of the I3TriggerHierarchy in the frame.",
	       triggerName_);
  AddParameter("IceTopPulseMaskKey",
	       "Name of the IceTop I3RecoPulseSeriesMapMask in the frame.",
	       itPulseMaskName_);
  
}


void I3CosmicRayFilter_13::Configure()
{
  GetParameter("TriggerKey",triggerName_);
  GetParameter("IceTopPulseMaskKey",itPulseMaskName_);
}

bool I3CosmicRayFilter_13::KeepEvent(I3Frame& frame)
{
  // Initalizing filter results
  bool it_sta3(false);
  bool it_sta5(false);
  bool it_infill_sta3(false);
  bool ii_smt_it_coinc(false);
  
  // ------------------ Count IceTop stations ----------------------
  //	  
  //!In-Fill and Standard Stations are counted separately
  unsigned int numStdStations(0);
  unsigned int numInfStations(0);

  const I3OMGeoMap& omgeo = frame.Get<I3Geometry>().omgeo;
  I3RecoPulseSeriesMapConstPtr itrp = frame.Get<I3RecoPulseSeriesMapConstPtr>(itPulseMaskName_);

  if(itrp){	
    // Initialize station counters
    std::map<int,int> stdStationCounter;
    std::map<int,int> infStationCounter;
    
    // Loop over IceTop masked reco pulses
    I3RecoPulseSeriesMap::const_iterator itrp_iter;
    for(itrp_iter = itrp->begin(); 
	itrp_iter != itrp->end(); ++itrp_iter){
      const OMKey& omKey = itrp_iter->first;
      
      if(omgeo.find(omKey)->second.omtype == I3OMGeo::IceTop){ 
	
	const I3RecoPulseSeries& dls = itrp_iter->second;
	if(dls.empty()){
	  log_warn("%s has empty reco pulse series. Skipping it!", 
		   omKey.str().c_str());
	  continue;
	}
	
	// Increment station counters
	switch(omKey.GetString()){
	  // In-fill and standard stations
	case 26:
	case 27:
	case 36:
	case 37:
	case 46:
	  stdStationCounter[omKey.GetString()]++;
	  infStationCounter[omKey.GetString()]++;
	  break;
	  
	  // Pure in-fill stations
	case 79:
	case 80:
	case 81:
	  infStationCounter[omKey.GetString()]++;
	  break;
	  
	  // Pure standard stations
	default:
	  stdStationCounter[omKey.GetString()]++;
	  break;
	}   
	
      }//icetop counting
      
    }//loop over omKey
    
    numStdStations = stdStationCounter.size();
    numInfStations = infStationCounter.size();	
  }
  else{
    log_trace("Missing \"%s\" in frame. Assuming there are no IceTop reco pulses for this trigger!", itPulseMaskName_.c_str());
  }
  
  //Look at the triggers in this p-frame
  I3TriggerHierarchyConstPtr triggers = frame.Get<I3TriggerHierarchyConstPtr>(triggerName_);
  if(triggers){
    //
    // Check IceTopSMT condition
    //
    if(I3TriggerHierarchyUtils::Count(*triggers, 
				      TriggerKey::ICE_TOP, 
				      TriggerKey::SIMPLE_MULTIPLICITY) > 0){
      
      // Just a cross check (should never happen)
      if(numStdStations==0 && numInfStations==0){
	log_error("No IceTop HLC hits even though there was an IceTopSMT trigger.");
      }
      
      //
      // ------------------ Check filter conditions ----------------------
      //
      
      // Checking IceTop_STA3 condition
      if(numStdStations>=3){
	log_trace("Found IceTopSTA3 event!");
	it_sta3 = true;
      }
      // Checking IceTop_STA5 condition
      if(numStdStations>=5){
	log_trace("Found IceTopSTA5 event!");
	it_sta5 = true;
      }

      // Checking IceTop_InFill_STA3 condition
      if(numInfStations>=3){
	log_trace("Found IceTop_InFill_STA3 event!");
	it_infill_sta3 = true;
      }
      
    }//IT SMT done
    
    //
    // Coincident events (check InIceSMT condition)
    //
    if(I3TriggerHierarchyUtils::Count(*triggers, 
				      TriggerKey::IN_ICE, 
				      TriggerKey::SIMPLE_MULTIPLICITY) > 0){
      
      //
      // ------------------ Check filter conditions ----------------------
      //
      // Checking InIce_SMT_IceTopCoincidence condition
      if (numStdStations>0){
	log_trace("Found InIceSMT_IceTopCoincidence event!");
	ii_smt_it_coinc = true;
      }

    }//IC SMT done
  }//triggers
  else{
    log_warn("Missing trigger hierarchy \"%s\" in frame. Cannot evaluate filter conditions!", triggerName_.c_str());
  }
  
  // Put filter results to frame
  frame.Put("IceTopSTA3_13",                 I3BoolPtr(new I3Bool(it_sta3)));
  // second copy to make sure SuperDST is kept
  frame.Put("SDST_IceTopSTA3_13",            I3BoolPtr(new I3Bool(it_sta3)));
  frame.Put("IceTopSTA5_13",                 I3BoolPtr(new I3Bool(it_sta5)));
  frame.Put("IceTop_InFill_STA3_13",         I3BoolPtr(new I3Bool(it_infill_sta3)));
  // second copy to make sure SuperDST is kept
  frame.Put("SDST_IceTop_InFill_STA3_13",    I3BoolPtr(new I3Bool(it_infill_sta3)));
  frame.Put("InIceSMT_IceTopCoincidence_13", I3BoolPtr(new I3Bool(ii_smt_it_coinc)));
  // second copy to make sure SuperDST is kept
  frame.Put("SDST_InIceSMT_IceTopCoincidence_13", I3BoolPtr(new I3Bool(ii_smt_it_coinc)));
  // Return True if any of the filter conditions is met
  return it_sta3 ||
         it_sta5 ||
         it_infill_sta3 ||
    	 ii_smt_it_coinc;
}
