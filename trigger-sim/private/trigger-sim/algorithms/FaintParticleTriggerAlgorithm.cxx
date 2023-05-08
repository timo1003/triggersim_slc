/**
 * copyright  (C) 2006
 * the icecube collaboration
 * $Id:
 *
 * @file FaintParticleTriggerAlgorithm.cxx
 * @version
 * @date
 * @author toale
 */

#include <trigger-sim/algorithms/FaintParticleTriggerAlgorithm.h>
#include <trigger-sim/algorithms/FPTTimeWindow.h>
#include <boost/foreach.hpp>
#include <boost/assign/std/vector.hpp>
#include "trigger-sim/algorithms/FptHit.h"
#include "dataclasses/geometry/I3Geometry.h"
#include <dataclasses/I3Direction.h>
#include <icetray/I3Units.h>
using namespace boost::assign;
 double double_velocity_min_;
  double double_velocity_max_;
  unsigned int double_min_;
  bool use_dc_version_;
  unsigned int triple_min_;
  unsigned int azimuth_histogram_min_; 
  unsigned int zenith_histogram_min_;
  double histogram_binning_;
  double slcfraction_min_;
FaintParticleTriggerAlgorithm::FaintParticleTriggerAlgorithm(double time_window,double time_window_separation, double max_trigger_length, unsigned int hit_min,unsigned int hit_max,double double_velocity_min,double double_velocity_max, unsigned int double_min,bool use_dc_version, unsigned int triple_min, unsigned int azimuth_histogram_min,unsigned int zenith_histogram_min, double histogram_binning, double slcfraction_min,  const I3GeometryConstPtr &geo) : 
  time_window_(time_window),
  time_window_separation_(time_window_separation),
  max_trigger_length_(max_trigger_length),
  hit_min_(hit_min),
  hit_max_(hit_max),
  double_velocity_min_(double_velocity_min),
  double_velocity_max_(double_velocity_max),
  double_min_(double_min),
  use_dc_version_(use_dc_version),
  triple_min_(triple_min), 
  azimuth_histogram_min_(azimuth_histogram_min), 
  zenith_histogram_min_(zenith_histogram_min), 
  histogram_binning_(histogram_binning), 
  slcfraction_min_(slcfraction_min), 
 
  triggerCount_(0),
  triggerIndex_(0)
{

  log_debug("FaintParticleTriggerAlgorithm configuration:");
  log_debug("  TriggerWindow = %f", time_window_);
  log_debug("  hit_min = %d", hit_min_);
  log_debug("  hit_max = %d", hit_max_);

}

FaintParticleTriggerAlgorithm::~FaintParticleTriggerAlgorithm() {}

void FaintParticleTriggerAlgorithm::AddHits(FptHitVectorPtr hits,const I3GeometryConstPtr &geo)
{

  log_debug("Adding %zd hits to FaintParticleTigger", hits->size());

  /*------------------------------------------------------------*
   * Check Trigger condition
   *------------------------------------------------------------*/
  FPTTimeWindow FPTtimeWindow(hit_min_,hit_max_,slcfraction_min_, time_window_,time_window_separation_);
  triggers_.clear();
  triggers_current_.clear();
  triggerCount_ = 0;
  triggerIndex_ = 0;
  
  // Get time windows
  FptHitIterPairVectorPtr timeWindows = FPTtimeWindow.FPTFixedTimeWindows(hits,time_window_separation_);

  // If the vector is empty, there are no time windows for this string
  if (timeWindows->empty()) {
    log_debug("No valid time windows for this string");
    return;
  }
  log_debug("Found %zd triggered time windows", timeWindows->size());
  FptHitVectorPtr timeHits_current(new FptHitVector);
  bool max_extended = false;
  // Loop over the time windows and pull out the hits in each
  for (FptHitIterPairVector::const_iterator timeWindowIter = timeWindows->begin(); 
       timeWindowIter != timeWindows->end(); 
       timeWindowIter++) {

    // Create a vector of the hits in this time window
    FptHitVectorPtr timeHits(new FptHitVector);
    // Get the window boundaries
    FptHitVector::const_iterator firstHit = timeWindowIter->first;
    FptHitVector::const_iterator lastHit  = timeWindowIter->second;
    


    // Iterate over the hits and pull out the ones for this window
    for (FptHitVector::const_iterator hitIter = firstHit; 
     hitIter != lastHit; 
     hitIter++){
      timeHits->push_back(*hitIter);
      //std::cout <<"Hit time"<<hitIter->time<<std::endl;
    }
    //Second cut: number of Doubles
    std::vector<int> Double_Indices = DoubleThreshold(timeHits, geo);
    unsigned int number_doubles = Double_Indices.size()/2;
    if (number_doubles >= double_min_ ){
        
        //Third cut on directional clustering or triple cut

        bool cut3 = false;
        if (use_dc_version_){
            
            std::vector<double> dir = getDirection(timeHits,Double_Indices,geo);
            unsigned int number_azimuth = dir[0];
            double mean_azimuth = dir[1];
            unsigned int number_zenith = dir[2];
            double mean_zenith = dir[3];
            if (number_zenith > zenith_histogram_min_ && number_azimuth > azimuth_histogram_min_) {
                cut3 = true;             
                }

            }
        else{
            unsigned int number_triples = TripleThreshold(timeHits,Double_Indices,geo);
            if (number_triples > triple_min_ ){
                cut3 = true;
                }
                       
        }

            
            if (cut3){
            /*
                 std::cout <<"TW first hit"<<timeHits->begin()->time<<std::endl;
                 std::cout <<"TWlast hit"<<timeHits->end()->time<<std::endl;
                 std::cout <<"Hits"<<(*timeHits).size()<<std::endl;
                 std::cout <<"doubles"<<number_doubles<<std::endl;
                 */
                 //Check if previous window was above threshold
                 if (timeHits_current->size()>0){
                     for (auto it = timeHits->begin(); it != timeHits->end(); ++it) {
                        // Check if the current element already exists in timeHits_current
                        if (std::find(timeHits_current->begin(), timeHits_current->end(), *it) == timeHits_current->end()) {
                            // If it doesn't exist, insert it into timeHits_current
                            timeHits_current->push_back(*it);
                        }
                    }
                     /*
                     std::cout <<"Extended trigger begin"<<timeHits_current->front().time<<std::endl;
                     std::cout <<"Extended end"<<timeHits_current->back().time<<std::endl;
                     std::cout <<"Hits"<<(*timeHits).size()<<std::endl;
                     std::cout <<"doubles"<<number_doubles<<std::endl;
                     */
                     
                     //only unique=
                     double trigger_length = timeHits_current->back().time - timeHits_current->front().time;
                     if (trigger_length > max_trigger_length_){
                     
                         triggers_.push_back(*timeHits_current);
                         triggerCount_++;
                         timeHits_current->clear();
                         max_extended = true;
                          }
                     //if we are at the last time window of the event and the trigger was not flushd by the max trigger length parameter flush it
                     if (timeWindowIter == timeWindows->end() - 1) {
                         if (max_extended ==false){
                             triggers_.push_back(*timeHits_current);
                             triggerCount_++;
                                }
                     
                     }

                     
                    
                 }
                     
                 

                else {
                    /*
                    std::cout <<"trigger begin"<<timeHits->front().time<<std::endl;
                    std::cout <<"end"<<timeHits->back().time<<std::endl;
                    std::cout <<"Hits"<<(*timeHits).size()<<std::endl;
                    std::cout <<"doubles"<<number_doubles<<std::endl;
                    */
                    
                    for (auto it = timeHits->begin(); it != timeHits->end(); ++it) {
                            timeHits_current->push_back(*it);
                        }
                    
                    // write out the trigger if we are at the last time window.
                    if (timeWindowIter == timeWindows->end() - 1) {
                         triggers_.push_back(*timeHits_current);
                         triggerCount_++;
        // Do something special for the last element
    }
                    }
        

            
        }
        else{
        //Check if previous window was above threshold
                     if (timeHits_current->size()>0){
                         triggers_.push_back(*timeHits_current);
                         triggerCount_++;
                         timeHits_current->clear();

                     }


        }




    }
    else {
    //Check if previous window was above threshold
                 if (timeHits_current->size()>0){
                     triggers_.push_back(*timeHits_current);
                     triggerCount_++;
                     timeHits_current->clear();


             }
  
    }
   }
}



unsigned int FaintParticleTriggerAlgorithm::GetNumberOfTriggers() {
  return triggerCount_;
}

FptHitVectorPtr FaintParticleTriggerAlgorithm::GetNextTrigger() {
  FptHitVectorPtr hits;
  if (triggerCount_ > 0) {
    log_debug("Returning trigger window %d", triggerIndex_);
    hits = FptHitVectorPtr(new FptHitVector(triggers_.at(triggerIndex_)));
    triggerCount_--;
    triggerIndex_++;
  }
  return hits;
}

std::vector<int> FaintParticleTriggerAlgorithm::DoubleThreshold(FptHitVectorPtr timeWindowHits, const I3GeometryConstPtr &geo)
{
    std::vector<int> Doubles;
    unsigned int double_combinations =0;
    int ind_hit_1 = -1;
    //Second loop starts from first element
    
    for (FptHitVector::const_iterator hitIter1 = timeWindowHits->begin(); hitIter1 != timeWindowHits->end(); hitIter1++) {   
        ind_hit_1++;
        int ind_hit_2 = ind_hit_1;
            for (FptHitVector::const_iterator hitIter2 = hitIter1+1; hitIter2 != timeWindowHits->end(); hitIter2++) {
                ind_hit_2++;
                FptHit hit1 = *hitIter1;
                FptHit hit2 = *hitIter2;
                OMKey omkey1(hit1.string, hit1.pos);
                OMKey omkey2(hit2.string, hit2.pos);
                if (omkey1 != omkey2){
                    //std::cout<<"double loop"<<hitIter1->time<<std::endl;
                    //std::cout<<"double loop2"<<hitIter2->time<<std::endl;
                    double distance = getDistance(*hitIter1, *hitIter2, geo);
                    double time = abs(hit2.time - hit1.time);
                    //in km/s
                    double velocity = 1e6*distance/time;
                    //std::cout<<"distance"<<velocity<<std::endl;
                    if (velocity> double_velocity_min_ && velocity <double_velocity_max_){
                        double_combinations++;
                        //Threshold exceeded: return empty list -> below cut threshold
                                             
                            
                        
                            
                        Doubles.push_back(ind_hit_1);
                        Doubles.push_back(ind_hit_2);

                        }
                    
                    }
                }
                    
            }
    
    
   
    
    return Doubles;
}

unsigned int FaintParticleTriggerAlgorithm::TripleThreshold(FptHitVectorPtr timeWindowHits,std::vector<int> Double_Indices, const I3GeometryConstPtr &geo)
{
    unsigned int triple_combinations =0;
    int loop_end = Double_Indices.size();
    for (int j = 0; j < loop_end-2; j+= 2) {
            for (int k = j + 2; k <= loop_end-2; k += 2) {
                //Check for two doubles that share the middle hit in time (0,1) (1,2) -> (0,1,2)
                int hit1_ind = Double_Indices[j+1];
                int hit2_ind =Double_Indices[k];
                if ( hit1_ind != hit2_ind )
                {
                    FptHit hit1 = (*timeWindowHits)[Double_Indices[j]];
                    FptHit hit2 = (*timeWindowHits)[Double_Indices[k+1]]; 
                    OMKey omkey1(hit1.string, hit1.pos);
                    OMKey omkey2(hit2.string, hit2.pos);
                    if (omkey1 != omkey2){
                        // As the doublets are velocity consistent only the third component (0-2) is checked
                        
                        double distance = getDistance(hit1, hit2, geo);
                        double time = abs(hit2.time - hit1.time);
                        //in km/s
                        double velocity = 1e6*distance/time;
                        if (velocity> double_velocity_min_ && velocity <double_velocity_max_){
                            triple_combinations++;
                            //stop calculating if threshold is exceeded
                            
                        }
                       
                        
                    }
                }
    
            }
     }
    
    
    
    return triple_combinations;
}

//function from SLOP trigger to calculate the distance between to OMs
double FaintParticleTriggerAlgorithm::getDistance(FptHit hit1, FptHit hit2,const I3GeometryConstPtr &geo)
{
  I3OMGeoMap::const_iterator geo_iterator_1 = geo->omgeo.find(OMKey(hit1.string, hit1.pos));
  I3OMGeoMap::const_iterator geo_iterator_2 = geo->omgeo.find(OMKey(hit2.string, hit2.pos));
  //std::cout<<"omkey"<<geo_iterator_1<<std::endl;

  double x1 = geo_iterator_1->second.position.GetX();
  double y1 = geo_iterator_1->second.position.GetY();
  double z1 = geo_iterator_1->second.position.GetZ();
  double x2 = geo_iterator_2->second.position.GetX();
  double y2 = geo_iterator_2->second.position.GetY();
  double z2 = geo_iterator_2->second.position.GetZ();
  
  double diff = sqrt( pow(x2 - x1, 2) + pow(y2 - y1, 2) + pow(z2 - z1, 2) );
  
  return diff;
}

std::vector<double> FaintParticleTriggerAlgorithm::getDirection(FptHitVectorPtr timeWindowHits, std::vector<int> Double_Indices, const I3GeometryConstPtr &geo)
{
    //Loop over Doubles and calculate the direction
    std::vector<double> final_zen_azi;
    std::vector<double> Zenith_values;
    std::vector<double> Azimuth_values;
    int loop_end = Double_Indices.size();
    for (int j = 0; j <= loop_end-2; j+= 2) {
        FptHit hit1 = (*timeWindowHits)[Double_Indices[j]];
        FptHit hit2 = (*timeWindowHits)[Double_Indices[j+1]]; 
        I3OMGeoMap::const_iterator geo_iterator_1 = geo->omgeo.find(OMKey(hit1.string, hit1.pos));
        I3OMGeoMap::const_iterator geo_iterator_2 = geo->omgeo.find(OMKey(hit2.string, hit2.pos));
        //std::cout<<"omkey"<<geo_iterator_1<<std::endl;

        double x1 = geo_iterator_1->second.position.GetX();
        double y1 = geo_iterator_1->second.position.GetY();
        double z1 = geo_iterator_1->second.position.GetZ();
        double x2 = geo_iterator_2->second.position.GetX();
        double y2 = geo_iterator_2->second.position.GetY();
        double z2 = geo_iterator_2->second.position.GetZ();
        I3Direction dir1((x2-x1),(y2-y1),(z2-z1));
        Zenith_values.push_back(dir1.GetZenith()/I3Units::degree);
        Azimuth_values.push_back(dir1.GetAzimuth()/I3Units::degree);
        /*
        std::cout<<"double indices"<<Double_Indices[j]<<std::endl;
        std::cout<<"double indices2"<<Double_Indices[j+1]<<std::endl;
        std::cout<<"zen"<<dir1.GetZenith()/I3Units::degree<<std::endl;   
        std::cout<<"azi"<<dir1.GetAzimuth()/I3Units::degree<<std::endl;  
        */
      
    }
    std::vector<double> hist_zenith = CalcHistogram(Zenith_values, 0, 180, histogram_binning_);
    std::vector<double> hist_azimuth = CalcHistogram(Azimuth_values, 0, 360, histogram_binning_);
    final_zen_azi.insert(final_zen_azi.end(), hist_azimuth.begin(), hist_azimuth.end());
    final_zen_azi.insert(final_zen_azi.end(), hist_zenith.begin(), hist_zenith.end());

    
    
    return final_zen_azi;
}


std::vector<double> FaintParticleTriggerAlgorithm::CalcHistogram(std::vector<double> Angles, int lower_bound, int upper_bound, int bin_size) {
    std::vector<int> hist_vals;
    std::vector<double> mean_angle_vals, Returnval;

    for (int j = lower_bound; j < upper_bound; j += bin_size) {
        // Include 180 and 360° in the last bins 160-180. Otherwise no meaningful mean value for the angle can be calculated.
        int upper_bin_size = j + bin_size;
        if (j == upper_bound - bin_size) {
            upper_bin_size = j + bin_size + 1;
        }
        int hist_counter = 0;
        std::vector<double> angle_values;
        for (double k : Angles) {
            if (k >= j && k < upper_bin_size) {
                hist_counter += 1;
                angle_values.push_back(k);
            }
        }
        hist_vals.push_back(hist_counter);

        // Calculate the mean angle for each bin
        double sum = 0;
        for (double k : angle_values) {
            sum += k;
        }
        if (hist_counter == 0) {
            mean_angle_vals.push_back(0);
        }
        else {
            mean_angle_vals.push_back(sum / hist_counter);
        }
        // Select the bin with maximum counts and its corresponding mean angle
    }

    Returnval.push_back((double)*std::max_element(hist_vals.begin(), hist_vals.end()));
    int max_ind = std::distance(hist_vals.begin(), std::max_element(hist_vals.begin(), hist_vals.end()));
    Returnval.push_back(mean_angle_vals[max_ind]);

    return Returnval;
}


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    