#include <filterscripts/I3MuonFilter_13.h>

#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3MuonFilter_13>);

#include <icetray/I3Units.h>
#include <icetray/I3Bool.h>
#include <gulliver/I3LogLikelihoodFitParams.h>
#include <dataclasses/physics/I3Particle.h>
#include <dataclasses/physics/I3RecoHit.h>
#include <dataclasses/physics/I3Trigger.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>
#include <dataclasses/physics/I3DOMLaunch.h>
#include <dataclasses/physics/I3RecoPulse.h>

using namespace I3TriggerHierarchyUtils;

I3MuonFilter_13::I3MuonFilter_13(const I3Context& context) :
  I3JEBFilter(context),
  pri_particlekey_("ipdfGConvolute"),
  responsekey_("InitialPulseSeriesReco")

{
  AddParameter("IceCubeResponseKey",
	       "Name of the I3RecoHitSeriesMap in the frame to use."
	       "Should contain only IceCube Pulses, with NFE, SeededRT, "
	       "and TimeWindow Cleaning already done.",
	       responsekey_);


  cos_zenith_zone1_.resize(0);
  cos_zenith_zone1_.push_back(-1.0);
  cos_zenith_zone1_.push_back(0.2);

  cos_zenith_zone2_.resize(0);
  cos_zenith_zone2_.push_back(0.2);
  cos_zenith_zone2_.push_back(0.5);

  cos_zenith_zone3_.resize(0);
  cos_zenith_zone3_.push_back(0.5);
  cos_zenith_zone3_.push_back(1.0);

  AddParameter("CosZenithZone1",
	       "Vector of minimum zenith angle cuts to be matched with its corresponding Nchan cut for Zone 1.  "
	       "If an event satisfies ANY pair of zenith/Nchan cuts, the event will be kept.",
	       cos_zenith_zone1_);

  AddParameter("CosZenithZone2",
	       "Vector of minimum zenith angle cuts to be matched with its corresponding Nchan cut for Zone 2.  "
	       "If an event satisfies ANY pair of zenith/Nchan cuts, the event will be kept.",
	       cos_zenith_zone2_);

  AddParameter("CosZenithZone3",
	       "Vector of minimum zenith angle cuts to be matched with its corresponding Nchan cut for Zone 3.  "
	       "If an event satisfies ANY pair of zenith/Nchan cuts, the event will be kept.",
	       cos_zenith_zone3_);


  AddParameter("PriParticleKey",
	       "Name of the I3Particle in the frame.",
	       pri_particlekey_);
  AddParameter("LLHFitParamsKey",
	       "Name of the LLH Fit Params key in the frame, to use as source for rlogl.",
	       llh_paramskey_);

  


  logl_zone1_ = 8.7;
  
  AddParameter("LogLZone1",
	       "Max value of loglikelihood/(nch -3) for Zone 1.",
	       logl_zone1_);

  slope_zone2_ = 3.9;
  intercept_zone2_ = 0.65;

  AddParameter("SlopeZone2",
	       "Min value of intcharge for Zone 2.",
	       slope_zone2_);
  AddParameter("InterceptZone2",
	       "Min value of intcharge for Zone 2.",
	       intercept_zone2_);

  slope_zone3_ = 0.6;
  intercept_zone3_ = 2.3;

  AddParameter("SlopeZone3",
	       "Min value of intcharge for Zone 3.",
	       slope_zone3_);
  AddParameter("InterceptZone3",
	       "Min value of intcharge for Zone 3.",
	       intercept_zone3_);

  //  AddParameter("IceCubeTriggers",
  //	       "Name of the I3TriggerHierarchy for IceCube triggers",
  //	       triggerkey_);
  
  }

void I3MuonFilter_13::Configure()
{
GetParameter("CosZenithZone1",cos_zenith_zone1_);
GetParameter("CosZenithZone2",cos_zenith_zone2_);
GetParameter("CosZenithZone3",cos_zenith_zone3_);
GetParameter("LogLZone1",logl_zone1_);
GetParameter("SlopeZone2",slope_zone2_);
GetParameter("InterceptZone2",intercept_zone2_);
GetParameter("SlopeZone3",slope_zone3_);
GetParameter("InterceptZone3",intercept_zone3_);
  
GetParameter("PriParticleKey",pri_particlekey_);
GetParameter("LLHFitParamsKey",llh_paramskey_);
GetParameter("IceCubeResponseKey",responsekey_);
}

bool I3MuonFilter_13::KeepEvent(I3Frame& frame)
{
  bool toreturn = false;

  unsigned int nch_;
  double intCharge_;
  double logintCharge_;

  double cos_pri_zenith_ = -1;

  if ( ! frame.Has(responsekey_) )
  {
    log_debug("-> event does not have responsekey %s, discarding it",responsekey_.c_str());
    return toreturn; //reject
  }

  const I3RecoPulseSeriesMap& iniceChannels = frame.Get<I3RecoPulseSeriesMap>(responsekey_);

  
  if (iniceChannels.size() != 0)
  { 

    nch_ = iniceChannels.size();
    
    intCharge_ = 0;
    
    I3RecoPulseSeriesMap::const_iterator miter;
    
    for(miter=iniceChannels.begin(); miter!=iniceChannels.end(); miter++)
    {
      
      const I3RecoPulseSeries &thishitinfo = miter->second;
	    
      for (I3RecoPulseSeries::const_iterator iseries = thishitinfo.begin();
	   iseries != thishitinfo.end(); iseries++)
      {
	intCharge_ += iseries->GetCharge();
      }
      
    }
    
    log_trace("Event has %d hit channels and a total charge of %f",
	      nch_, intCharge_);
    
    logintCharge_ = log10(intCharge_);    
  }
  else
  {
    log_info("-> event has empty RecoPulseSeries ... rejecting");
    return toreturn; //reject
  }
  
  I3ParticleConstPtr pri_i3part = frame.Get<I3ParticleConstPtr>(pri_particlekey_);
  I3LogLikelihoodFitParamsConstPtr llhparams = frame.Get<I3LogLikelihoodFitParamsConstPtr>(llh_paramskey_);
  //  I3TriggerHierarchyConstPtr triggers = frame.Get<I3TriggerHierarchyConstPtr>(triggerkey_);
  
  if(!pri_i3part || pri_i3part->GetFitStatus() != I3Particle::OK)
  {
    log_debug("Primary gulliver LLH did not succeed.  Ignoring event.");
    return toreturn;
  }
  else
  {

    cos_pri_zenith_ =  cos(pri_i3part->GetZenith());

    if( (cos_pri_zenith_ > cos_zenith_zone1_[0]) && (cos_pri_zenith_ <= cos_zenith_zone1_[1]) && 
        (pri_i3part->GetFitStatus() == I3Particle::OK) ) 
    {
       if( (llhparams->rlogl_*(nch_ - 5)/(nch_ - 3)) <= logl_zone1_ )
       {
         log_trace("Event has %f intcharge and "
  	         "passes the minimum threshold of %f",
	        (double) llhparams->rlogl_*(nch_ - 5)/(nch_ - 3), logl_zone1_ );
         toreturn = true;
       }
    }

    if( (cos_pri_zenith_ > cos_zenith_zone2_[0] && cos_pri_zenith_ <= cos_zenith_zone2_[1]) && 
        (pri_i3part->GetFitStatus() == I3Particle::OK) ) 
    {
      if( logintCharge_ > slope_zone2_*cos_pri_zenith_ + intercept_zone2_ )
      {
        log_trace("Event has %f intcharge and "
		  "passes the minimum threshold of %f",
	          (double) logintCharge_, slope_zone2_*cos_pri_zenith_ + intercept_zone2_);
        toreturn = true;
      }
    }

    if( (cos_pri_zenith_ > cos_zenith_zone3_[0] && cos_pri_zenith_ <= cos_zenith_zone3_[1]) && 
        (pri_i3part->GetFitStatus() == I3Particle::OK) ) 
    {
      if( logintCharge_ > slope_zone3_*cos_pri_zenith_ + intercept_zone3_ )
      {
	log_trace("Event has %f intcharge and "
		  "passes the minimum threshold of %f",
		  (double) logintCharge_, slope_zone3_*cos_pri_zenith_ + intercept_zone3_ );
        toreturn = true;
      }    
    }      

  }

  return toreturn;
}

void I3MuonFilter_13::Finish()
{
  log_info("MuonFilter Rate *************************");
  log_info("Parameters:");
  int cont;

  int counter1 = 1;
  cont = 0;
  while(cont < int(cos_zenith_zone1_.size()) - 1)
    {
      log_info("  -- Zone 1 Cut Pair %d",counter1);
      log_info("  Cos(Zenith):  %f",cos_zenith_zone1_[cont]);
      log_info("  Cos(Zenith):  %f",cos_zenith_zone1_[cont + 1]);
      ++cont;
      ++counter1;
    }
  int counter2 = 1;
  cont = 0;
  while(cont < int(cos_zenith_zone2_.size()) - 1)
    {
      log_info("  -- Zone 2 Cut Pair %d",counter2);
      log_info("  Cos(Zenith):  %f",cos_zenith_zone2_[cont]);
      log_info("  Cos(Zenith):  %f",cos_zenith_zone2_[cont + 1]);
      ++cont;
      ++counter2;
    }
  int counter3 = 1;
  cont = 0;
  while(cont < int(cos_zenith_zone3_.size()) - 1)
    {
      log_info("  -- Zone 3 Cut Pair %d",counter3);
      log_info("  Cos(Zenith):  %f",cos_zenith_zone3_[cont]);
      log_info("  Cos(Zenith):  %f",cos_zenith_zone3_[cont + 1]);
      ++cont;
      ++counter3;
    }

  log_info("   ");
}
