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

#ifndef SLC_TRIGGER_ALGORITHM_H
#define SLC_TRIGGER_ALGORITHM_H

#include "icetray/I3Logging.h"
#include "trigger-sim/algorithms/SlcTHit.h"
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
   trigger.
   
 */

class SlcTriggerAlgorithm
{

 public:
  SlcTriggerAlgorithm(double triggerWindow,double separation, bool triple_bool, unsigned int hit_min,unsigned int hit_max, unsigned int double_min, unsigned int double_max, unsigned int triple_min,unsigned int triple_max,unsigned int azi_min,unsigned int zen_min, double binning, double slcfraction_min, double cut_veldoublet_min,double cut_veldoublet_max, const I3GeometryConstPtr &geo);
  ~SlcTriggerAlgorithm();

  void AddHits(SlcTHitVectorPtr hits, const I3GeometryConstPtr &geo);

  unsigned int GetNumberOfTriggers();
  SlcTHitVectorPtr GetNextTrigger();
  std::vector<int> DoubleThreshold(SlcTHitVectorPtr timeWindowHits, const I3GeometryConstPtr &geo);
  double getDistance(SlcTHit hit1,SlcTHit hit2,const I3GeometryConstPtr &geo);
  unsigned int TripleThreshold(SlcTHitVectorPtr timeWindowHits,std::vector<int> Double_Indices, const I3GeometryConstPtr &geo);
  std::vector<double> getDirection(SlcTHitVectorPtr timeWindowHits, std::vector<int> Double_Indices, const I3GeometryConstPtr &geo);
  std::vector<double> CalcHistogram(std::vector<double> Angles, int lower_bound, int upper_bound, int bin_size);
 private:

  double triggerWindow_;
  bool triple_bool_;
  unsigned int hit_min_;
  unsigned int hit_max_;
  unsigned int double_min_;
  unsigned int double_max_;
  unsigned int triple_min_;
  unsigned int triple_max_;
  unsigned int azi_min_; 
  unsigned int zen_min_;
  double binning_;
  double slcfraction_min_;
  double cut_veldoublet_min_;
  double cut_veldoublet_max_;
  double separation_;
  SlcTHitVectorVector triggers_;
  unsigned int triggerCount_;
  unsigned int triggerIndex_;

  SET_LOGGER("SlcTriggerAlgorithm");
};

#endif
