#include <filterscripts/I3VEFFilter_13.h>
#include <filterscripts/I3FilterModule.h>

I3_MODULE(I3FilterModule<I3VEFFilter_13>);

#include <dataclasses/geometry/I3Geometry.h>
#include <dataclasses/physics/I3RecoPulse.h>
#include <dataclasses/physics/I3Particle.h>
#include <dataclasses/I3Double.h>
#include <icetray/I3Units.h>

I3VEFFilter_13::I3VEFFilter_13(const I3Context& context) :
  I3JEBFilter(context),
  linefitcut_(2.9),
  muonllhcut_(2.6),
  toplayerDOMcut_(5),
  allpulseskey_("InitialPulseSeriesReco"),
  poleMuonLlhFit_("PoleMuonLlhFit"),
  poleMuonLinefit_("PoleMuonLinefit"),
  singleStringReq_(false)
{
  AddParameter("LinefitCut",
	       "Remove events that have linefit zenith angle less than this",
	       linefitcut_);

  AddParameter("MuonLlhCut",
	       "Remove events that have MuonLlh zenith angle less than this",
	       muonllhcut_);

  AddParameter("ToplayerDOMcut",
	       "How many layers of DOM's should be used in the veto cap",
	       toplayerDOMcut_);
  
  AddParameter("PoleMuonLlhFit",
	       "The standard log likelihood linefit performed by Muon Group",
	       poleMuonLlhFit_);

  AddParameter("PoleMuonLinefit",
	       "The standard muon linefit",
	       poleMuonLinefit_);

  AddParameter("RecoPulsesKey",
	       "Key for all the reco pulses.",
	       allpulseskey_);

  AddParameter("SingleStringRequirement",
	       "Reject events with pulses on multiple strings.",
	       singleStringReq_);
}

void I3VEFFilter_13::Configure()
{
  GetParameter("LinefitCut",linefitcut_);
  GetParameter("MuonLlhCut",muonllhcut_);
  GetParameter("ToplayerDOMcut",toplayerDOMcut_);
  GetParameter("RecoPulsesKey",allpulseskey_);
  GetParameter("PoleMuonLlhFit",poleMuonLlhFit_);
  GetParameter("PoleMuonLinefit",poleMuonLinefit_);
  GetParameter("SingleStringRequirement",singleStringReq_);
  nRejNOmuonllhsrt=nRejNOpulses=nRejIsDownGoingLlh=nRejNOlinefit= nRejIsDownGoingLineFit= nRejNOgeo=nRejTopLayers=nRejMultipleStrings=nDOMs=0;
} 

bool I3VEFFilter_13::KeepEvent(I3Frame& frame)
{
  I3RecoPulseSeriesMapConstPtr all =
    frame.Get<I3RecoPulseSeriesMapConstPtr>(allpulseskey_);
  if(!all)
    {
      log_debug("Pulses not found.  Ignoring event.");
      nRejNOpulses++;
      return false;
    }

  //  MuonLLH upgoing cut 
  I3ParticleConstPtr muonllhsrt = 
    frame.Get<I3ParticleConstPtr>(poleMuonLlhFit_);
  if(!muonllhsrt)
    {
      log_debug("Could not find the MuonSRTllh reco.  Ignoring event.");
      nRejNOmuonllhsrt++;
      return false;
    }
  bool IsUpGoingLlh = (muonllhsrt->GetZenith())>muonllhcut_;
  if(!IsUpGoingLlh)
    {
      log_debug("The Event's MuonSRTllh reco is downgoing.  Ignoring event.");
      nRejIsDownGoingLlh++;
      return false;
    }

  //  Linefit upgoing cut 
  I3ParticleConstPtr linefit =
    frame.Get<I3ParticleConstPtr>(poleMuonLinefit_);
  if(!linefit)
    {
      log_debug("Could not find the linefit.  Ignoring event.");
      nRejNOlinefit++;
      return false;
    }

  bool IsUpGoingLinefit = (linefit->GetZenith())>linefitcut_;
  if(!IsUpGoingLinefit)
    {
      log_debug("The Event's linefit is downgoing.  Ignoring event.");
      nRejIsDownGoingLineFit++;
      return false;
    }

  //  First loop over pulses for quick checks
  I3GeometryConstPtr geometry =
    frame.Get<I3GeometryConstPtr>();
  if(!geometry)
    {
      log_debug("Geometry not found.  Ignoring event.");
      nRejNOgeo++;
      return false;
    }

  int ndoms =0;
  int stringhit = std::numeric_limits<int>::max();
  for(I3RecoPulseSeriesMap::const_iterator alliter = all->begin();
      alliter != all->end();
      ++alliter)
    {
      // Ignore DOMs with no pulses
      if(alliter->second.size() == 0) continue;

      // Check for pulses in the top n DOM layers
      if(alliter->first.GetOM() < (toplayerDOMcut_ + 1))
	{
	  log_debug("hit in the top layers! Veto event");
	  nRejTopLayers++;
	  return false;
	}

      // Check that we stay on one string
      int currstring = (alliter->first).GetString();
      if(stringhit != currstring && singleStringReq_)
        {
          if(stringhit == std::numeric_limits<int>::max())
            {
	      stringhit = currstring;
            }
          else
            {
              log_debug("Found pulses on two different strings.  Ignoring event.");
              nRejMultipleStrings++;
              return false;
            }
	}
      ndoms++;
    }

  nDOMs+=ndoms;

  //  Final Acceptance
  log_debug("Wow.  This event made it through all those cuts.  Congratulations event.");
  return true;
}

void I3VEFFilter_13::Finish()
{
  log_info("VEFFilter Rate *************************");
  log_info("PARAMETERS :");
  log_info("  TopLayerDOMcut : %d",toplayerDOMcut_);
  log_info("  LineFitcut : %f",linefitcut_);
  log_info("  MuonLlhcut: %f",muonllhcut_);
  log_info("# REJECTED EVENTS : ");
  log_info("  TopLayerDOMcut : %d",nRejTopLayers);
  log_info("  LineFit cut : %d",nRejIsDownGoingLineFit);
  log_info("  MuonLlh cut: %d",nRejIsDownGoingLlh);
  log_info("  No pulses: %d",nRejNOpulses);
  log_info("  No muonllhsrt: %d",nRejNOmuonllhsrt);
  log_info("  No linefit: %d",nRejNOlinefit);
  log_info("  No geo: %d",nRejNOgeo);
  log_info("  Multiple Strings: %d",nRejMultipleStrings);
  log_info(" nDOMs : %d", nDOMs);
  log_info(" ");
}
