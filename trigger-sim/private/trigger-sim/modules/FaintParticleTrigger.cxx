#include <iostream>
#include <math.h>
#include <boost/foreach.hpp>
#include "icetray/I3TrayHeaders.h"
#include "icetray/I3Units.h"
#include "icetray/I3Bool.h"
#include "dataclasses/physics/I3TriggerHierarchy.h"
#include "dataclasses/status/I3TriggerStatus.h"
#include "dataclasses/status/I3DetectorStatus.h"
#include "dataclasses/geometry/I3Geometry.h"
#include "dataclasses/physics/I3DOMLaunch.h"
#include "dataclasses/TriggerKey.h"
#include "dataclasses/I3Constants.h"
#include "dataclasses/I3Double.h"
#include "dataclasses/I3Map.h"
#include "dataclasses/I3Vector.h"
#include "trigger-sim/utilities/DOMSetFunctions.h"
#include "trigger-sim/algorithms/TriggerContainer.h"
#include "trigger-sim/modules/FaintParticleTrigger.h"
#include "trigger-sim/utilities/DetectorStatusUtils.h"
#include "trigger-sim/algorithms/FptHit.h"
#include <trigger-sim/algorithms/FPTTimeWindow.h>
#include <trigger-sim/algorithms/FaintParticleTriggerAlgorithm.h>

using namespace std;
using namespace I3Units;

using DetectorStatusUtils::tk_ts_pair_t;
using DetectorStatusUtils::_sourceID;
using DetectorStatusUtils::_typeID;
using DetectorStatusUtils::_configID;
using DetectorStatusUtils::GetTriggerStatus;

I3_MODULE(FaintParticleTrigger);
const TriggerKey::SourceID SOURCEID(TriggerKey::IN_ICE);
const TriggerKey::TypeID TYPEID(TriggerKey::FAINT_PARTICLE);

FaintParticleTrigger::FaintParticleTrigger(const I3Context& ctx) :
  I3Module(ctx),
  triggerSourceParam_(INT_MIN),
  triggerSource_(TriggerKey::UNKNOWN_SOURCE),
  configIDParam_(INT_MIN),
  triggerName_("I3Triggers"),
  dataReadoutName_("InIceRawData"),
  domSetsName_("DOMSets"),
  // the following parameters are read from the GCD:
  time_window_(NAN),     // 2500 for  DC 3000 ns for full detector
  time_window_separation_(NAN), // 800 ns
  max_trigger_length_(NAN),
  hit_min_(NAN),           // 
  hit_max_(NAN),           // 
  double_velocity_min_(NAN), 
  double_velocity_max_(NAN), 
  double_min_(NAN), 
  use_dc_version_(NAN),
  triple_min_(NAN), 
  azimuth_histogram_min_(NAN), 
  zenith_histogram_min_(NAN), 
  histogram_binning_(NAN), 
  slcfraction_min_(NAN), 
  domSet_(boost::optional<int>())

  {
    AddOutBox("OutBox");
    
    AddParameter("DataReadoutName",
         "This holds the DOM launches",
        dataReadoutName_);
        AddParameter("TriggerSource",
           "Source of the trigger (IN_ICE = 0)",
           triggerSourceParam_);
    
    AddParameter("TriggerName",
         "Name to give to this triggers' records in the event",
         triggerName_);
    
    AddParameter("TriggerConfigID",
         "Config ID of the trigger.",
         configIDParam_);
    
    AddParameter("DOMSetsName",
         "Name of the I3MapKeyVectorInt defining the DomSets for each DOM.",
         domSetsName_);
    

}    
      
     
FaintParticleTrigger::~FaintParticleTrigger(){
}     
       
void FaintParticleTrigger::Configure(){
    GetParameter("DataReadoutName", dataReadoutName_);
    GetParameter("TriggerName",triggerName_);
    GetParameter("TriggerSource",triggerSourceParam_);
    GetParameter("TriggerConfigID",configIDParam_);
    GetParameter("DOMSetsName", domSetsName_);

    if(triggerSourceParam_ != INT_MIN)
      triggerSource_ = static_cast<TriggerKey::SourceID>(triggerSourceParam_);

    if(configIDParam_ != INT_MIN)
      configID_ = configIDParam_;


}

void FaintParticleTrigger::Finish(){
}
      
void FaintParticleTrigger::DAQ(I3FramePtr frame){
      
  // Get the DOMSets from the frame
  I3MapKeyVectorIntConstPtr domSets = 
    frame->Get<I3MapKeyVectorIntConstPtr>(domSetsName_);
    
    
  I3GeometryConstPtr geometry = frame->Get<I3GeometryConstPtr>();    
  //std::cout << "Next event"<<std::endl;
  // lists per frame:
  //error new class including slc informatin has to be created

  FptHitVectorPtr hits(new FptHitVector);
  /*------------------------------------------------------------*
   * Get DomLaunchSeriesMap from frame
   *------------------------------------------------------------*/
  if (!frame->Has(dataReadoutName_)) {
    log_debug("Frame does not contain an I3DOMLaunchSeriesMap named %s", 
         dataReadoutName_.c_str());
    PushFrame( frame );
    return;
  }
    
  const I3DOMLaunchSeriesMap& dlsMap = frame->Get<I3DOMLaunchSeriesMap>(dataReadoutName_);
  BOOST_FOREACH(I3DOMLaunchSeriesMap::const_reference r,dlsMap){
    BOOST_FOREACH(I3DOMLaunchSeries::const_reference launch,r.second){
   
    
    if( ( domSet_ && DOMSetFunctions::InDOMSet(r.first,domSet_.get(),domSets) ) ||
        !domSet_ ) {                                                      
      // either if the whole detector or a specific domset are specified, 
      // in both cases copy DomLaunches
       
      FptHitPtr hit = FptHitPtr(new FptHit);
      hit->string = r.first.GetString();
      hit->pos = r.first.GetOM();
      hit->lc = launch.GetLCBit();
      hit->time = launch.GetStartTime();
      hits->push_back(*hit);
      /*  
      SlcTHit hit;
      hit.string = r.first.GetString();
      hit.pos = r.first.GetOM();
      hit.lc = launch.GetLCBit();
      std::cout << "hits"<< launch.GetLCBit();  
      hit.time = launch.GetStartTime();
      TimeWindowList.push_back(hit);
       */
        
      
      
                }
          }
   
      }
      

    /*
    for(int i = 0; i < int(hits->size()); i++)
      {
        SlcTHit payload = hits->at(i);
        TimeWindowList->push_back(*payload);
      }
    */
    
    /*
    std::cout<<"hit_min"<<hit_min_<<std::endl;
    std::cout<<"hit_max"<<hit_max_<<std::endl;
    std::cout<<"double_min"<<double_min_<<std::endl;
    std::cout<<"double_max"<<double_max_<<std::endl; 
    std::cout<<"azi_min"<<azi_min_<<std::endl;
    std::cout<<"zen_min"<<zen_min_<<std::endl; 
    std::cout<<"triple_min"<<triple_min_<<std::endl;
    std::cout<<"triple_max"<<triple_max_<<std::endl;
    std::cout<<"vel_min"<<cut_veldoublet_min_<<std::endl;
    std::cout<<"vel_max"<<cut_veldoublet_max_<<std::endl;
    std::cout<<"trigger length max"<<max_trigger_length_<<std::endl;
    */

    // Check to see if a trigger hierarchy already exists
    I3TriggerHierarchyPtr triggers;
    if(frame->Has(triggerName_)){
        const I3TriggerHierarchy& old_th = frame->Get<I3TriggerHierarchy>(triggerName_);
        triggers = I3TriggerHierarchyPtr(new I3TriggerHierarchy(old_th));
        frame->Delete(triggerName_);
    }else{
        triggers = I3TriggerHierarchyPtr(new I3TriggerHierarchy);
    }
    
    I3GeometryConstPtr geo = frame->Get<I3GeometryConstPtr>("I3Geometry");
    if( ! geo )
      {
      log_fatal("Can't get geometry from the frame!");
      }

    
    // Sort hits timewise
    /*
    std::cout.precision(15);
    std::cout<<"Before sorting"<<hits->begin()->time<<endl;
    std::cout<<"Before sorting end"<<hits->end()->time<<endl;
    std::cout<<"After sorting"<<hits->begin()->time<<endl;
    std::cout<<"After sorting end"<<hits->end()->time<<endl;
    
    */
    std::vector<I3Trigger> tlist;
    sort(hits->begin(), hits->end());
    if (hits->size()>1){

        tlist =RunTrigger(hits, geo);
    }
        

        



    // Fill the trigger hierarchy
    std::vector<I3Trigger>::const_iterator tIter;
    for (tIter = tlist.begin(); tIter != tlist.end(); tIter++)
      triggers->insert(triggers->begin(), *tIter);    

    frame->Put(triggerName_,triggers);
    PushFrame( frame );


}

std::vector<I3Trigger> FaintParticleTrigger::RunTrigger(FptHitVectorPtr hits__, const I3GeometryConstPtr &geo)
    
{
    std::vector<I3Trigger> tlist__;
    FaintParticleTriggerAlgorithm fpTrigger(time_window_,time_window_separation_, max_trigger_length_,hit_min_, hit_max_,double_velocity_min_,double_velocity_max_,double_min_,use_dc_version_, triple_min_, azimuth_histogram_min_, zenith_histogram_min_, histogram_binning_, slcfraction_min_,   geo);
    
 
    
    
    fpTrigger.AddHits(hits__, geo);
    
    unsigned int numTriggers = fpTrigger.GetNumberOfTriggers();
    for (unsigned int n = 0; n < numTriggers; n++) {

      FptHitVectorPtr timeHits = fpTrigger.GetNextTrigger();

      // We have a trigger!
      //triggerCount_++;

      // The trigger times are defined by the hits in the time window
      double startTime(timeHits->front().time);
      double stopTime(timeHits->back().time);

      I3Trigger tr;
      tr.GetTriggerKey() = triggerKey_;
      tr.SetTriggerFired(true);
      tr.SetTriggerTime(startTime);
      tr.SetTriggerLength(stopTime - startTime);

      tlist__.push_back(tr);
    
        }
    
    /*
    int first_cut = TimeWindowList__.size();
    if (first_cut >= hit_min_ and first_cut <= hit_max_){
    
    //triggerCount_++;

      // The trigger times are defined by the hits in the time window
      //double startTime(hits__->front().time);
      //double stopTime(hits__->back().time);

      I3Trigger tr;
      tr.GetTriggerKey() = triggerKey_;
      tr.SetTriggerFired(true);
      //tr.SetTriggerTime(startTime);
      //tr.SetTriggerLength(stopTime - startTime);

      tlist__.push_back(tr);
            }
    */
    return tlist__;
        
    
              
              
}    

void FaintParticleTrigger::DetectorStatus(I3FramePtr frame){
  // Get DetectorStatus from the frame
  I3DetectorStatusConstPtr detStatus = frame->Get<I3DetectorStatusConstPtr>();
  if(!detStatus) log_fatal("This DetectorStatus frame has no I3DetectorStatus object.");

  boost::optional<tk_ts_pair_t> tkts = GetTriggerStatus
    (detStatus, _sourceID = SOURCEID, _typeID = TYPEID, _configID = configID_ );

  if(!tkts) log_fatal("Failed to configure this module from the DetectorStatus.");

  // this needs to be passed on to the I3Trigger
  triggerKey_ = tkts.get().first;
  
  // now set the parameters
  tkts.get().second.GetTriggerConfigValue("time_window", time_window_);
  tkts.get().second.GetTriggerConfigValue("time_window_separation", time_window_separation_);
  tkts.get().second.GetTriggerConfigValue("max_trigger_length", max_trigger_length_);
  tkts.get().second.GetTriggerConfigValue("hit_min", hit_min_);
  tkts.get().second.GetTriggerConfigValue("hit_max", hit_max_);
  tkts.get().second.GetTriggerConfigValue("double_velocity_min", double_velocity_min_);
  tkts.get().second.GetTriggerConfigValue("double_velocity_max", double_velocity_max_);
  tkts.get().second.GetTriggerConfigValue("double_min", double_min_);
  tkts.get().second.GetTriggerConfigValue("use_dc_version", use_dc_version_);
  tkts.get().second.GetTriggerConfigValue("triple_min", triple_min_);
  tkts.get().second.GetTriggerConfigValue("azimuth_histogram_min", azimuth_histogram_min_);
  tkts.get().second.GetTriggerConfigValue("zenith_histogram_min", zenith_histogram_min_); 
  tkts.get().second.GetTriggerConfigValue("histogram_binning", histogram_binning_);
  tkts.get().second.GetTriggerConfigValue("slcfraction_min", slcfraction_min_);
  tkts.get().second.GetTriggerConfigValue("domSet", domSet_);//these are optional


  
   
  PushFrame( frame );
}

      
      
      
      