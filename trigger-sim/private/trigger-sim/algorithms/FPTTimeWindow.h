#ifndef FPT_TIME_WINDOW_H
#define FPT_TIME_WINDOW_H

#include <string>
#include "trigger-sim/algorithms/FptHit.h"
#include "icetray/I3Logging.h"

/**
 * @brief A simple timewindow class used by the triggers.
 */

class FPTTimeWindow
{
 public:

  /**
   * Constructor requires a threshold and a time window (in ns)
   */
  FPTTimeWindow(unsigned int hit_min, unsigned int hit_max, double slcfraction_min, double time_window, double time_window_separation);

  ~FPTTimeWindow();


   //* Fixed time windows
 
  FptHitIterPairVectorPtr FPTFixedTimeWindows(FptHitVectorPtr hits,double separation);

 private:

  /**
   * Default constructor is private until we define defaults
   */
  FPTTimeWindow();

  void DumpHits(FptHitList& hits, const std::string& head, const std::string& pad);
  void CopyHits(FptHitList& sourceHits, FptHitList& destHits);
  bool Overlap(FptHitList& hits1, FptHitList& hits2);

  unsigned int hit_min_;
  unsigned int hit_max_;
  double slcfraction_min_;
  double time_window_;
  double time_window_separation_;

  FptHitListPtr FPTtimeWindowHits_;
  FptHitListPtr FPTtriggerWindowHits_;

  SET_LOGGER("FPTTimeWindow");
};

#endif // FPT_TIME_WINDOW_H
