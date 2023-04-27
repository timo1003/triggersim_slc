/**
 * copyright  (C) 2010
 * the icecube collaboration
 * $Id:
 *
 * @file CylinderTrigger.cxx
 * @version
 * @date
 * @author danninger
 */

#include <trigger-sim/modules/CylinderTrigger.h>
#include <trigger-sim/algorithms/CylinderTriggerAlgorithm.h>
#include <icetray/OMKey.h>
#include <dataclasses/I3Vector.h>
#include <icetray/I3Units.h>
#include <icetray/I3Bool.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>
#include <boost/foreach.hpp>
#include <boost/assign/std/vector.hpp>
#include <dataclasses/geometry/I3Geometry.h>
#include "trigger-sim/utilities/DOMSetFunctions.h"
#include "trigger-sim/utilities/DetectorStatusUtils.h"

using namespace boost::assign;
using DetectorStatusUtils::tk_ts_pair_t;
using DetectorStatusUtils::_sourceID;
using DetectorStatusUtils::_typeID;
using DetectorStatusUtils::_configID;
using DetectorStatusUtils::GetTriggerStatus;

I3_MODULE(CylinderTrigger);
const TriggerKey::TypeID TYPEID(TriggerKey::VOLUME);

CylinderTrigger::CylinderTrigger(const I3Context& context) : 
  I3Module(context),
  launchReadoutName_(""), // formerly, "InIceRawData", but this won't allow for IceTop-Volume
  pulseReadoutName_(""),
  triggerName_("I3Triggers"),
  domSetsName_("DOMSets"),
  configIDParam_(INT_MIN),
  triggerWindow_(NAN),
  triggerThreshold_(INT_MAX),
  cylinderRadius_(NAN),
  cylinderHeight_(NAN),
  measurementMode_(0),
  domSet_(INT_MIN),
  eventCount_(0),
  triggerCount_(0)
{

  AddParameter("DataReadoutName",
	       "This holds the DOM launches",
	       launchReadoutName_);

  AddParameter("PulseReadoutName",
	       "This holds the reco pulses",
	       pulseReadoutName_);
  
  AddParameter("TriggerName",
	       "Name of the I3TriggerHierarchy to store the triggers in.",
	       triggerName_);
    
  AddParameter("TriggerConfigID",
	       "Config ID of the trigger.",
	       configIDParam_);

  AddParameter("DOMSetsName",
           "Name of the I3MapKeyVectorInt defining the DomSets for each DOM.",
           domSetsName_);

  AddParameter("MeasurementMode",
	       "The way to do the triggering. 0=All LC hits, 1=PMTs with at least 1 LC hit, 2=Modules with at least 1 LC hit",
	       measurementMode_);

  AddOutBox("OutBox");
}

CylinderTrigger::~CylinderTrigger() {}

void CylinderTrigger::Configure()
{  
  GetParameter("DataReadoutName", launchReadoutName_);
  GetParameter("PulseReadoutName", pulseReadoutName_);
  GetParameter("TriggerName",triggerName_);
  GetParameter("TriggerConfigID",configIDParam_);
  GetParameter("DOMSetsName", domSetsName_);

  GetParameter("MeasurementMode",measurementMode_);

  if(configIDParam_ != INT_MIN)
    configID_ = configIDParam_;

  log_warn("Using measurement mode %i", measurementMode_);

}

void CylinderTrigger::DAQ(I3FramePtr frame)
{
 
  // Get the DOMSets from the frame
  I3MapKeyVectorIntConstPtr domSets = 
    frame->Get<I3MapKeyVectorIntConstPtr>(domSetsName_);

  // Some debugging messages:
  if (domSets) {
    for (I3MapKeyVectorInt::const_iterator ds = domSets->begin(); ds != domSets->end(); ds++) { 
      OMKey k = ds->first;
      std::vector<int> vi = ds->second;
      for (unsigned int i=0; i<vi.size(); i++) log_debug("DOMset-from-Qframe entry %s, %d", k.str().c_str(), vi[i]);
    }
  } else { 
    log_debug("You requested to grab the \"%s\" DOMSets from the frame, but it is empty.", domSetsName_.c_str());  // debug
  }

  // needed to calculate Cylinder
  I3GeometryConstPtr geometry = frame->Get<I3GeometryConstPtr>(); 
  
  // Create the trigger object
  CylinderTriggerAlgorithm volumeTrigger(triggerWindow_, 
					 triggerThreshold_, 
					 simpleMultiplicity_, 
					 geometry, 
					 cylinderRadius_, 
					 cylinderHeight_);

  log_debug("Checking for CylinderTriggers...");
  eventCount_++;

  std::vector<I3Trigger> tlist;

  /*------------------------------------------------------------*
   * Get DomLaunchSeriesMap from frame
   *------------------------------------------------------------*/
  // Default values for the hit maps should be empty
  I3DOMLaunchSeriesMapConstPtr launchMap(new I3DOMLaunchSeriesMap());
  I3RecoPulseSeriesMapConstPtr pulseMap(new I3RecoPulseSeriesMap());
  
  if( (launchReadoutName_.size() == 0) && (pulseReadoutName_.size() == 0) ){
    if(triggerKey_.GetSource() == TriggerKey::IN_ICE){
      launchReadoutName_ = "InIceRawData";
    }else{
      if(triggerKey_.GetSource() == TriggerKey::ICE_TOP){
        launchReadoutName_ = "IceTopRawData";
      }else{
        std::stringstream s;
        s<<triggerKey_;
        log_error("Couldn't determine the trigger source from this trigger : ");
        log_error("%s",s.str().c_str());
        log_fatal("You'll never find a nameless map with launches in it.");
      }
    }
  }
  else {
    log_debug("Grabbing: %s and %s", launchReadoutName_.c_str(), pulseReadoutName_.c_str());

    // Grab the launches
    if( launchReadoutName_.size() && frame->Has(launchReadoutName_))
      launchMap = frame->Get<I3DOMLaunchSeriesMapConstPtr>(launchReadoutName_);

    // Grab the pulses
    if( pulseReadoutName_.size() && frame->Has(pulseReadoutName_))
      pulseMap = frame->Get<I3RecoPulseSeriesMapConstPtr>(pulseReadoutName_);
  }


  // count the hits for debugging purposes
  int count = 0;
  I3DOMLaunchSeriesMap::const_iterator mapIter;
  for (mapIter = launchMap->begin(); mapIter != launchMap->end(); mapIter++) {
    I3DOMLaunchSeries::const_iterator seriesIter;
    for (seriesIter = mapIter->second.begin(); 
	 seriesIter != mapIter->second.end(); 
	 seriesIter++) count++;
  }
  log_debug("Got %d launches to split", count);

  count = 0;
  I3RecoPulseSeriesMap::const_iterator mapIter2;
  for (mapIter2 = pulseMap->begin(); mapIter2 != pulseMap->end(); mapIter2++) {
    I3RecoPulseSeries::const_iterator seriesIter;
    for (seriesIter = mapIter2->second.begin(); 
	 seriesIter != mapIter2->second.end(); 
	 seriesIter++) count++;
  }
  log_debug("Got %d pulses to split", count);

  /*------------------------------------------------------------*
   * Fill the hits
   *------------------------------------------------------------*/
  TriggerHitVectorPtr hitVector(new TriggerHitVector);
  FillHits(launchMap, hitVector, domSets);
  FillHits(pulseMap, hitVector, domSets);

  /*------------------------------------------------------------*
   * Time order the hits
   *------------------------------------------------------------*/
  std::sort(hitVector->begin(), hitVector->end());
  Dump(hitVector);

  /*------------------------------------------------------------*
   * Run the CylinderTrigger
   *------------------------------------------------------------*/
  volumeTrigger.AddHits(hitVector);
  
  unsigned int numTriggers = volumeTrigger.GetNumberOfTriggers();
  for (unsigned int n = 0; n < numTriggers; n++) {
    
    TriggerHitVectorPtr triggerHits = volumeTrigger.GetNextTrigger();
    
    // We have a trigger!
    triggerCount_++;
    
    // The trigger times are defined by the hits in the time window
    double startTime(triggerHits->front().time);
    double stopTime(triggerHits->back().time);
    
    I3Trigger tr;
    tr.GetTriggerKey() = triggerKey_;
    tr.SetTriggerFired(true);
    tr.SetTriggerTime(startTime);
    tr.SetTriggerLength(stopTime - startTime);
    
    tlist.push_back(tr);
    
  } // end loop over triggers
    
  // Check to see if a trigger hierarchy already exists
  I3TriggerHierarchyPtr triggers;
  if(frame->Has(triggerName_)){
    const I3TriggerHierarchy& old_th = frame->Get<I3TriggerHierarchy>(triggerName_);
    triggers = I3TriggerHierarchyPtr(new I3TriggerHierarchy(old_th));
    frame->Delete(triggerName_);
  }else{
    triggers = I3TriggerHierarchyPtr(new I3TriggerHierarchy);
  }

  // Fill the trigger hierarchy
  std::vector<I3Trigger>::const_iterator tIter;
  for (tIter = tlist.begin(); tIter != tlist.end(); tIter++)
    triggers->insert(triggers->begin(), *tIter);    

  frame->Put(triggerName_,triggers);
  PushFrame( frame );
}

void CylinderTrigger::Finish()
{
  std::stringstream sstr;
  sstr << "Found "<<triggerCount_<<" triggers out of "<<eventCount_<<" events";
  if(configID_) sstr<<" for config id "<<configID_.get()<<".";
  else sstr<<".";
  log_info("%s",sstr.str().c_str());
}

void CylinderTrigger::FillHits(I3DOMLaunchSeriesMapConstPtr launches, 
			       TriggerHitVectorPtr hits, 
			       I3MapKeyVectorIntConstPtr domSets)
{
  log_debug("Fill the hits");
  I3DOMLaunchSeriesMap::const_iterator mapIter;
  std::set<OMKey> lcPMTs;
  std::set<OMKey> lcOMs;
  for (mapIter = launches->begin(); mapIter != launches->end(); mapIter++) {
    const OMKey& omKey = mapIter->first;

    I3DOMLaunchSeries::const_iterator seriesIter;
    for (seriesIter = mapIter->second.begin(); 
	 seriesIter != mapIter->second.end();
	 seriesIter++) {
      if( seriesIter->GetLCBit() ){
	if (domSet_) { 
	  log_debug("A DOMSet is specified for this trigger: %d", domSet_.get());
	  log_debug("...and is DOM %s included? %d", omKey.str().c_str(), DOMSetFunctions::InDOMSet(omKey,domSet_.get(),domSets));
	}
	else { 
	  log_debug("No DOMSet is specified, so this code will just say %s is included by default", omKey.str().c_str()); 
	}      
      	if( ( domSet_ && DOMSetFunctions::InDOMSet(omKey,domSet_.get(),domSets) ) ||
	    !domSet_ ){
          TriggerHitPtr hit(new TriggerHit);
		  hit->pos = omKey.GetOM();
		  hit->string = omKey.GetString();
		  hit->time = seriesIter->GetStartTime();
		  
		  switch(measurementMode_) {
		  case 1: {
   	        if( std::find(lcPMTs.begin(),
		 	   lcPMTs.end(),
			   omKey) == lcPMTs.end() ){
	           lcPMTs.insert(omKey);
	           hits->push_back(*hit);
			}
			break;
		  }
		  case 2: {
			OMKey module(omKey);
			module.SetPMT(0);
			if( std::find(lcOMs.begin(),
			    lcOMs.end(),
			    module) == lcOMs.end() ){
				lcOMs.insert(module);
				hits->push_back(*hit);
			}
			break;
		  }
		  default: 
		    hits->push_back(*hit);
		  }
		}
      }
    }	
  }
}



void CylinderTrigger::FillHits(I3RecoPulseSeriesMapConstPtr pulses, 
			       TriggerHitVectorPtr hits, 
			       I3MapKeyVectorIntConstPtr domSets)
{
  log_debug("Fill the hits");
  I3RecoPulseSeriesMap::const_iterator mapIter;
  std::set<OMKey> lcPMTs;
  std::set<OMKey> lcOMs;
  for (mapIter = pulses->begin(); mapIter != pulses->end(); mapIter++) {
    const OMKey& omKey = mapIter->first;

    I3RecoPulseSeries::const_iterator seriesIter;
    for (seriesIter = mapIter->second.begin(); 
	 seriesIter != mapIter->second.end();
	 seriesIter++) {
      if( seriesIter->GetFlags() & I3RecoPulse::LC ){
      	if( ( domSet_ && DOMSetFunctions::InDOMSet(omKey,domSet_.get(),domSets) ) ||
	    !domSet_ ){
  
     	  TriggerHitPtr hit(new TriggerHit);
		  hit->pos = omKey.GetOM();
		  hit->string = omKey.GetString();
		  hit->time = seriesIter->GetTime();

		  switch(measurementMode_) {
            case 1: {
		      if( std::find(lcPMTs.begin(), lcPMTs.end(), omKey) == lcPMTs.end() ){
                lcPMTs.insert(omKey);
			    hits->push_back(*hit);
		      }
			  break;
		    }
		    case 2: {
	          OMKey module(omKey);
		      module.SetPMT(0);
		      if( std::find(lcOMs.begin(), lcOMs.end(), module) == lcOMs.end() ){
			    lcOMs.insert(module);
			    hits->push_back(*hit);
		      }
			  break;
		    }
		    default: {
		      hits->push_back(*hit);
		    }
		  }
		}
      }
    }
  }
}



void CylinderTrigger::Dump(TriggerHitVectorPtr input)
{
  log_debug("Dumping Event with %zd hits...", input->size());

  TriggerHitVector::const_iterator iter;
  for (iter = input->begin(); iter != input->end(); iter++) {
    const TriggerHit& hit __attribute__((unused)) = *iter;
    log_debug("  Time %f   Position %u", hit.time, hit.pos);
  }
}

void CylinderTrigger::DetectorStatus(I3FramePtr frame){
  // Get DetectorStatus from the frame
  I3DetectorStatusConstPtr detStatus = frame->Get<I3DetectorStatusConstPtr>();
  if(!detStatus) log_fatal("This DetectorStatus frame has no I3DetectorStatus object.");

  boost::optional<tk_ts_pair_t> tkts = GetTriggerStatus
    (detStatus, _sourceID = TriggerKey::UNKNOWN_SOURCE,
     _typeID = TYPEID,
     _configID = configID_ );

  if(!tkts) log_fatal("Failed to configure this module from the DetectorStatus.");

  // this needs to be passed on to the I3Trigger
  triggerKey_ = tkts.get().first;
  
  // now set the parameters
  tkts.get().second.GetTriggerConfigValue("simpleMultiplicity", simpleMultiplicity_);
  tkts.get().second.GetTriggerConfigValue("multiplicity", triggerThreshold_);
  tkts.get().second.GetTriggerConfigValue("timeWindow", triggerWindow_);
  tkts.get().second.GetTriggerConfigValue("radius", cylinderRadius_);
  tkts.get().second.GetTriggerConfigValue("height", cylinderHeight_);
  tkts.get().second.GetTriggerConfigValue("domSet", domSet_);

  log_info("Cylinder: %d, multi: %d, timewindow: %f, radius: %f, height: %f, domset: %d", 
	    simpleMultiplicity_, triggerThreshold_, triggerWindow_, 
	    cylinderRadius_, cylinderHeight_, domSet_.get());

  PushFrame( frame );
}
