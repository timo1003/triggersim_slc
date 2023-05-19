#include "trigger-sim/algorithms/FPTTimeWindow.h"
#include <boost/foreach.hpp>

using namespace std;
FPTTimeWindow::FPTTimeWindow(unsigned int hit_min, unsigned int hit_max, double slcfraction_min,double time_window, double time_window_separation) 
  : hit_min_(hit_min), hit_max_(hit_max),slcfraction_min_(slcfraction_min), time_window_(time_window), time_window_separation_(time_window_separation) 
{
  FPTtimeWindowHits_ = FptHitListPtr( new FptHitList() );
  FPTtriggerWindowHits_ = FptHitListPtr( new FptHitList() );
}

FPTTimeWindow::~FPTTimeWindow() {}

/**
   Implementation of a sliding time window with a fixed sliding interval. All time windows for which the hit threshold is already satisfied are saved and returned.

 */

FptHitIterPairVectorPtr FPTTimeWindow::FPTFixedTimeWindows(FptHitVectorPtr hits,double time_window_separation)
{
  // The return variable is a std::vector of pairs, each pair is the begin/end iterators for the time window
  FptHitIterPairVectorPtr FPTtriggerWindows(new FptHitIterPairVector());

  // Initialize the trigger condition
  // bool trigger = false;

  // Create the begin/end pointers
  FptHitVector::const_iterator beginHit;
  FptHitVector::const_iterator endHit;

  // Outer loop over all hits except the last
  // The iteration of startingHit is controlled by the sliding of the time window
    
  // set correct endtime:
  

  FptHitVector::const_iterator startingHit = hits->begin();
  // when hits->end()->time is used -> weird end times that does not correspond to one of the hits is chosen
  double endtime;  
  FptHitVector::const_iterator nextHit1;
  for (nextHit1 = hits->begin(); nextHit1 != hits->end(); nextHit1++) {

      endtime = nextHit1->time;
      //double endtime = nextHit1->time;
      }  
  //cout<<"starttimeme"<<hits->begin()->time<<endl;

  //cout<<"endtime"<<endtime<<endl;
  for (double timeWindowStart=startingHit->time; timeWindowStart< endtime; timeWindowStart+=time_window_separation){


    // Define the times of this trigger window
    double startTime = timeWindowStart;
    double stopTime  = startTime + time_window_;
    //cout <<"timewin"<<startTime<<endl;
    //cout <<"timewinend"<<stopTime<<endl;
    
    log_debug("TimeWindow = (%f, %f)", startTime, stopTime);
    /*
    if (global==26){
        cout<<"startTime"<<startTime<<endl;
        cout<<"startTime"<<stopTime<<endl;
    }
    */
   
      
    // Initialize the counter
    unsigned int count = 0;

    // Initialize the begin/end pointers
    //set beginHit hit for first time window  
    bool beginHit_set = false;
    if (timeWindowStart == hits->begin()->time) {
        
        beginHit = hits->begin(); 
        beginHit_set =true;
    }
    //Look for the first hit that is within the time window
    else {
  
        
    FptHitVector::const_iterator beginHit2;
    FptHitVector::const_iterator FirstHitInWindow;
    for (FirstHitInWindow = beginHit; FirstHitInWindow != hits->end(); FirstHitInWindow++) { 
            //Set the beginHit in the new timewindow
            if (FirstHitInWindow->time >= startTime && FirstHitInWindow->time < stopTime){
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
    FptHitVector::const_iterator nextHit;
    bool end_reached = false;
    for (nextHit = beginHit; nextHit != hits->end(); nextHit++) {
       
      // The time of the next hit
      double nextTime = nextHit->time;
      log_debug("  NextTime = %f", nextTime);
      
      // Check if it falls in the time window
      if (nextTime < startTime) {
    // error, hits should be time ordered
      } 
      else if (nextTime >= stopTime){
          end_reached = true;
          endHit = nextHit;
      }
        
      else if (nextTime < stopTime) {
    // in window, increment counter
        count++;
        if (nextTime == hits->back().time) {
  
         end_reached =true;
         endHit =hits->end();
            }
          
      }

    log_debug("    Hit inside window, counter = %d", count);
     if (end_reached ){
    // Hit is beyond window, check for trigger
    log_debug("    Hit outside window...");

    if (count >= hit_min_ && count <= hit_max_) {
      log_debug("      but we have a trigger, save pointers");
      

      // Save the pointers
     
      //cout<<"save tw"<<beginHit->time<<endl;
      //cout<<"save tw end"<<endHit->time<<endl;
        
      int hlc_count = 0;
      int slc_count = 0;  
      FptHitVector::const_iterator nextHit2;
      if (nextTime >= stopTime){
          for (nextHit2 = hits->begin(); nextHit2 != hits->end(); nextHit2++) {
                double hitTime = nextHit2->time;
                if (hitTime >=startTime && hitTime < stopTime){     
                    if (nextHit2->lc){
                        hlc_count++;
                        }
                    else{
                        slc_count++;
                        }
                }
          }
    }
      else{
              for (nextHit2 = hits->begin(); nextHit2 != hits->end(); nextHit2++) {
                double hitTime = nextHit2->time;
                if (hitTime >=startTime && hitTime <= stopTime){ 

                    if (nextHit2->lc){
                        hlc_count++;
                        }
                    else{
                        slc_count++;
                        }
                }
          
          
              }
          
      }
      double slc_fraction = static_cast<double>(slc_count) / (slc_count + hlc_count);
      if (slc_fraction > slcfraction_min_) {
          /*
          cout <<"Hits timewindow"<<count<<endl;
          cout <<"timewin"<<startTime<<endl;
          cout <<"timewinend"<<stopTime<<endl;
          cout <<"Hits timewindow"<<count<<endl;
          cout <<"SLCfrac timewin"<<slc_fraction<<endl;
         */
          FptHitIterPair FPTtriggerWindow(beginHit, endHit);
          FPTtriggerWindows->push_back(FPTtriggerWindow);
          break;
       }
       else {break;}

      // Set startingHit to endHit
    } 

      } // end time window check

    } // end inner loop

  } // end outer loop

  return FPTtriggerWindows;
}


void FPTTimeWindow::DumpHits(FptHitList& hits, const string& head, const string& pad)
{

  log_debug("%s", head.c_str());
  int n = 0;
  BOOST_FOREACH( const FptHit& hit, hits ) {
    log_debug("%sHit %d @ Time %f", pad.c_str(), n, hit.time);
    n++;
  }

}

void FPTTimeWindow::CopyHits(FptHitList& sourceHits, FptHitList& destHits)
{

  // Copy from source to dest IFF source does not already exist in dest
  BOOST_FOREACH( FptHit sourceHit, sourceHits ) {
    if (find(destHits.begin(), destHits.end(), sourceHit) == destHits.end())
      destHits.push_back(sourceHit);
  }

}

bool FPTTimeWindow::Overlap(FptHitList& hits1, FptHitList& hits2)
{
  bool overlap = false;
  BOOST_FOREACH( FptHit hit1, hits1 ) {
    if (find(hits2.begin(), hits2.end(), hit1) != hits2.end()) {
      overlap = true;
      break;
    }
  }
  return overlap;
}