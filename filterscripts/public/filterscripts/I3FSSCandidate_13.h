#ifndef I3FSSCandidate_13__H
#define I3FSSCandidate_13__H

#include <filterscripts/I3JEBFilter.h>
#include <dataclasses/physics/I3RecoPulse.h>
#include <dataclasses/physics/I3Particle.h>
#include <string>
#include <vector>

/**
 * @class I3FSSCandidate_13
 *
 * Implementation of the Full Sky Starting (FSS) candidate selection for season 2013
 * 
 */

class I3FSSCandidate_13 : public I3JEBFilter {

    public:

        I3FSSCandidate_13(const I3Context&);
        ~I3FSSCandidate_13(){}
        void Configure();
        bool KeepEvent(I3Frame& frame);
        void Finish();

        SET_LOGGER("I3FSSCandidate_13");

    private:

        // implementation methods
        void ConfigureSideVetoStrings();
        bool FSSCandidate();
        bool VetoCheck();    

        // configurable parameters
        unsigned int nSideVetoLayers_;
        unsigned int nTopVetoLayers_;
        std::string responseKey_;
        std::string MuonTrackFitName_;
        std::string eventHeaderName_;

        // statistics counters
        unsigned int nKept_;
        unsigned int nSeen_;
        unsigned int nMissingPulses_;
	unsigned int nBadOrMissingTrackFit_;
	unsigned int nSideVetoRejected_;
        unsigned int nTopVetoRejected_;
        
        // sorted vector of side veto string numbers
        std::vector<unsigned int> sideVetoStrings_;

        // convenience pointers
        I3RecoPulseSeriesMapConstPtr recoPulses_;
        I3ParticleConstPtr MuonTrackFitPtr_;

};

#endif /* I3FSSCandidate_13__H */
