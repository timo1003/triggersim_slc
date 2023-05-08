#ifndef I3_FAINT_PARTICLE_TRIGGER_H
#define I3_FAINT_PARTICLE_TRIGGER_H

#include "icetray/I3Module.h"
#include "dataclasses/physics/I3Trigger.h"
#include "dataclasses/physics/I3Particle.h"
#include <dataclasses/geometry/I3Geometry.h>
#include "trigger-sim/algorithms/FptHit.h"
#include "trigger-sim/algorithms/TriggerContainer.h"


/*
 * faint particle trigger
 */

class FaintParticleTrigger : public I3Module
{
public:

    FaintParticleTrigger(const I3Context& ctx);
    ~FaintParticleTrigger();

    void Configure();
    
    void DAQ(I3FramePtr frame);
    void DetectorStatus(I3FramePtr frame);
    void Finish();

private:

    FaintParticleTrigger();
    
    int GetTrigStatusSetting(const I3TriggerStatus&, const std::string&);
    void ConfigureFromDetStatus(const I3DetectorStatus& detstatus);
    

    std::vector<I3Trigger> RunTrigger(FptHitVectorPtr hits__,
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
    double max_trigger_length_; 
    double hit_min_;
    double hit_max_;
    double double_velocity_min_;
    double double_velocity_max_; 
    double double_min_;
    bool use_dc_version_;
    double triple_min_;
    double azimuth_histogram_min_;
    double zenith_histogram_min_;
    double histogram_binning_;
    double slcfraction_min_;
    boost::optional<int> domSet_;

    
    SET_LOGGER("FaintParticleTrigger");

};	// end of class 

#endif //I3_FAINT_PARTICLE_TRIGGER_NEW_H