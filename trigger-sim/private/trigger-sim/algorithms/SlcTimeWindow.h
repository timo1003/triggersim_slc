#ifndef SLC_TIME_WINDOW_H
#define SLC_TIME_WINDOW_H

#include <string>
#include "trigger-sim/algorithms/SlcTHit.h"
#include "icetray/I3Logging.h"

/**
 * @brief A simple timewindow class used by the triggers.
 */

class SlcTimeWindow
{
 public:

  /**
   * Constructor requires a threshold and a time window (in ns)
   */
  SlcTimeWindow(unsigned int hit_min, unsigned int hit_max, double slcfraction_min, double window, double separation);

  ~SlcTimeWindow();


   //* Fixed time windows
 
  SlcTHitIterPairVectorPtr SlcFixedTimeWindows(SlcTHitVectorPtr hits,double separation);

 private:

  /**
   * Default constructor is private until we define defaults
   */
  SlcTimeWindow();

  void DumpHits(SlcTHitList& hits, const std::string& head, const std::string& pad);
  void CopyHits(SlcTHitList& sourceHits, SlcTHitList& destHits);
  bool Overlap(SlcTHitList& hits1, SlcTHitList& hits2);

  unsigned int hit_min_;
  unsigned int hit_max_;
  double slcfraction_min_;
  double window_;
  double separation_;

  SlcTHitListPtr SlctimeWindowHits_;
  SlcTHitListPtr SlctriggerWindowHits_;

  SET_LOGGER("SlcTimeWindow");
};

#endif // SLC_TIME_WINDOW_H
