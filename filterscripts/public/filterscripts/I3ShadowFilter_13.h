#ifndef FILTER_2013_SHADOWFILTER_13__H
#define FILTER_2013_SHADOWFILTER_13__H

/**
 *  copyright  (C) 2012
 *  the icecube collaboration
 *  $Id$
 *
 *  @file
 *  @version $Revision$
 *  @date $Date$
 *  @author David Boersma <boersma@icecube.wisc.edu>
 */

// standard library stuff
#include <string>
#include <vector>

// icetray/JEB stuff
#include "icetray/IcetrayFwd.h"
#include "phys-services/I3RandomService.h"
#include "filterscripts/I3JEBFilter.h"
#include "dataclasses/I3Time.h"
#include "dataclasses/physics/I3Particle.h"
#include "dataclasses/physics/I3RecoPulse.h"

/**
 * @brief An I3Filter which selects events which have a good quality
 * particle with a direction within a search window around the Moon/Sun
 * (rectangular in zenith/azimuth).
 */
class I3ShadowFilter_13 : public I3JEBFilter {
public:

    I3ShadowFilter_13(const I3Context & context);
    void Configure();
    bool KeepEvent(I3Frame & frame);
    void Finish();

private:
    std::string shadowName_;
    std::string eventHeader_;
    std::string particleKey_;
    std::string pulsesKey_;
    std::string nChKey_;
    std::string nStringKey_;
    std::string corsikaMJDName_;
    std::string corsikaRandServiceName_;
    I3RandomServicePtr corsikaRandService_;

    double shadowZenithMaximum_;
    std::vector < double > zenithRange_;
    std::vector < double > azimuthRange_;
    std::vector < double > corsikaMJDRange_;

    int nChThreshold_;
    int nStringThreshold_;
    bool solidAngleCorr_;

    I3ParticleConstPtr fit_;

    int nCh_;
    int nString_;
    int paranoia_;

    unsigned int nKeep_;
    unsigned int nRejShadow_;
    unsigned int nRejMiss_;
    unsigned int nRejBadFit_;
    unsigned int nRejZenith_;
    unsigned int nRejAzimuth_;
    unsigned int nRejNCh_;
    unsigned int nRejNString_;
    unsigned int nReusedMJD_;
    unsigned int nGeneratedMJD_;
    unsigned int nReuseNChNString_;

    double mjdStart_;
    double mjdEnd_;
    double timeMJD_;
    double shadowAzimuth_;
    double shadowZenith_;
    bool corsikaMode_;

    /**
     * Compute nCh_ and nString_
     */
    void ComputeNChNString(const I3RecoPulseSeriesMap &pulses);

    /**
     * function pointer to the relevant astro/coordinate-service function
     * (RA for Sun or Moon)
     */
    I3Direction (*GetShadow)(const I3Time&);

  
    /// checks angular specs of Moon window
    void ConfigureShadowWindow();

    /// checks specs of time window (for Corsika input data)
    void ConfigureCorsika();

    /// checks if the frame actually contains the relevant input data
    bool InputDataAvailable(I3Frame&);

    /// checks the simple cuts (nch/nstr/ndir/rlogl)
    bool SurvivesCuts();

    /// checks if Moon is high enough above the horizon
    bool CheckShadow(I3Frame &frame );

    /// checks fit direction with Moon window
    bool InShadowWindow();

    SET_LOGGER("I3ShadowFilter_13");
};

#endif /* FILTER_2013_SHADOWFILTER_13__H */
