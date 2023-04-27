#ifndef SLC_T_HIT_H
#define SLC_T_HIT_H

#include <vector>
#include <list>
#include "dataclasses/I3Map.h"

/**
 * Slc_Trigger_Hit
 *
 * A simple hit class used by the trigger-sim.
 * derived from trigger-sim/TriggerHit.h
 *
 */

class SlcTHit
{
 public:
  SlcTHit() : time(0), pos(0), lc(0), string(0) {}
  SlcTHit(double aTime, unsigned int aPos, int aLc, int aString) : time(aTime), pos(aPos), lc(aLc), string(aString) {}

  double time;
  int pos;
  int lc;
  int string;
  double x;
  double y;
  double z;

  bool operator<(const SlcTHit& rhs) const { return time < rhs.time; }
  bool operator==(const SlcTHit& rhs) const { return ( (pos == rhs.pos) && (time == rhs.time) && (string == rhs.string) ); }

};

typedef std::vector<SlcTHit> SlcTHitVector;
typedef std::vector<SlcTHitVector> SlcTHitVectorVector;
typedef I3Map<int, SlcTHitVector> IntSlcTHitVectorMap;
typedef I3Map<SlcTHit, int> SlcTHitIntMap;
typedef std::pair<SlcTHitVector::const_iterator, SlcTHitVector::const_iterator> SlcTHitIterPair;
typedef std::vector<SlcTHitIterPair> SlcTHitIterPairVector;
typedef std::list<SlcTHit> SlcTHitList;

I3_POINTER_TYPEDEFS(SlcTHit);
I3_POINTER_TYPEDEFS(SlcTHitVector);
I3_POINTER_TYPEDEFS(SlcTHitVectorVector);
I3_POINTER_TYPEDEFS(IntSlcTHitVectorMap);
I3_POINTER_TYPEDEFS(SlcTHitIntMap);
I3_POINTER_TYPEDEFS(SlcTHitIterPair);
I3_POINTER_TYPEDEFS(SlcTHitIterPairVector);
I3_POINTER_TYPEDEFS(SlcTHitList);

typedef std::vector<SlcTHitPtr> SlcTHitPtrVector;

#endif // SLOW_MP_HIT_H
