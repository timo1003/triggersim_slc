/**
 * copyright  (C) 2006
 * the icecube collaboration
 * $Id:
 *
 * @file SimpleMajorityTriggerAlgorithm.cxx
 * @version
 * @date
 * @author toale
 */

#include <trigger-sim/algorithms/SlcTriggerAlgorithm.h>
#include <trigger-sim/algorithms/SlcTimeWindow.h>
#include <boost/foreach.hpp>
#include <boost/assign/std/vector.hpp>
#include "trigger-sim/algorithms/SlcTHit.h"
#include "dataclasses/geometry/I3Geometry.h"
#include <dataclasses/I3Direction.h>
#include <icetray/I3Units.h>
using namespace boost::assign;

SlcTriggerAlgorithm::SlcTriggerAlgorithm(double triggerWindow,double separation, bool triple_bool, unsigned int hit_min,unsigned int hit_max, unsigned int double_min, unsigned int double_max, unsigned int triple_min,unsigned int triple_max,unsigned int azi_min,unsigned int zen_min, double binning, double slcfraction_min, double cut_veldoublet_min,double cut_veldoublet_max, const I3GeometryConstPtr &geo) : 
  triggerWindow_(triggerWindow),
  triple_bool_(triple_bool),
  hit_min_(hit_min),
  hit_max_(hit_max),
  double_min_(double_min),
  double_max_(double_max),
  triple_min_(triple_min), 
  triple_max_(triple_max), 
  azi_min_(azi_min), 
  zen_min_(zen_min), 
  binning_(binning), 
  slcfraction_min_(slcfraction_min), 
  cut_veldoublet_min_(cut_veldoublet_min),
  cut_veldoublet_max_(cut_veldoublet_max),
  separation_(separation),
  triggerCount_(0),
  triggerIndex_(0)
{

  log_debug("SlcTriggerAlgorithm configuration:");
  log_debug("  TriggerWindow = %f", triggerWindow_);
  log_debug("  hit_min = %d", hit_min_);
  log_debug("  hit_max = %d", hit_max_);

}

SlcTriggerAlgorithm::~SlcTriggerAlgorithm() {}

void SlcTriggerAlgorithm::AddHits(SlcTHitVectorPtr hits,const I3GeometryConstPtr &geo)
{

  log_debug("Adding %zd hits to SlcTigger", hits->size());

  /*------------------------------------------------------------*
   * Check Trigger condition
   *------------------------------------------------------------*/
  SlcTimeWindow SlctimeWindow(hit_min_,hit_max_,slcfraction_min_, triggerWindow_,separation_);
  triggers_.clear();
  triggerCount_ = 0;
  triggerIndex_ = 0;

  // Get time windows
  SlcTHitIterPairVectorPtr timeWindows = SlctimeWindow.SlcFixedTimeWindows(hits,separation_);

  // If the vector is empty, there are no time windows for this string
  if (timeWindows->empty()) {
    log_debug("No valid time windows for this string");
    return;
  }
  log_debug("Found %zd triggered time windows", timeWindows->size());

  // Loop over the time windows and pull out the hits in each
  for (SlcTHitIterPairVector::const_iterator timeWindowIter = timeWindows->begin(); 
       timeWindowIter != timeWindows->end(); 
       timeWindowIter++) {

    // Create a vector of the hits in this time window
    SlcTHitVectorPtr timeHits(new SlcTHitVector);

    // Get the window boundaries
    SlcTHitVector::const_iterator firstHit = timeWindowIter->first;
    SlcTHitVector::const_iterator lastHit  = timeWindowIter->second;
    


    // Iterate over the hits and pull out the ones for this window
    for (SlcTHitVector::const_iterator hitIter = firstHit; 
     hitIter != lastHit; 
     hitIter++){
      timeHits->push_back(*hitIter);
      //std::cout <<"Hit time"<<hitIter->time<<std::endl;
    }
    //Second cut: number of Doubles
    std::vector<int> Double_Indices = DoubleThreshold(timeHits, geo);
    unsigned int number_doubles = Double_Indices.size()/2;
  
    if (number_doubles >= double_min_ &&  number_doubles <= double_max_){
        
        //Third cut on directional clustering or triple cut
        bool cut3 = false;
        if (triple_bool_){
            unsigned int number_triples = TripleThreshold(timeHits,Double_Indices,geo);
            if (number_triples > triple_min_ && number_triples < triple_max_){
                cut3 = true;
                }
                                                          
                
        
        
            }
        else{
            std::vector<double> dir = getDirection(timeHits,Double_Indices,geo);
            unsigned int number_azimuth = dir[0];
            double mean_azimuth = dir[1];
            unsigned int number_zenith = dir[2];
            double mean_zenith = dir[3];

            if (number_zenith > zen_min_ && number_azimuth > azi_min_) {
                cut3 = true;
            }
            
        if (cut3){
            //Fourth cut on the SLC fraction
        
                 triggers_.push_back(*timeHits);
                 triggerCount_++;
                 log_debug("Time window (%f, %f) has %zd hits", firstHit->time, (--lastHit)->time, timeHits->size());
                 /*
                 std::cout <<"TW first hit"<<timeHits->begin()->time<<std::endl;
                 std::cout <<"TWlast hit"<<timeHits->end()->time<<std::endl;
                 std::cout <<"Hits"<<(*timeHits).size()<<std::endl;
                 std::cout <<"doubles"<<number_doubles<<std::endl;
                 std::cout <<"azimuth"<<number_azimuth<<std::endl;
                 std::cout <<"zenith"<<number_zenith<<std::endl;
                 */
                 log_debug("Trigger! Count = %d", triggerCount_);
            
            
        

            
    }
        
   
      

    }
  
    }
   }
}

unsigned int SlcTriggerAlgorithm::GetNumberOfTriggers() {
  return triggerCount_;
}

SlcTHitVectorPtr SlcTriggerAlgorithm::GetNextTrigger() {
  SlcTHitVectorPtr hits;
  if (triggerCount_ > 0) {
    log_debug("Returning trigger window %d", triggerIndex_);
    hits = SlcTHitVectorPtr(new SlcTHitVector(triggers_.at(triggerIndex_)));
    triggerCount_--;
    triggerIndex_++;
  }
  return hits;
}

std::vector<int> SlcTriggerAlgorithm::DoubleThreshold(SlcTHitVectorPtr timeWindowHits, const I3GeometryConstPtr &geo)
{
    std::vector<int> Doubles;
    unsigned int double_combinations =0;
    int ind_hit_1 = -1;
    //Second loop starts from first element
    
    for (SlcTHitVector::const_iterator hitIter1 = timeWindowHits->begin(); hitIter1 != timeWindowHits->end(); hitIter1++) {   
        ind_hit_1++;
        int ind_hit_2 = ind_hit_1;
            for (SlcTHitVector::const_iterator hitIter2 = hitIter1+1; hitIter2 != timeWindowHits->end(); hitIter2++) {
                ind_hit_2++;
                SlcTHit hit1 = *hitIter1;
                SlcTHit hit2 = *hitIter2;
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
                    if (velocity> cut_veldoublet_min_ && velocity <cut_veldoublet_max_){
                        double_combinations++;
                        //Threshold exceeded: return empty list -> below cut threshold
                        if (double_combinations > double_max_){
                            std::vector<int> Doubles;
                            return Doubles;
                       
                            
                        }
                            
                        Doubles.push_back(ind_hit_1);
                        Doubles.push_back(ind_hit_2);

                    
                    
                    }
                }
                    
            }
    }
    
    
    
    
    
    
    return Doubles;
}

unsigned int SlcTriggerAlgorithm::TripleThreshold(SlcTHitVectorPtr timeWindowHits,std::vector<int> Double_Indices, const I3GeometryConstPtr &geo)
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
                    SlcTHit hit1 = (*timeWindowHits)[Double_Indices[j]];
                    SlcTHit hit2 = (*timeWindowHits)[Double_Indices[k+1]]; 
                    OMKey omkey1(hit1.string, hit1.pos);
                    OMKey omkey2(hit2.string, hit2.pos);
                    if (omkey1 != omkey2){
                        // As the doublets are velocity consistent only the third component (0-2) is checked
                        
                        double distance = getDistance(hit1, hit2, geo);
                        double time = abs(hit2.time - hit1.time);
                        //in km/s
                        double velocity = 1e6*distance/time;
                        if (velocity> cut_veldoublet_min_ && velocity <cut_veldoublet_max_){
                            triple_combinations++;
                            //stop calculating if threshold is exceeded
                            if (triple_combinations > triple_max_){
                                std::vector<int> Doubles;
                                return triple_max_+1;
                       
                            }
                        }
                       
                        
                    }
                }
    
            }
     }
    
    
    
    return triple_combinations;
}

//function from SLOP trigger to calculate the distance between to OMs
double SlcTriggerAlgorithm::getDistance(SlcTHit hit1, SlcTHit hit2,const I3GeometryConstPtr &geo)
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

std::vector<double> SlcTriggerAlgorithm::getDirection(SlcTHitVectorPtr timeWindowHits, std::vector<int> Double_Indices, const I3GeometryConstPtr &geo)
{
    //Loop over Doubles and calculate the direction
    std::vector<double> final_zen_azi;
    std::vector<double> Zenith_values;
    std::vector<double> Azimuth_values;
    int loop_end = Double_Indices.size();
    for (int j = 0; j <= loop_end-2; j+= 2) {
        SlcTHit hit1 = (*timeWindowHits)[Double_Indices[j]];
        SlcTHit hit2 = (*timeWindowHits)[Double_Indices[j+1]]; 
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
    std::vector<double> hist_zenith = CalcHistogram(Zenith_values, 0, 180, binning_);
    std::vector<double> hist_azimuth = CalcHistogram(Azimuth_values, 0, 360, binning_);
    final_zen_azi.insert(final_zen_azi.end(), hist_azimuth.begin(), hist_azimuth.end());
    final_zen_azi.insert(final_zen_azi.end(), hist_zenith.begin(), hist_zenith.end());

    
    
    return final_zen_azi;
}


std::vector<double> SlcTriggerAlgorithm::CalcHistogram(std::vector<double> Angles, int lower_bound, int upper_bound, int bin_size) {
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


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    