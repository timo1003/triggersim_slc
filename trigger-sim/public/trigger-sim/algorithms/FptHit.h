#ifndef FPTHIT_H
#define FPTHIT_H

#include <vector>
#include <list>
#include "dataclasses/I3Map.h"

/**
 * Fpt_Trigger_Hit
 *
 * A simple hit class used by the trigger-sim.
 * derived from trigger-sim/TriggerHit.h
 *
 */

class FptHit
{
 public:
  FptHit() : time(0), pos(0), lc(0), string(0) {}
  FptHit(double aTime, unsigned int aPos, int aLc, int aString) : time(aTime), pos(aPos), lc(aLc), string(aString) {}

  double time;
  int pos;
  int lc;
  int string;
  double x;
  double y;
  double z;

  bool operator<(const FptHit& rhs) const { return time < rhs.time; }
  bool operator==(const FptHit& rhs) const { return ( (pos == rhs.pos) && (time == rhs.time) && (string == rhs.string) ); }

};

typedef std::vector<FptHit> FptHitVector;
typedef std::vector<FptHitVector> FptHitVectorVector;
typedef I3Map<int, FptHitVector> IntFptHitVectorMap;
typedef I3Map<FptHit, int> FptHitIntMap;
typedef std::pair<FptHitVector::const_iterator, FptHitVector::const_iterator> FptHitIterPair;
typedef std::vector<FptHitIterPair> FptHitIterPairVector;
typedef std::list<FptHit> FptHitList;

I3_POINTER_TYPEDEFS(FptHit);
I3_POINTER_TYPEDEFS(FptHitVector);
I3_POINTER_TYPEDEFS(FptHitVectorVector);
I3_POINTER_TYPEDEFS(IntFptHitVectorMap);
I3_POINTER_TYPEDEFS(FptHitIntMap);
I3_POINTER_TYPEDEFS(FptHitIterPair);
I3_POINTER_TYPEDEFS(FptHitIterPairVector);
I3_POINTER_TYPEDEFS(FptHitList);

typedef std::vector<FptHitPtr> FptHitPtrVector;

#endif // FPTHIT_H
