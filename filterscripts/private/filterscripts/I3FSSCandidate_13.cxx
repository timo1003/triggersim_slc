#include <filterscripts/I3FSSCandidate_13.h>
#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3FSSCandidate_13>);

#include <icetray/I3Units.h>
#include <icetray/I3Bool.h>
#include <dataclasses/I3Double.h>
#include <astro/I3Astro.h>
#include <phys-services/I3GSLRandomService.h>

#include <cmath>
#include <limits>
#include <algorithm>

I3FSSCandidate_13::I3FSSCandidate_13(const I3Context& context) :
        I3JEBFilter(context),
        nSideVetoLayers_(1),
        nTopVetoLayers_(5),
	responseKey_("InitialPulseSeriesReco"),
	MuonTrackFitName_("PoleMuonLineFit"),
        eventHeaderName_("I3EventHeader"),
        nKept_(0),
        nSeen_(0),
        nMissingPulses_(0),
        nBadOrMissingTrackFit_(0),
	nSideVetoRejected_(0),
        nTopVetoRejected_(0)
{
    AddParameter("NSideVetoLayers",
                 "Number of side veto layers (0, 1, 2 or 3). If the *earliest* pulse of an event "
                 "occur in a string in any of the side veto layers defined, the entire event will be "
                 "rejected. (Later pulses in the side veto layer do not affect the filter decision.)",
                 nSideVetoLayers_);

    AddParameter("NTopVetoLayers",
                 "Number of top veto layers (0-60). If *any* pulse occur in a non-DeepCore DOM with "
		 "DOM number less or equal to this threshold, during the full event time, the entire "
		 "event will be rejected.",
                 nTopVetoLayers_);

    AddParameter("IceCubeResponseKey",
		 "Name of the I3RecoPulseSeriesMap in the frame to use."
		 "Should contain only IceCube HLC launches, with NFE, DOM Launch Cleaning, "
		 "and TimeWindow Cleaning already done. This will be used to evaluate "
		 "the top- and side-vetos.",
		 responseKey_ );

    AddParameter("MuonTrackFitName",
                 "Frame name of the I3Particle object with the muon track fit (SLC+HLC).",
                  MuonTrackFitName_);

    AddParameter("EventHeaderName",
		 "Frame name of event header object.",
		 eventHeaderName_ );

}

void I3FSSCandidate_13::Configure(){

    GetParameter( "NSideVetoLayers", nSideVetoLayers_);
    GetParameter( "NTopVetoLayers", nTopVetoLayers_);
    GetParameter( "IceCubeResponseKey", responseKey_ );
    GetParameter( "MuonTrackFitName", MuonTrackFitName_);
    GetParameter( "EventHeaderName", eventHeaderName_ );
   
    ConfigureSideVetoStrings();

}

// create a sorted vector of side veto strings
void I3FSSCandidate_13::ConfigureSideVetoStrings(){

    // IC86 Sideveto setup
    unsigned int IC86_sv1[28] = {
        1,2,3,4,5,6,7,13,14,21,22,30,31,40,41,
        50,51,59,60,67,68,72,73,74,75,76,77,78
    };
    unsigned int IC86_sv2[22] = {
        8,9,10,11,12,15,20,23,29,32,39,42,49,
        52,58,61,64,65,66,69,70,71
    };
    unsigned int IC86_sv3[16] = {
        16,17,18,19,24,28,33,38,43,48,53,55,56,57,62,63
    };

    switch(nSideVetoLayers_){
        // note: no break for case 3,2,1
        case 3: sideVetoStrings_.insert(sideVetoStrings_.end(),IC86_sv3,IC86_sv3+16);
        case 2: sideVetoStrings_.insert(sideVetoStrings_.end(),IC86_sv2,IC86_sv2+22);
        case 1: sideVetoStrings_.insert(sideVetoStrings_.end(),IC86_sv1,IC86_sv1+28);
        case 0: break;
        default:
                log_fatal( "invalid nr of side veto layers: %u",
                           nSideVetoLayers_);
    }
    sort(sideVetoStrings_.begin(),sideVetoStrings_.end());
}

// FSS filter: keep or reject
bool I3FSSCandidate_13::KeepEvent(I3Frame& frame){

    // hello
    ++nSeen_;

    // check pulses
    recoPulses_ = frame.Get<I3RecoPulseSeriesMapConstPtr>(responseKey_);
    if ( (!recoPulses_) || (recoPulses_->size() == 0) ){
         log_debug( "(%s) event does not have (usable) pulses %s",
                    GetName().c_str(), responseKey_.c_str() );
         ++nMissingPulses_;
         return false;
    }

    // check tracks    
    MuonTrackFitPtr_ = frame.Get<I3ParticleConstPtr>(MuonTrackFitName_);
    bool FitOK = (MuonTrackFitPtr_ && (MuonTrackFitPtr_->GetFitStatus() == I3Particle::OK ));
    
    if (!FitOK) {
         log_debug("(%s) track fits %s and %s are both bad or missing",
		   GetName().c_str(),
		   MuonTrackFitName_.c_str(), MuonTrackFitName_.c_str());
	 ++nBadOrMissingTrackFit_;
	 return false;
    }

    bool fss = FitOK && FSSCandidate();

    if (fss){
        ++nKept_;
        return true;
    } 

    return false;
}

bool I3FSSCandidate_13::FSSCandidate(){
    if ( ! VetoCheck() ){
        return false;
    }
    return true;
}

bool I3FSSCandidate_13::VetoCheck(){

    unsigned int earliest_string = 0;
    double earliest_time = std::numeric_limits<double>::max();
    I3RecoPulseSeriesMap::const_iterator miter;
    for ( miter=recoPulses_->begin(); miter!=recoPulses_->end(); miter++ ){
        unsigned int om = miter->first.GetOM();
        unsigned int str = miter->first.GetString();
        if ( ( om <= nTopVetoLayers_ ) && ( str < 79 ) ){
	    nTopVetoRejected_++;
            log_trace( "(%s) rejected by top veto, hit in om=%d str=%d",
                       GetName().c_str(), om, str );
            return false;
        }
        const I3RecoPulseSeries &pulseseries = miter->second;
        for ( I3RecoPulseSeries::const_iterator ipulse = pulseseries.begin();
                                                ipulse != pulseseries.end();
                                                ipulse++ ){
            double t = ipulse->GetTime();
            if ( earliest_time > t ){
                earliest_time = t;
                earliest_string = str;
            }
        }
    }

    // try to find the earliest string in the list of veto strings
    std::vector<unsigned int>::iterator iside =
        std::lower_bound(sideVetoStrings_.begin(),
                         sideVetoStrings_.end(), earliest_string);
    if ( ( iside != sideVetoStrings_.end() ) && (earliest_string == *iside) ){
        nSideVetoRejected_++;
        log_trace( "(%s) rejected by side veto, hit at time t=%f in str=%u",
                   GetName().c_str(), earliest_time, earliest_string );
        return false;
    }
    // (Check: for ints, equality is the same as equalence, so the
    // above is OK; Scott Meyers, Effective STL, item 45, page 195.)

    log_trace( "(%s) top & side veto OK (earliest string was %u)",
               GetName().c_str(), earliest_string );

    return true;
}

void I3FSSCandidate_13::Finish(){

    log_info( "(%s) Full Sky Starting (FSS) Candidate Rate *************************",
              GetName().c_str() );

    log_info("KEPT: %u", nKept_ );
    log_info("REJECTED: %u", (nSeen_-nKept_) );
   
    log_info("Missing pulses rejected: %u", nMissingPulses_ );
    log_info("Bad or missing track fit: %u", nBadOrMissingTrackFit_ );

    log_info("Top Veto rejected: %u", nTopVetoRejected_ );
    log_info("Side Veto rejected: %u", nSideVetoRejected_ );

}
