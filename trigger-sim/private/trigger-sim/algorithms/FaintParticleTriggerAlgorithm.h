/**
 * copyright  (C) 2006
 * the icecube collaboration
 * $Id: 
 *
 * @file SimpleMajorityTriggerAlgorithm.h
 * @version
 * @date
 * @author toale
 */

#ifndef FAINT_PARTICLE_TRIGGER_ALGORITHM_H
#define FAINT_PARTICLE_TRIGGER_ALGORITHM_H

#include "icetray/I3Logging.h"
#include "trigger-sim/algorithms/FptHit.h"
#include "dataclasses/geometry/I3Geometry.h"

/**

   The SimpleMajorityTriggerAlgorithm class is a port the DAQ trigger algorithm 
   of the same name. The algorithm has 2 configuration parameters:

   1) TriggerWindow: The length of the sliding time window used to define
                     an interesting time period.

   2) TriggerThreshold: The minimum number of hits that must be present within
                        a time period of TriggerWindow.

   A trigger is satisified if there are at least TriggerThreshold hits in a time
   window of length TriggerWindow.

   The algorithm works in one steps:

   1) Find a time window: A sliding time window is applied to each hit and the 
      number of hits falling in it is counted. As long as the threshold condition
      is meet, the widow will continue to slide. Once the number of hits drops
      below the threshold, a trigger is defined which includes all hits that were
      part of any valid window. A hit cannot be part of more than one active
      time window.

   When a trigger is found, the hits that are included are any that were in the 
   time window. The trigger start will be the earliest hit time in the time window
   and the trigger stop will be the latest hit time in the time window.

   A time window with multiple indepent clusters of hits will only produce a single
   trigger, but all hits in the time window will be used to define the length of the
   trigger
   
   
 */

class FaintParticleTriggerAlgorithm
{

 public:
  FaintParticleTriggerAlgorithm(double time_window,double time_window_separation, double max_trigger_length,  unsigned int hit_min,unsigned int hit_max,double double_velocity_min,double double_velocity_max, unsigned int double_min, bool use_dc_version, unsigned int triple_min,unsigned int azimuth_histogram_min,unsigned int zenith_histogram_min, double histogram_binning, double slcfraction_min, const I3GeometryConstPtr &geo);
  ~FaintParticleTriggerAlgorithm();




  void AddHits(FptHitVectorPtr hits, const I3GeometryConstPtr &geo);

  unsigned int GetNumberOfTriggers();
  FptHitVectorPtr GetNextTrigger();
  std::vector<int> DoubleThreshold(FptHitVectorPtr timeWindowHits, const I3GeometryConstPtr &geo);
  double getDistance(FptHit hit1,FptHit hit2,const I3GeometryConstPtr &geo);
  unsigned int TripleThreshold(FptHitVectorPtr timeWindowHits,std::vector<int> Double_Indices, const I3GeometryConstPtr &geo);
  std::vector<double> getDirection(FptHitVectorPtr timeWindowHits, std::vector<int> Double_Indices, const I3GeometryConstPtr &geo);
  std::vector<double> CalcHistogram(std::vector<double> Angles, int lower_bound, int upper_bound, int bin_size);
 private:

  double time_window_;
  double time_window_separation_;
  double max_trigger_length_;
  unsigned int hit_min_;
  unsigned int hit_max_;
  double double_velocity_min_;
  double double_velocity_max_;
  unsigned int double_min_;
  bool use_dc_version_;
  unsigned int triple_min_;
  unsigned int azimuth_histogram_min_; 
  unsigned int zenith_histogram_min_;
  double histogram_binning_;
  double slcfraction_min_;
  FptHitVectorVector triggers_;
  FptHitVectorVector triggers_current_;
  unsigned int triggerCount_;
  unsigned int triggerIndex_;

  SET_LOGGER("FaintParticleTriggerAlgorithm");
};

#endif
