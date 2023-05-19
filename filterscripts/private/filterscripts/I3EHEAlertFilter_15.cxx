
//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=//
// A filtering script to select out high energy track like events //
// meant to be used for generating alerts. It has 100% overlap    //
// with EHE Filter, and most likely others as well.               //
//-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=//

#include <filterscripts/I3EHEAlertFilter_15.h>
#include <filterscripts/I3FilterModule.h>
#include <recclasses/I3PortiaEvent.h>
#include <recclasses/I3OpheliaFirstGuessTrack.h>
#include <dataclasses/physics/I3Particle.h>

I3_MODULE(I3FilterModule<I3EHEAlertFilter_15>);

//----------------------------------------------//
// Constructor
//----------------------------------------------//
I3EHEAlertFilter_15::I3EHEAlertFilter_15(const I3Context& context) :
  I3JEBFilter(context),
  m_skip2D(false),
  m_looser(false),
  m_loosest(false),
  m_portiaSummaryKey("EHESummaryPulseInfo"),
  m_opheliaPartKey(""),
  m_opheliaFitParamsKey("")
{

  AddParameter("PortiaEventName",
	       "Name of the PortiaEvent in the frame.",
	       m_portiaSummaryKey);

  AddParameter("EHEFirstGuessParticleName",
	       "Name of the EHEFirstGuess particle in the frame.",
	       m_opheliaPartKey);

  AddParameter("EHEFirstGuessName",
	       "Name of the EHEFirstGuess fit parameters in the frame.",
	       m_opheliaFitParamsKey);

  AddParameter("Skip2DTest",
	       "Flag to turn off 2D requirement. Used for testing.",
	       m_skip2D);

  AddParameter("Looser",
	       "Flag to use the looser 2D requirement. Used for heartbeat.",
	       m_looser);

  AddParameter("Loosest",
	       "Flag to use the loosest 2D requirement. Used for PnF testing.",
	       m_loosest);

}

//----------------------------------------------//
// Configure
//----------------------------------------------//
void I3EHEAlertFilter_15::Configure()
{

  GetParameter("PortiaEventName",m_portiaSummaryKey);
  GetParameter("EHEFirstGuessParticleName",m_opheliaPartKey);
  GetParameter("EHEFirstGuessName",m_opheliaFitParamsKey);
  GetParameter("Skip2DTest", m_skip2D);
  GetParameter("Looser", m_looser);
  GetParameter("Loosest", m_loosest);
  
}

//----------------------------------------------//
// Decide to keep event
//----------------------------------------------//
bool I3EHEAlertFilter_15::KeepEvent(I3Frame& frame)
{

  // The requirements will be placed on four
  // variables from portia and first guess fit.
  double lognpe = 0.;
  double nch    = 0.;
  double coszen = 0.;
  double rchi2  = 0.;


  // Get NPE and Nch
  I3PortiaEventConstPtr portia_ptr = frame.Get<I3PortiaEventConstPtr>(m_portiaSummaryKey);
  if( portia_ptr ){
    lognpe = log10(portia_ptr->GetTotalBestNPEbtw());
    nch    = portia_ptr->GetTotalNchbtw();
  }
  else{
    log_error("EHEAlertFilter: No portia event information found!");
    return false;
  }

  // Get coszen 
  I3ParticleConstPtr ophPart_ptr = frame.Get<I3ParticleConstPtr>(m_opheliaPartKey);
  if( ophPart_ptr ) coszen = cos( ophPart_ptr->GetZenith() );
  else{
    log_error("EHEAlertFilter: No fit result from ophelia!");
    return false;
  }


  // Get Improved line fit
  I3OpheliaFirstGuessTrackConstPtr ophFGT_ptr = 
    frame.Get<I3OpheliaFirstGuessTrackConstPtr>(m_opheliaFitParamsKey);
  if( ophFGT_ptr ) rchi2 = ophFGT_ptr->GetFitQuality();
  else{
    log_error("EHEAlertFilter: No Ophelia First Guess track pointer!");
    return false;
  }

  // 'Level 3' requirements
  if( !(lognpe > 3.6 && nch > 300 ) ) return false;
  if( !(25 < rchi2 && rchi2 < 80 ) )  return false;

  // 'Level 4' requirements
  if( m_skip2D )  return true;
  if( m_looser )  return PassLooser2D(lognpe, coszen) && !Pass2D(lognpe,coszen);
  if( m_loosest ) return PassLoosest2D(lognpe, coszen) && !Pass2D(lognpe,coszen);
  return Pass2D(lognpe, coszen);

}

//----------------------------------------------//
// Final signal region requirements
//----------------------------------------------//
bool I3EHEAlertFilter_15::Pass2D(double lognpe, 
				 double coszen)
{

  // Lower zenith requirement
  if( coszen < 0.1 ) return lognpe >= 3.6;

  // Elliptical requirement
  return lognpe >= 3.6 + 2.99 * sqrt(1 - pow((coszen-0.93)/0.83,2));

}

//----------------------------------------------//
// Looser requirement for heartbeat
//----------------------------------------------//
bool I3EHEAlertFilter_15::PassLooser2D(double lognpe, 
				       double coszen)
{

  // Lower zenith requirement
  // Most up-going events will be interesting
  // so don't include this in the heart-beat alert
  if( coszen < 0.1 )  return false;

  // Elliptical requirement
  return lognpe >= 3.6 + 1.0 * sqrt(1 - pow((coszen-0.85)/0.75,2));

}

//----------------------------------------------//
// Loosest requirement for PnF testing
//----------------------------------------------//
bool I3EHEAlertFilter_15::PassLoosest2D(double lognpe, 
					double coszen)
{

  // Lower zenith requirement
  // Most up-going events will be interesting
  // so don't include this in the heart-beat alert
  if( coszen < 0.1 )  return false;

  // Elliptical requirement
  return lognpe >= 3.6 + 0.75 * sqrt(1 - pow((coszen-0.70)/0.60,2));

}

//----------------------------------------------//
// Finish up
//----------------------------------------------//
void I3EHEAlertFilter_15::Finish()
{

  log_info("EHEAlertFilter Rate *************************");
  log_info("   ");

}
