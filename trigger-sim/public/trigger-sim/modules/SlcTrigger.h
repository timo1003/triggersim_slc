#ifndef I3_SLC_TRIGGER_H
#define I3_SLC_TRIGGER_H

#include "icetray/I3Module.h"
#include "dataclasses/physics/I3Trigger.h"
#include "dataclasses/physics/I3Particle.h"
#include <dataclasses/geometry/I3Geometry.h>
#include "trigger-sim/algorithms/SlcTHit.h"
#include "trigger-sim/algorithms/TriggerContainer.h"


/*
 * slc trigger
 */

class SlcTrigger : public I3Module
{
public:

    SlcTrigger(const I3Context& ctx);
    ~SlcTrigger();

    void Configure();
    
    void DAQ(I3FramePtr frame);
    void DetectorStatus(I3FramePtr frame);
    void Finish();

private:

    SlcTrigger();
    
    int GetTrigStatusSetting(const I3TriggerStatus&, const std::string&);
    void ConfigureFromDetStatus(const I3DetectorStatus& detstatus);
    

    std::vector<I3Trigger> RunTrigger(SlcTHitVectorPtr hits__,
    const I3GeometryConstPtr &geo);
    //function wil be deifned
    
    /* Here follow the variables the module needs */
    // Name of dom launch series
    int triggerSourceParam_;
    TriggerKey::SourceID triggerSource_;
    TriggerKey triggerKey_;
    int configIDParam_;
    boost::optional<int> configID_;
    std::string triggerName_;
    std::string dataReadoutName_;
    std::string domSetsName_;

    double time_window_;
    double time_window_separation_;
    bool triple_bool_;
    double hit_min_;
    double hit_max_;
    double double_min_;
    double double_max_;
    double triple_min_;
    double triple_max_;
    double azi_min_;
    double zen_min_;
    double binning_;
    double slcfraction_min_;
    double cut_veldoublet_min_;
    double cut_veldoublet_max_; 
    double max_trigger_length_;   
    boost::optional<int> domSet_;
    boost::optional<bool> dc_algo_;

    
    SET_LOGGER("SlcTrigger");

};	// end of class 

#endif //I3_SLC_TRIGGER_NEW_H