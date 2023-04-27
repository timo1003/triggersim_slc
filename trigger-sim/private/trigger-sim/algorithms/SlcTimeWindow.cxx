#include "trigger-sim/algorithms/SlcTimeWindow.h"
#include <boost/foreach.hpp>

using namespace std;

SlcTimeWindow::SlcTimeWindow(unsigned int hit_min, unsigned int hit_max, double slcfraction_min,double window, double separation) 
  : hit_min_(hit_min), hit_max_(hit_max),slcfraction_min_(slcfraction_min), window_(window), separation_(separation) 
{
  SlctimeWindowHits_ = SlcTHitListPtr( new SlcTHitList() );
  SlctriggerWindowHits_ = SlcTHitListPtr( new SlcTHitList() );
}

SlcTimeWindow::~SlcTimeWindow() {}

/**
   Implementation of a sliding time window with a fixed sliding interval. All time windows for which the hit threshold is already satisfied are saved and returned.

 */

SlcTHitIterPairVectorPtr SlcTimeWindow::SlcFixedTimeWindows(SlcTHitVectorPtr hits,double separation)
{
  // The return variable is a std::vector of pairs, each pair is the begin/end iterators for the time window
  SlcTHitIterPairVectorPtr SlctriggerWindows(new SlcTHitIterPairVector());

  // Initialize the trigger condition
  // bool trigger = false;

  // Create the begin/end pointers
  SlcTHitVector::const_iterator beginHit;
  SlcTHitVector::const_iterator endHit;

  // Outer loop over all hits except the last
  // The iteration of startingHit is controlled by the sliding of the time window
    
  // set correct endtime:
  

  SlcTHitVector::const_iterator startingHit = hits->begin();
  // when hits->end()->time is used -> weird end times that does not correspond to one of the hits is chosen
  double endtime;  
  SlcTHitVector::const_iterator nextHit1;
  for (nextHit1 = hits->begin(); nextHit1 != hits->end(); nextHit1++) {

      endtime = nextHit1->time;
      //double endtime = nextHit1->time;
      }  
  //cout<<"starttimeme"<<hits->begin()->time<<endl;

  //cout<<"endtime"<<endtime<<endl;
  for (double timeWindowStart=startingHit->time; timeWindowStart< endtime; timeWindowStart+=separation){


    // Define the times of this trigger window
    double startTime = timeWindowStart;
    double stopTime  = startTime + window_;
    //cout <<"timewin"<<startTime<<endl;
    //cout <<"timewinend"<<stopTime<<endl;
    log_debug("TimeWindow = (%f, %f)", startTime, stopTime);
     
 
      
    // Initialize the counter (including startingHit)
    unsigned int count = 1;

    // Initialize the begin/end pointers
    //set beginHit hit for first time window  
    bool beginHit_set = false;
    if (timeWindowStart == hits->begin()->time) {
        
        beginHit = hits->begin(); 
        beginHit_set =true;
    }
    //Look for the first hit that is within the time window
    else {
  
        
    SlcTHitVector::const_iterator beginHit2;
    SlcTHitVector::const_iterator FirstHitInWindow;
    for (FirstHitInWindow = beginHit; FirstHitInWindow != hits->end(); FirstHitInWindow++) { 
            //Set the beginHit in the new timewindow
            if (FirstHitInWindow->time >= startTime && FirstHitInWindow->time <= stopTime){
                    beginHit=FirstHitInWindow;
                    beginHit_set = true;
                    break;
                    }
                    //time window is empty -> continue with the next one
              
            
        }
    }
    
    // no hit in the time window
    if (!beginHit_set){
        //cout<<"continu timewin is empty"<<endl;
        continue;
        }

    // Inner loop over all later hits
    SlcTHitVector::const_iterator nextHit;
    for (nextHit = beginHit + 1; nextHit != hits->end(); nextHit++) {
      
      // The time of the next hit
      double nextTime = nextHit->time;
      log_debug("  NextTime = %f", nextTime);

      // Check if it falls in the time window
      if (nextTime < startTime) {
    // error, hits should be time ordered
      } else if (nextTime < stopTime) {
    // in window, increment counter
    count++;
    log_debug("    Hit inside window, counter = %d", count);
      } else {
    // Hit is beyond window, check for trigger
    log_debug("    Hit outside window...");

    if (count >= hit_min_ && count <= hit_max_) {
      log_debug("      but we have a trigger, save pointers");
      endHit = nextHit;

      // Save the pointers
      //cout <<"timewin"<<startTime<<endl;
      //cout <<"timewinend"<<stopTime<<endl;
      //cout<<"save tw"<<beginHit->time<<endl;
      //cout<<"save tw end"<<endHit->time<<endl;
        
      int hlc_count = 0;
      int slc_count = 0;  
      SlcTHitVector::const_iterator nextHit2;
      for (nextHit2 = hits->begin(); nextHit2 != hits->end(); nextHit2++) {
            double hitTime = nextHit2->time;
            if (hitTime >=startTime && hitTime < stopTime){
            //std::cout<<"bed"<<slc<<std::endl;
                if (nextHit2->lc){
                    hlc_count++;
                    }
                else{
                    slc_count++;
                    }
            }
      }
      double slc_fraction = static_cast<double>(slc_count) / (slc_count + hlc_count);
      if (slc_fraction > slcfraction_min_) {
          /*
          cout <<"timewin"<<startTime<<endl;
          cout <<"timewinend"<<stopTime<<endl;
          cout <<"Hits timewindow"<<count<<endl;
          cout <<"SLCfrac timewin"<<slc_fraction<<endl;
          */
          SlcTHitIterPair SlctriggerWindow(beginHit, endHit);
          SlctriggerWindows->push_back(SlctriggerWindow);
          break;
       }

      // Set startingHit to endHit
    } 

      } // end time window check

    } // end inner loop

  } // end outer loop

  return SlctriggerWindows;
}


void SlcTimeWindow::DumpHits(SlcTHitList& hits, const string& head, const string& pad)
{

  log_debug("%s", head.c_str());
  int n = 0;
  BOOST_FOREACH( const SlcTHit& hit, hits ) {
    log_debug("%sHit %d @ Time %f", pad.c_str(), n, hit.time);
    n++;
  }

}

void SlcTimeWindow::CopyHits(SlcTHitList& sourceHits, SlcTHitList& destHits)
{

  // Copy from source to dest IFF source does not already exist in dest
  BOOST_FOREACH( SlcTHit sourceHit, sourceHits ) {
    if (find(destHits.begin(), destHits.end(), sourceHit) == destHits.end())
      destHits.push_back(sourceHit);
  }

}

bool SlcTimeWindow::Overlap(SlcTHitList& hits1, SlcTHitList& hits2)
{
  bool overlap = false;
  BOOST_FOREACH( SlcTHit hit1, hits1 ) {
    if (find(hits2.begin(), hits2.end(), hit1) != hits2.end()) {
      overlap = true;
      break;
    }
  }
  return overlap;
}
