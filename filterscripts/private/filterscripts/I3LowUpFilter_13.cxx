/** 
 * copyright  (C) 2008
 * the icecube collaboration
 * $Id:$
 * 
 * @version: $Revision:00-00-01$
 * @file I3LowUpFilter_13.cxx
 * @date $Date: 03 Sept 2012$
 * comments: for IC86-III, 2013
 * @author wikstrom + updated danninger + updated mzoll
 **/

#include "filterscripts/I3LowUpFilter_13.h"

#include "filterscripts/I3FilterModule.h"
I3_MODULE(I3FilterModule<I3LowUpFilter_13>);

#include "icetray/OMKey.h"
#include "dataclasses/physics/I3RecoPulse.h"
#include "dataclasses/physics/I3Particle.h"
#include "dataclasses/geometry/I3Geometry.h"
#include "dataclasses/geometry/I3OMGeo.h"
#include "dataclasses/I3Position.h"
#include "icetray/I3Units.h"
#include <vector>
#include <string>
#include "CommonVariables/hit_multiplicity/calculator.h"
#include "CommonVariables/hit_statistics/calculator.h"

#include <boost/assign/list_of.hpp>
#include <list>
#include <stdlib.h>

using namespace std;

I3LowUpFilter_13 :: I3LowUpFilter_13(const I3Context& context) : I3JEBFilter(context),
recoPulsesName_(""), 
tracknamelist_(1,""),
nchanCut_(4),
zenithCut_(80.),
zExtensionCut_(600.),
timeExtensionCut_(4000.),
zTravelCut_(-10.),
zMaxCut_(440.),
iSCritActive_(true),
nRejNoPulses(0), nRejNoHits(0), nRejNch(0), nRejZen(0), nRejZExt(0), nRejTExt(0), nRejZTravel(0), nRejNoTrack(0), nRejZMax(0), nRejInnerString(0), nPassedTot (0)
{
  AddParameter("Pulses","Name of reco pulse series map to be used",recoPulsesName_);
  AddParameter("RecoTrackNameList","List of Track Recos considered by filter (priority ordered; first entry has highest)", tracknamelist_ );
  AddParameter("nchanCut", "Filter parameter", nchanCut_);
  AddParameter("zTravelCut", "The tuning parameter", zTravelCut_);
  AddParameter("zenithCut", "Filter parameter", zenithCut_);
  AddParameter("zExtensionCut", "Filter parameter", zExtensionCut_);
  AddParameter("timeExtensionCut", "Filter parameter", timeExtensionCut_);
  AddParameter("zMaxCut", "Veto everything above this z", zMaxCut_);
  AddParameter("ISCrit", "Perform InnerString-Criterion", iSCritActive_);
}

void I3LowUpFilter_13 :: Configure()
{
  GetParameter("Pulses", recoPulsesName_);
  GetParameter("RecoTrackNameList", tracknamelist_ );
  GetParameter("nchanCut", nchanCut_);
  GetParameter("zTravelCut", zTravelCut_);
  GetParameter("zenithCut", zenithCut_);
  GetParameter("zExtensionCut", zExtensionCut_);
  GetParameter("timeExtensionCut", timeExtensionCut_);
  GetParameter("zMaxCut", zMaxCut_);
  GetParameter("ISCrit", iSCritActive_);
  
  //create lookuptable for IC86
  outerStrings.assign(86+1,false);
  outerStrings[1] = true;
  outerStrings[2] = true;
  outerStrings[3] = true;
  outerStrings[4] = true;
  outerStrings[5] = true;
  outerStrings[6] = true;
  outerStrings[13] = true;
  outerStrings[21] = true;
  outerStrings[30] = true;
  outerStrings[40] = true;
  outerStrings[50] = true;
  outerStrings[59] = true;
  outerStrings[67] = true;
  outerStrings[74] = true;
  outerStrings[73] = true;
  outerStrings[78] = true;
  outerStrings[77] = true;
  outerStrings[76] = true;
  outerStrings[75] = true;
  outerStrings[68] = true;
  outerStrings[60] = true;
  outerStrings[51] = true;
  outerStrings[41] = true;
  outerStrings[31] = true;
  outerStrings[22] = true;
  outerStrings[14] = true;
  outerStrings[7] = true;
}

bool I3LowUpFilter_13 :: KeepEvent(I3Frame& frame)
{
  log_debug("eventid %i", frame.Get<I3EventHeaderConstPtr>("I3EventHeader")->GetEventID());
  
  I3GeometryConstPtr geometry = frame.Get<I3GeometryConstPtr>();
  
  I3RecoPulseSeriesMapConstPtr recoMap = frame.Get<I3RecoPulseSeriesMapConstPtr>(recoPulsesName_);
  
// Check HLC Map
  if (recoMap){
    log_debug("Found pulses");
  }else{
    log_debug("No pulses, skipping event");
    nRejNoPulses++;
    return false;
  }
  
  if (recoMap->size()<2){
    log_debug("Too few events");
    nRejNoHits++;
    return false;
  }
  
  // Get zenith
  double track_zenith = 0.;
  bool goodtrack = false;
  int size = (int)(tracknamelist_.size());
  for (int i=0; i<size; i++) {
    I3ParticleConstPtr track = frame.Get<I3ParticleConstPtr>(tracknamelist_[i]);
    if (track && (track->GetFitStatus() == I3Particle::OK)) {
      track_zenith = track->GetZenith();
      goodtrack = true;
      log_debug("Found good track: %s", tracknamelist_[i].c_str());
      break;
    }
  }
  if (!goodtrack) {
    log_debug("No good track, skipping event");
    nRejNoTrack++;
    return false;
  }
  
  // Zenith Cut
  if (track_zenith < zenithCut_){
    log_debug("Rejected: NO track_zen<zenithCut_: %f<%f", track_zenith, zenithCut_);
    nRejZen++;
    return false;
  }
  log_debug("Passed track_zenith<zenithCut_: %f<%f", track_zenith, zenithCut_);
  
  unsigned int nch = (common_variables::hit_multiplicity::CalculateHitMultiplicity(*geometry, *recoMap)->GetNHitDoms());
  double z_travel = common_variables::hit_statistics::CalculateZTravel(*geometry, *recoMap)->value;
  double z_max = common_variables::hit_statistics::CalculateZMax(*geometry, *recoMap)->value;
  double z_ext = z_max - common_variables::hit_statistics::CalculateZMin(*geometry, *recoMap)->value;
  double t_ext = common_variables::hit_statistics::CalculateMaxPulseTime(*geometry, *recoMap)->value - common_variables::hit_statistics::CalculateMinPulseTime(*geometry, *recoMap)->value;
 
  // Nchan Cut
  if (nch < nchanCut_){
    log_debug("Rejected: NO nch < nchanCut_: %i < %i", (int)nch, (int)nchanCut_);
    nRejNch++;
    return false;
  }
  log_debug("Passed nch<=nchanCut_: %i <= %i", (int)nch, (int)nchanCut_);
  
  // Z_Extension Cut
  if (z_ext > zExtensionCut_){
    log_debug("Rejected: NO z_ext > zExtensionCut_: %f > %f", z_ext, zExtensionCut_);
    nRejZExt++;
    return false;
  }
  log_debug("Passed z_ext< = zExtensionCut_: %f <= %f", z_ext, zExtensionCut_);
  
  // T_Extension Cut
  if (t_ext > timeExtensionCut_) {
    log_debug("Rejected: NO t_ext > timeExtensionCut_: %f > %f", t_ext, timeExtensionCut_);
    nRejTExt++;
    return false;
  }
  log_debug("Passed t_ext <= timeExtensionCut_: %f <= %f", t_ext, timeExtensionCut_);
  
  // Z_travel Cut
  if (z_travel < zTravelCut_){
    log_debug("Rejected: NO z_travel < zCut: %f < %f", z_travel, zTravelCut_);
    nRejZTravel++;
    return false;
  }
  log_debug("Passed z_travel >= zTravelCut_: %f >= %f", z_travel, zTravelCut_);
  
  // Top Veto Cut
  if (z_max > zMaxCut_) {
    log_debug("Rejected: NO z_max > ZMaxCut_: %f > %f", z_max, zMaxCut_);
    nRejZMax++;
    return false;
  }
  log_debug("Passed z_max <= ZMaxCut_: %f <= %f", z_max, zMaxCut_);
  
  // Inner String Criterion: Require an inner string, and a second hit in any other string
  if (iSCritActive_){
    bool ISCrit = InnerStringCriterion(recoMap);
    if (not ISCrit) {
      log_debug("Failed InnerStringCriterion");
      nRejInnerString++;
      return false;
    }
    log_debug("Passed InnerStringCriterion");
  }
  
  // Finishing the module
  log_debug("---Event passed all filter requirements---");
  nPassedTot++;
  return true;
}

bool I3LowUpFilter_13::InnerStringCriterion(I3RecoPulseSeriesMapConstPtr recoMap) {
  map<int,bool> strings;
  bool foundInnerString = false;
  bool foundSecondString = false;
  for(I3RecoPulseSeriesMap::const_iterator reco_iter=recoMap->begin(); reco_iter != recoMap->end(); reco_iter++) {
    strings[reco_iter->first.GetString()] = true;
    if(strings.size()>1) foundSecondString = true;
    if(outerStrings[reco_iter->first.GetString()] == false) foundInnerString = true;
    if(foundSecondString && foundInnerString) {
      return true;
    }
  }
  return false;
}

void I3LowUpFilter_13 :: Finish()
{
  log_debug("LowUpFilter_13****************************");
  log_debug("Cut Parameters:");
  log_debug("  zenith > %f", zenithCut_);
  log_debug("  nchan > %d", nchanCut_);
  log_debug("  zTravel > %f", zTravelCut_);
  log_debug("  zExtension < %f", zExtensionCut_);
  log_debug("  timeExtension < %f", timeExtensionCut_);
  log_debug("  zenith < %f", zenithCut_);
  log_debug("  ZMax < %f", zMaxCut_);
  log_debug("  ISCrit applied = %i",int(iSCritActive_));
  log_debug("Rejected because of missing Pulses: %d", nRejNoPulses);
  log_debug("Rejected because of few hits    : %d", nRejNoHits);
  log_debug("Rejected because of missing track : %d", nRejNoTrack);
  log_debug("Rejected because of Zenith        : %d", nRejZen);
  log_debug("Rejected because of Nch           : %d", nRejNch);
  log_debug("Rejected because of ZExtension    : %d", nRejZExt);
  log_debug("Rejected because of TimeExtension : %d", nRejTExt);
  log_debug("Rejected because of ZTravel       : %d", nRejZTravel);
  log_debug("Rejected because of ZMax          : %d", nRejZMax);
  log_debug("Rejected because of inner string  : %d", nRejInnerString);
  log_debug("-------------------------------------------");
  log_debug("Total number rejected: %d", (nRejNoPulses+ nRejNoHits+ nRejNch+ nRejZen+ nRejZExt+ nRejTExt+ nRejZTravel+ nRejNoTrack+ nRejZMax+ nRejInnerString)); 
  log_debug("Total number passed  : %d", nPassedTot);
}
