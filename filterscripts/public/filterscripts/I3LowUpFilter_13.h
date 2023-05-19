/**
 * copyright (C) 2007
 * the IceCube collaboration
 * $Id:$
 * 
 * @file I3LowUpFilter_13.h
 * @version $Revision: v00-00-01$
 * @author mzoll <marcel.zoll@fysik.su.se > Meike de Widt
 * @date Dec 14 2007, last update Sep 2013$
 */

#ifndef JEB_FILTER_I3LOWUPFILTER13_H
#define JEB_FILTER_I3LOWUPFILTER13_H

#include "filterscripts/I3JEBFilter.h"
#include "dataclasses/physics/I3RecoPulse.h"
#include "dataclasses/physics/I3Particle.h"
#include "icetray/I3Units.h"
#include <vector>
#include <string>

/// The LowUpFilter implementation for 2013 (IC86:III)
class I3LowUpFilter_13 : public I3JEBFilter
{
  public:
    /// Constructor for TrayContext
    I3LowUpFilter_13(const I3Context& context);
    /// std KeepEvent function
    bool KeepEvent(I3Frame& frame);
    /// std Configure function
    void Configure();
    /// std Finish function
    void Finish();
    
    /// logging set to LowUpFilter_13
    SET_LOGGER("I3LowUpFilter_13");

  private:
    // Intern Definitions
    /// lookuptable which strings are on the outside of the IceCube array 
    std::vector<bool> outerStrings;
    /**
    * @brief Evaluate the InnerStringCriterion
    * @param recoMap the passed RecoMapSeries to be evaluated
    */
    bool InnerStringCriterion(I3RecoPulseSeriesMapConstPtr recoMap);
    // Input Parameters
    /// OPTION: Name of the I3RecoPulseSeries in the frame
    std::string recoPulsesName_;
    /// OPTION: List of Names of I3Particles that are taken as first Reconstruction 
    std::vector<std::string> tracknamelist_;
    /// OPTION: nChan Cut value in [au] (lower limit)
    unsigned int nchanCut_;
    /// OPTION: Zenith Cut on the best Reconstruction with status::OK in [rad] (lower limit)
    double zenithCut_;
    /// OPTION: ZExtension Cut value [m] (upper limit)
    double zExtensionCut_;
    /// OPTION: TExtension Cut value in [ns] (upper limit)
    double timeExtensionCut_;
    /// OPTION: ZTravel Cut in [m] (upper limit)
    double zTravelCut_;
    /// OPTION: VetoZ Cut value in [m] (upper limit)
    double zMaxCut_;
    /// OPTION: Bool if the InnerStringCriterion should be used
    bool iSCritActive_;
    
    // bookkeeping of event numbers failing certain cuts
    /// number of rejected events because of PulseSeries with empty pulses
    unsigned int nRejNoPulses;
    /// number of rejected events because of PulseSeries without hits
    unsigned int nRejNoHits;
    /// number of rejected events because of nchannel failing cuts
    unsigned int nRejNch;
    /// number of rejected events because of zenith failing cuts
    unsigned int nRejZen;
    /// number of rejected events because of z_extension failing cuts
    unsigned int nRejZExt;
    /// number of rejected events because of t_extension failing cuts
    unsigned int nRejTExt;
    /// number of rejected events because of z_travel failing cuts
    unsigned int nRejZTravel;
    /// number of rejected events because of no good track
    unsigned int nRejNoTrack;
    /// number of rejected events because of z_max failing cuts
    unsigned int nRejZMax;
    /// number of rejected events because of PulseSeries failing InnerStringCriterion
    unsigned int nRejInnerString;
    /// number of events passed
    unsigned int nPassedTot;
};

#endif
