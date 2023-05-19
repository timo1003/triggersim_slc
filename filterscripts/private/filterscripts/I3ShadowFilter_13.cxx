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

// JEB
#include "filterscripts/I3ShadowFilter_13.h"
#include "filterscripts/I3FilterModule.h"

// standard icetray/dataclasses stuff
#include "icetray/I3Units.h"
#include "icetray/I3DefaultName.h"
#include "icetray/I3Configuration.h"
#include "dataclasses/I3Direction.h"
#include "dataclasses/I3Double.h"
#include "icetray/I3Int.h"
#include "dataclasses/physics/I3EventHeader.h"
#include "dataclasses/physics/I3RecoPulse.h"
#include "dataclasses/physics/I3Waveform.h"
#include "astro/I3Astro.h"
#include "gulliver/I3LogLikelihoodFit.h"
#include "gulliver/I3LogLikelihoodFitParams.h"

I3ShadowFilter_13::I3ShadowFilter_13(const I3Context & context):
    I3JEBFilter(context),
    shadowName_("Moon"),
    eventHeader_(I3DefaultName < I3EventHeader >::value()),
    particleKey_(""),
    pulsesKey_(""),
    corsikaMJDName_("CorsikaMoon"),
    corsikaRandServiceName_(""),
    shadowZenithMaximum_(90.0 * I3Units::degree),
    nChThreshold_(0),
    nStringThreshold_(0),
    solidAngleCorr_(false),
    nCh_(0),
    nString_(0),
    paranoia_(10),
    nKeep_(0),
    nRejShadow_(0),
    nRejMiss_(0),
    nRejBadFit_(0),
    nRejZenith_(0),
    nRejAzimuth_(0),
    nRejNCh_(0),
    nRejNString_(0),
    nReusedMJD_(0),
    nGeneratedMJD_(0),
    nReuseNChNString_(0),
    corsikaMode_(false),
    GetShadow(NULL)
{
    zenithRange_.resize(2);
    zenithRange_[0] = -15.0 * I3Units::degree;
    zenithRange_[1] = +15.0 * I3Units::degree;
    azimuthRange_.resize(2);
    azimuthRange_[0] = -90.0 * I3Units::degree;
    azimuthRange_[1] = +90.0 * I3Units::degree;

    AddParameter( "WhichShadow",
                  "Shadow from which object (Moon or Sun)?",
                  shadowName_);

    AddParameter( "EventHeaderName",
                  "Name of the EventHeader in the frame",
                  eventHeader_);

    AddParameter( "CorsikaMJDName",
                  "If fake event times are generated for corika events, "
                  "then the MJD and angular coordinates are stored in the "
                  "frame. If several Moon filters are defined (e.g. one "
                  "for conventional data and one for extended DST), then "
                  "subsequent filters can reuse the generated times and "
                  "and angles (instead of generating different ones) if "
                  "the same name is configured for this option. ",
                  corsikaMJDName_ );
    AddParameter( "CorsikaMJDRange",
                  "For testing with corsika: give the MJD range (e.g. "
                  "29 September 10:00h - 5 October 21:00h (2011): [55833.417,55839.875]"
                  "Instead of getting the event time from the event header, "
                  "for each event a random time in the given MJD range will be "
                  "generated. Default: empty range, i.e. assume exp input data ",
                  corsikaMJDRange_);

    AddParameter( "CorsikaRandService",
                  "Name of the random number generator servuce used to generate "
                  "the event time in the year for corsika events.",
                  corsikaRandServiceName_);

    AddParameter( "MaximumZenith",
                  "Maximum zenith for the Moon/Sun (default: horizon)",
                  shadowZenithMaximum_);

    AddParameter( "ParticleName",
                  "Name of the particle in the frame",
                  particleKey_);

    AddParameter( "ZenithRange",
                  "Zenith range for the angular window, specified by "
                  "two doubles that specify the minimum and maximum "
                  "zenith difference w.r.t. the Moon/Sun coordinates.",
                  zenithRange_);

    AddParameter( "AzimuthRange",
                  "Azimuth range for the 'shadow window', specified by "
                  "two doubles that specify the minimum and maximum "
                  "azimuth difference w.r.t. the Moon/Sun coordinates.",
                  azimuthRange_);

    AddParameter( "CorrectSolidAngle",
                  "If set, then the behavior of AzimuthRange is slightly "
                  "changed: the azimuth difference is multiplied with "
                  "sin(zenith) (zenith of the reconstructed track).",
                  solidAngleCorr_ );

    AddParameter( "NChannelCut",
                  "The *minimum* number of hit channels an event should "
                  "contain in order to be kept by this filter.",
                  nChThreshold_);

    AddParameter( "NStringCut",
                  "The *minimum* number of strings an event should "
                  "contain in order to be kept by this filter.",
                  nStringThreshold_);

    AddParameter( "RecoPulsesName",
                  "Name of the I3RecoPulseSeriesMap that was used by "
                  "the track reconstruction.",
                  pulsesKey_ );

}

void I3ShadowFilter_13::Configure(){

    GetParameter( "WhichShadow", shadowName_);
    GetParameter( "EventHeaderName", eventHeader_);
    GetParameter( "CorsikaRandService", corsikaRandServiceName_);
    GetParameter( "CorsikaMJDRange", corsikaMJDRange_);
    GetParameter( "CorsikaMJDName", corsikaMJDName_);
    GetParameter( "MaximumZenith", shadowZenithMaximum_);
    GetParameter( "ParticleName", particleKey_);
    GetParameter( "ZenithRange", zenithRange_);
    GetParameter( "AzimuthRange", azimuthRange_);
    GetParameter( "CorrectSolidAngle", solidAngleCorr_ );
    GetParameter( "NChannelCut", nChThreshold_);
    GetParameter( "NStringCut", nStringThreshold_);
    GetParameter( "RecoPulsesName", pulsesKey_);

    if (particleKey_.empty()) {
        log_fatal
            ("(%s) You should specify a value for the ParticleName option.",
             GetName().c_str());
    }

    if ( pulsesKey_.empty() ){
        if (nChThreshold_>0 || nStringThreshold_>0) {
            log_fatal( "(%s) You specified cuts on Nch/Nstring "
                       "(Nch>=%d and Nstring>=%d "
                       "but not name of an I3RecoPulseSeriesMap",
                       GetName().c_str(), nChThreshold_, nStringThreshold_ );
        }
    } else {
        if (nChThreshold_==0 && nStringThreshold_==0) {
            log_fatal( "(%s) You did not specify thresholds for Nch/Nstring "
                       "but you *did* give a name of an I3RecoPulseSeriesMap",
                       GetName().c_str() );
        }
        nChKey_ = pulsesKey_ + "_NCH_HLC";
        nStringKey_ = pulsesKey_ + "_NSTRING_HLC";
    }

    ConfigureShadowWindow();

    ConfigureCorsika();

}

void I3ShadowFilter_13::ConfigureShadowWindow(){
    if ( shadowName_ == "Moon" ){
        GetShadow = &I3GetMoonDirection;
    } else if ( shadowName_ == "Sun" ){
        GetShadow = &I3GetSunDirection;
    } else {
        log_fatal( "(%s) got %s for shadowing object, should be Moon or Sun.",
                   GetName().c_str(), shadowName_.c_str() );

    }
    if ( ( azimuthRange_[1]-azimuthRange_[0] > 360*I3Units::degree ) ||
         ( azimuthRange_[1] <= azimuthRange_[0]   ) ||
         ( azimuthRange_[1] > 360*I3Units::degree ) ||
         ( azimuthRange_[0] < -360*I3Units::degree ) ){
        log_fatal("(%s) Something wrong with azimuth range: [%gdeg,%gdeg]",
                  GetName().c_str(),
                  azimuthRange_[0]/I3Units::degree,
                  azimuthRange_[1]/I3Units::degree );
    }

    if ( ( zenithRange_[1] <= zenithRange_[0]     ) ||
         ( zenithRange_[1] > +180*I3Units::degree ) ||
         ( zenithRange_[0] < -180*I3Units::degree ) ){
        log_fatal("(%s) Something wrong with zenith range: [%gdeg,%gdeg]",
                  GetName().c_str(),
                  zenithRange_[0]/I3Units::degree,
                  zenithRange_[1]/I3Units::degree );
    }

    if ( shadowZenithMaximum_ < 60*I3Units::degree ){
        log_warn("(%s) MaximumZenith was set to %gdeg; "
                 "this will kill all your events...",
                 GetName().c_str(),
                 shadowZenithMaximum_/I3Units::degree );
    }
}

void I3ShadowFilter_13::ConfigureCorsika(){

    if ( corsikaMJDRange_.size() == 2 ){ 
        mjdStart_ = corsikaMJDRange_[0];
        mjdEnd_ = corsikaMJDRange_[1];

	I3Time limit;
	limit.SetUTCCalDate(1980, 1, 1, 0, 0, 0.);
	long mjd_1980 = limit.GetModJulianDay();
	limit.SetUTCCalDate(2030, 1, 1, 0, 0, 0.);
	long mjd_2030 = limit.GetModJulianDay();
	
	
        if (    ( mjdStart_ < mjdEnd_ )
	     && ( mjdStart_ > mjd_1980 )
             && ( mjdEnd_ < mjd_2030 ) ){
            log_info( "(%s) MJD start/end dates OK: %f,%f",
                       GetName().c_str(), mjdStart_, mjdEnd_);
        } else {
            log_fatal( "(%s) bad or fishy MJD start/end dates: %f,%f",
                       GetName().c_str(), mjdStart_, mjdEnd_);
        }
        if ( corsikaRandServiceName_.empty() ){
            log_fatal("(%s) a random service is required for corsika event "
                      "time generation (corsika MJD range is %f-%f)",
                      GetName().c_str(), mjdStart_, mjdEnd_ );
        }
        corsikaRandService_ =
            context_.Get< I3RandomServicePtr >( corsikaRandServiceName_ );
        if ( ! corsikaRandService_ ){
            log_fatal("(%s) Random service \"%s\" was not found in context.",
                      GetName().c_str(), corsikaRandServiceName_.c_str() );
        }
        corsikaMode_ = true;
    }

}

bool I3ShadowFilter_13::KeepEvent(I3Frame & frame){

    log_debug("(%s) starting %s Shadow filter on new event",
              shadowName_.c_str(), GetName().c_str());

    if (paranoia_-->0){
        if ( frame.Has("I3MCTree") && !corsikaMode_ ){
            log_fatal("Input data seems to be simulation "
                      "(I found an I3MCTree object), "
                      "but you have not provided an MJD range + RNG service!!");
        }
        if ( corsikaMode_ && !(frame.Has("I3MCTree") || frame.Has("I3MCTree_preMuonProp")) ){
            log_fatal("You have provided an MJD range + RNG service, but the "
                      "input data seems to be exp data "
                      "(I did not find an I3MCTree object in the frame)!!");
        }
    }

    bool decision = false;
    timeMJD_ = shadowAzimuth_ = shadowZenith_ = NAN;

    if ( ! CheckShadow(frame) ){
        log_debug( "(%s) Rejecting event: %s too low (zenith of %s too high).",
                   GetName().c_str(), shadowName_.c_str(), shadowName_.c_str() );
    } else if ( ! InputDataAvailable(frame) ){
        log_debug( "(%s) Rejecting event: missing/bad input data.",
                  GetName().c_str() );
    } else if ( ! SurvivesCuts() ){
        log_debug( "(%s) Rejecting event: "
                   "too low multiplicity or too low quality track.",
                   GetName().c_str() );
    } else if ( ! InShadowWindow() ){
        log_debug( "(%s) Rejecting event: Fit not within %s window.",
                   GetName().c_str(), shadowName_.c_str() );
    } else {
        // hooray!
        log_debug( "(%s) Keeping %s Shadow event.",
                   shadowName_.c_str(), GetName().c_str() );
        decision = true;
        ++nKeep_;
    }

    return decision;
}

void I3ShadowFilter_13::
ComputeNChNString(const I3RecoPulseSeriesMap &pulses){
    I3RecoPulseSeriesMap::const_iterator i=pulses.begin();
    std::set<int> stringset;
    nCh_ = 0;
    for (;i!=pulses.end();++i){
        I3RecoPulseSeries::const_iterator ipulse=i->second.begin();
        for ( ; ipulse!=i->second.end();ipulse++){
            //  for the old-school pulse indexing
            //int source = ipulse->GetSourceIndex();
            //if ( source == I3Waveform::ATWD ||
            //     source == I3Waveform::FADC ){
            // now: new simpler condition for use with new pulse flags
            if ( ipulse->GetFlags() & I3RecoPulse::LC ) {
                nCh_ += 1;
                stringset.insert(i->first.GetString());
                break;
            }
        }
    }
    nString_ = stringset.size();
}

bool I3ShadowFilter_13::InputDataAvailable(I3Frame& frame){

    nCh_ = 0;
    nString_ = 0;
    if ( pulsesKey_.empty() ){
        log_trace("(%s) no pulses specified.", GetName().c_str() );
    } else {
        I3IntConstPtr nChPtr = frame.Get < I3IntConstPtr > (nChKey_);
        I3IntConstPtr nStringPtr = frame.Get < I3IntConstPtr > (nStringKey_);
        if ( nChPtr && nStringPtr ){
            log_debug( "(%s) reusing Nch=%s=%d and Nstring=%s=%d",
                       GetName().c_str(), nChKey_.c_str(), nChPtr->value,
                       nStringKey_.c_str(), nStringPtr->value );
            nCh_ = nChPtr->value;
            nString_ = nStringPtr->value;
            ++nReuseNChNString_;
        } else {
            I3RecoPulseSeriesMapConstPtr pulsesPtr =
                frame.Get < I3RecoPulseSeriesMapConstPtr > (pulsesKey_);
            if (!pulsesPtr) {
                log_debug("(%s) Event does not have a pulsemap/mask named %s. "
                          "Event will be rejected (by this filter).",
                          GetName().c_str(), pulsesKey_.c_str());
                ++nRejMiss_;
                return false;
            }
            ComputeNChNString(*pulsesPtr);
            // We store this in the frame because Moon and Sun both need them
            // and we want to avoid this being computed twice.
            frame.Put( nChKey_,     I3IntPtr( new I3Int(nCh_) ) );
            frame.Put( nStringKey_, I3IntPtr( new I3Int(nString_) ) );
        }
    }

    if (!frame.Has(particleKey_)) {
        log_debug("(%s) Event does not have particleKey %s. "
                  "Event being filtered.",
                  GetName().c_str(), particleKey_.c_str());
        ++nRejMiss_;
        return false;
    }
    fit_ = frame.Get < I3ParticleConstPtr >(particleKey_);
    if ( fit_->GetFitStatus() != I3Particle::OK ){
        log_debug("(%s) Fit %s failed for this event with status %d(%s). "
                  "Event being filtered.",
                  GetName().c_str(), particleKey_.c_str(),
                  fit_->GetFitStatus(),
                  fit_->GetFitStatusString().c_str());
        ++nRejBadFit_;
        return false;
    }

    log_trace( "(%s) input data OK", GetName().c_str() );
    return true;

}

bool I3ShadowFilter_13::SurvivesCuts(){

    if ( ! pulsesKey_.empty() ){

        // check NCH
        if ( nCh_ < nChThreshold_ ){
            log_debug("(%s) NCH(HLC)=%d < %d. ",
                      GetName().c_str(), nCh_, nChThreshold_);
            ++nRejNCh_;
            return false;
        }

        // check NSTRING
        if ( nString_ < nStringThreshold_ ){
            log_debug("(%s) NSTRING(HLC)=%d < %d. ",
                      GetName().c_str(), nString_, nStringThreshold_);
            ++nRejNString_;
            return false;
        }

    }

    // hooray!
    log_trace( "(%s) survived cuts", GetName().c_str() );
    return true;
}

bool I3ShadowFilter_13::CheckShadow(I3Frame &frame ){
    bool corsika_store = false;
    bool corsika_reuse = false;
    I3Time eventtime;
	    
    if ( corsikaMode_ ) {
        // ignore I3EventHeader, generate fake MJD or get it from the frame
        if ( frame.Has(corsikaMJDName_ + "MJD" ) ){
            // reusing previously generated fake MJD & associated Moon variables
            timeMJD_ =
                frame.Get<I3DoubleConstPtr>(corsikaMJDName_+"MJD")->value;
            shadowAzimuth_ =
                frame.Get<I3DoubleConstPtr>(corsikaMJDName_+"Azimuth")->value;
            shadowZenith_ =
                frame.Get<I3DoubleConstPtr>(corsikaMJDName_+"Zenith")->value;
            corsika_reuse = true;
            ++nReusedMJD_;
            // TODO (?): check that timeMJD_ is indeed within range
        } else {
            // generating fake MJD, associated Moon variables will be computed later
            timeMJD_ = corsikaRandService_->Uniform(mjdStart_,mjdEnd_);
	    eventtime = I3Time(timeMJD_);
            ++nGeneratedMJD_;
            corsika_store = true;
        }
    } else {
        // use I3EventHeader, do not generate/reuse a fake MJD
        I3EventHeaderConstPtr eh =
            frame.Get < I3EventHeaderConstPtr >(eventHeader_);
        eventtime = eh->GetStartTime();
        timeMJD_ = eventtime.GetModJulianDayDouble();

    }
    if ( ! corsika_reuse ){
        // this happens
        // (1) for exp data, no "corsika mode"
        // (2) for exp or sim data in "corsika mode",
        //     when fake shadow coordinates were not found in frame
        I3Direction shadowDir = GetShadow(eventtime);

        shadowZenith_ = shadowDir.GetZenith();
        shadowAzimuth_ = shadowDir.GetAzimuth();
    }
    if ( corsika_store ){
        // store these variables in the frame so that:
        // (1) other shadow filters can reuse them
        //     (e.g. conventional vs SuperDST on the Moon)
        // (2) they can be stored for use in analysis, filter studies
        frame.Put(corsikaMJDName_+"MJD",I3DoublePtr(new I3Double(timeMJD_)));
        frame.Put(corsikaMJDName_+"Azimuth",I3DoublePtr(new I3Double(shadowAzimuth_)));
        frame.Put(corsikaMJDName_+"Zenith",I3DoublePtr(new I3Double(shadowZenith_)));
    }
    if (shadowZenith_ > shadowZenithMaximum_) {
        log_debug("(%s) %s zenith %f > %f (max), "
                  "event being filtered.",
                  GetName().c_str(), shadowName_.c_str(),
                  shadowZenith_ / I3Units::degree,
                  shadowZenithMaximum_ / I3Units::degree);
        ++nRejShadow_;
        return false;
    }
    log_trace("(%s) OK: %s zenith %f <= %f (max)",
              GetName().c_str(), shadowName_.c_str(),
              shadowZenith_ / I3Units::degree,
              shadowZenithMaximum_ / I3Units::degree);
    return true;
}

bool I3ShadowFilter_13::InShadowWindow(){
    const I3Direction & dir = fit_->GetDir();
    double zenithDiff = dir.GetZenith() - shadowZenith_;
    double azimuthDiff = fmod(dir.GetAzimuth() - shadowAzimuth_,2*M_PI);
    /*
     * From the fmod man page:
     * "The  fmod()  function  computes  the  remainder  of dividing x by y.
     * The return value is x - n * y, where n is the quotient of x / y,
     * rounded towards zero to an integer."
     * This means that for example fmod(-10,2pi)=-3.71681 < -pi,
     * or in general that the return value of fmod(x,2pi) is in the interval
     * (-2pi,+2pi) and not (as desired) (-pi,pi].
     */
    if ( azimuthDiff > M_PI ){
        azimuthDiff -= 2 * M_PI;
    }
    if ( azimuthDiff <= -M_PI ){
        azimuthDiff += 2 * M_PI;
    }
    if ( solidAngleCorr_ ) azimuthDiff *= sin( dir.GetZenith() );
    if ((zenithDiff < zenithRange_[0]) || (zenithDiff > zenithRange_[1])) {
        log_trace("(%s) rejected: "
                  "particle %s has a zenith of %f, shadow zenith is %f",
                  GetName().c_str(), particleKey_.c_str(),
                  dir.GetZenith()/I3Units::degree,
                  shadowZenith_/I3Units::degree);
        ++nRejZenith_;
        return false;
    } else if ((azimuthDiff < azimuthRange_[0]) ||
               (azimuthDiff > azimuthRange_[1])) {
        log_trace("(%s) rejected: "
                  "particle %s has a azimuth of %fdeg, shadow azimuth is %fdeg",
                  GetName().c_str(), particleKey_.c_str(),
                  dir.GetAzimuth()/I3Units::degree,
                  shadowAzimuth_/I3Units::degree);
        ++nRejAzimuth_;
        return false;
    }

    return true;
}

void I3ShadowFilter_13::Finish()
{

    log_info("************ %s %s ShadowFilter Rate *************************",
             GetName().c_str(), shadowName_.c_str() );
    log_info("Parameters:");
    log_info("  Azimuth Range:  %f - %f",
             azimuthRange_[0] / I3Units::degree,
             azimuthRange_[1] / I3Units::degree);
    log_info("  Zenith Range:  %f - %f", zenithRange_[0] / I3Units::degree,
             zenithRange_[1] / I3Units::degree);
    log_info("Thresholds: Nch>=%d, Nstr>=%d, zenith(%s)<%.2fdeg",
             nChThreshold_, nStringThreshold_,
             shadowName_.c_str(), shadowZenithMaximum_/I3Units::degree );
    log_info("   ");

    log_info("Accepted events: %u", nKeep_ );
    log_info("Rejected because %s was too low: %u", shadowName_.c_str(), nRejShadow_ );
    log_info("Rejected because of missing data: %u", nRejMiss_ );
    log_info("Rejected because of a bad fit: %u", nRejBadFit_ );
    log_info("Rejected because of zenith diff: %u", nRejZenith_ );
    log_info("Rejected because of azimuth diff: %u", nRejAzimuth_ );
    log_info("Rejected because of low NCh: %u", nRejNCh_ );
    log_info("Rejected because of low NString: %u", nRejNString_ );
    if ( (nGeneratedMJD_>0 || nReusedMJD_>0) && !corsikaMode_ ){
        log_fatal("Curses & expletives! "
                  "MJDs are not supposed to be reused/generated except in corsika mode!");
    }
    if ( corsikaMode_ ){
        log_info("Generated MJD (corsika): %u", nGeneratedMJD_ );
        log_info("Reused MJD (corsika): %u", nReusedMJD_ );
        // maybe I should do the following with log_warn
        log_info("(%s) PLEASE make sure that the information about "
                      "the Corsika fake event time is stored and preserved, "
                      "that makes these data more useful.", GetName().c_str());
	log_info("(%s) As a MINIMUM the generated MJD time \"%s\" should "
                      "be stored. Having \"%s\"+\"%s\" and/or \"%s\"+\"%s\" "
                      "would be very convenient, but they can be recomputed "
                      "from the MJD, so if you want to keep storage minimal "
                      "then these can be omitted.", GetName().c_str(),
                      (corsikaMJDName_+"MJD").c_str(),
                      (corsikaMJDName_+"Azimuth").c_str(),
                      (corsikaMJDName_+"Zenith").c_str(),
                      (corsikaMJDName_+"RA").c_str(),
                      (corsikaMJDName_+"Decl").c_str());
    }

}

I3_MODULE(I3FilterModule<I3ShadowFilter_13>);
