#include <filterscripts/I3CascadeFilter_13.h>
#include <filterscripts/I3FilterModule.h>

I3_MODULE(I3FilterModule<I3CascadeFilter_13>);

#include <dataclasses/physics/I3RecoPulse.h>
#include <recclasses/I3TensorOfInertiaFitParams.h>
#include <recclasses/I3HitMultiplicityValues.h>
#include <recclasses/I3CscdLlhFitParams.h>
#include <dataclasses/I3Double.h>
#include <dataclasses/physics/I3Trigger.h>
#include <dataclasses/physics/I3TriggerHierarchy.h>
#include <dataclasses/physics/I3Particle.h>
#include <icetray/OMKey.h>
#include <icetray/I3Int.h>

using namespace I3TriggerHierarchyUtils;



I3CascadeFilter_13::I3CascadeFilter_13(const I3Context& context) :
	I3JEBFilter(context),
	hitMultKey_("HitMultiplicity"),
	llhParticleKey_("PoleTrackLlhFit"),
	cscdllhparamskey_("cscdllhParams"),
	toiparamskey_("toiParams"),
	lfkey_("LineFit"),
	minNString_(2),
	cosThetaMax_(0.21),
	CscdrLlh1_(10.7),
	CscdrLlh2_(10.5),
	toievalratio_(0.05),
	lfvelocity_(0.12),
	cscdllhkey_(""),
	eratiokey_(""),
	lfvelkey_("")
{
    AddParameter("HitMultiplicityKey",
                 "The I3HitMultiplicityValues in the frame where NString can be found",
                 hitMultKey_);
    
    AddParameter("LlhParticleKey",
                 "The I3Particle in the frame to be used for getting zenith for above, ie track-llh)",
                 llhParticleKey_);
    
    AddParameter("CscdLlhFitParams",
                 "Name of the I3CscdLlhFitParams in the frame.",
                 cscdllhparamskey_);
    
    AddParameter("TensorOfInertiaFitParams",
                 "Name of the I3TensorOfInertiaFitParams in the frame.",
                 toiparamskey_);
    
    AddParameter("LinefitKey",
                 "Name of the linefit I3Particle object in the frame.",
                 lfkey_);       
    
    AddParameter("minNString",
                 "Minimum number of hit strings",
                 minNString_);	      
    
    AddParameter("cosThetaMax",
                 "The cos theta value for separating regions 1 and 2",
                 cosThetaMax_);	      
    
    AddParameter("CscdrLlh1",
                 "cascade rllh cut for region 1",
                 CscdrLlh1_);
    
    AddParameter("CscdrLlh2",
                 "cascade rllh cut for region 2",
                 CscdrLlh2_);     
    
    AddParameter("ToIEvalRatio",
                 "Minimum Tensor of Inertia Eigenvalue Ratio for region 2",
                 toievalratio_);
    
    AddParameter("LinefitVelocity",
                 "Maximum Linefit Velocity for region 2",
                 lfvelocity_);
    
    AddParameter("CascadeLlhKey",
                 "Name of the I3Double object where the cascade rllh should be "
                 "stored.  If empty, the cascade rllh will not be stored.",
                 cscdllhkey_);
    
    AddParameter("EvalRatioKey",
                 "Name of the I3Double object where the EvalRatio should be "
                 "stored.  If empty, the EvalRatio will not be stored.",
                 eratiokey_);
    
    AddParameter("LFVelKey",
                 "Name of the I3Double object where the LineFitVel should be "
                 "stored.  If empty, the LineFitVel will not be stored.",
                 lfvelkey_);
    
    
    
}

void I3CascadeFilter_13::Configure()
{
	// input
    GetParameter("HitMultiplicityKey",hitMultKey_);
    GetParameter("LlhParticleKey",llhParticleKey_);
    GetParameter("CscdLlhFitParams",cscdllhparamskey_);
    GetParameter("TensorOfInertiaFitParams",toiparamskey_);
    GetParameter("LinefitKey",lfkey_);
	
	// cut values
    GetParameter("minNString",minNString_);
    GetParameter("cosThetaMax",cosThetaMax_);
    GetParameter("CscdrLlh1",CscdrLlh1_);
    GetParameter("CscdrLlh2",CscdrLlh2_);
    GetParameter("ToIEvalRatio",toievalratio_);
    GetParameter("LinefitVelocity",lfvelocity_);
	
	// output
    GetParameter("CascadeLlhKey",cscdllhkey_);
    GetParameter("EvalRatioKey",eratiokey_);
    GetParameter("LFVelKey",lfvelkey_);
    
}

bool I3CascadeFilter_13::KeepEvent(I3Frame& frame)
{
    I3HitMultiplicityValuesConstPtr hitMult =
    frame.Get<I3HitMultiplicityValuesConstPtr>(hitMultKey_);
    
    I3ParticleConstPtr llhParticle =
    frame.Get<I3ParticleConstPtr>(llhParticleKey_);
    
    I3CscdLlhFitParamsConstPtr cscdllhparams =
    frame.Get<I3CscdLlhFitParamsConstPtr>(cscdllhparamskey_);
    
    I3TensorOfInertiaFitParamsConstPtr toiparams = 
    frame.Get<I3TensorOfInertiaFitParamsConstPtr>(toiparamskey_);
    
    I3ParticleConstPtr linefit = 
    frame.Get<I3ParticleConstPtr>(lfkey_);
    
    // prechecks
    if (hitMult)
    {
	if (hitMult->GetNHitStrings() < minNString_) // too few strings hit
	{
		log_trace("Event has too few hit strings.  Filtering event from data stream.");
		return false;
	}
    }
    
    // now run the actual cascade filter
    if (llhParticle && cscdllhparams) // needed for cascade filter in any case
    {
    	if (cos(llhParticle->GetZenith()) < cosThetaMax_) // upgoing branch, region 1
    	{
    		if (cscdllhparams->GetReducedLlh() <= CscdrLlh1_)
    		{
				log_debug("Event satisifies cut in region 1 of filter. Keeping event.");
		        if(cscdllhkey_ != "")
		        {
		            I3DoublePtr cscdllhval(new I3Double(cscdllhparams->GetReducedLlh()));
		            frame.Put(cscdllhkey_,cscdllhval);
		        }
		        return true;
    		}
    	}
    	else // downgoing branch, region 2
    	{
    		if (linefit && toiparams) // needed for cascade filter in region 2
    		{
    			if (cos(llhParticle->GetZenith()) >= cosThetaMax_ && 
					cscdllhparams->GetReducedLlh() <= CscdrLlh2_ &&
					toiparams->evalratio >= toievalratio_ && 
					linefit->GetSpeed() <= lfvelocity_)
				{
					log_debug("Event satisfies the Cascade Filter region 2.  Keeping event.");
		            if(cscdllhkey_ != "")
		            {
		                I3DoublePtr cscdllhval(new I3Double(cscdllhparams->GetReducedLlh()));
		                frame.Put(cscdllhkey_,cscdllhval);
		            }
		            if(eratiokey_ != "")
		            {
		                I3DoublePtr evalratio(new I3Double(toiparams->evalratio));
		                frame.Put(eratiokey_,evalratio);
		            }
		            if(lfvelkey_ != "")
		            {
		                I3DoublePtr lfvelocity(new I3Double(linefit->GetSpeed()));
		                frame.Put(lfvelkey_,lfvelocity);
		            }
		            return true;
				}
    		}
    		else
    		{
    			log_debug("Object needed for Cascade Filter does not exist in frame. Ignoring Event.");
    			return false;
    		}
    	}
    }
    else
    {
    	log_debug("Object needed for Cascade Filter does not exist in frame. Ignoring Event.");
    	return false;
    }
    
    log_trace("Event does not satisfy the Cascade Filter.  Filtering event from data stream.");
    return false;
    
}

void I3CascadeFilter_13::Finish()
{
    log_info("CascadeFilter Rate *************************");
    log_info("Parameters:");
    log_info("  Cos Zenith separating filter regions: %.2f", cosThetaMax_);
    log_info("  Max Cscd rLlh for region 1:           %.2f", CscdrLlh1_);
    log_info("  Max Cscd rLlh for region 2:           %.2f", CscdrLlh2_);
    log_info("  Min Toi Eval Ratio for region 2:      %.2f", toievalratio_);
    log_info("  Max LineFit velocity for region2:     %.2f", lfvelocity_);
    log_info("   ");
}
