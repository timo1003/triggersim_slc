#ifndef I3EHEAlertFilter15_h
#define I3EHEAlertFilter15_h

#include <filterscripts/I3JEBFilter.h>

class I3EHEAlertFilter_15 : public I3JEBFilter
{

 public:

  I3EHEAlertFilter_15(const I3Context&);
  
  // Nominal
  void Configure();
  bool KeepEvent(I3Frame& frame);
  void Finish();

  // Final 2-D selection in NPE and cos(zen)
  bool Pass2D(double NPE, double coszen);

  // Looser 2-D selection in NPE and cos(zen)
  // This will be used for the 'heartbeat' to 
  // check all is well
  bool PassLooser2D(double NPE, double coszen);

  // Loosest 2-D selection in NPE and cos(zen)
  // Used for PnF initial testing
  bool PassLoosest2D(double NPE, double coszen);
  
  SET_LOGGER("I3EHEAlertFilter_15");
  
 private:

  bool m_skip2D;                     // Useful flag for testing
  bool m_looser;                     // User looser selection
  bool m_loosest;                    // User loosest selection

  std::string m_portiaSummaryKey;    // EHEPortia Event Summary
  std::string m_opheliaPartKey;      // Ophelia Improved Linefit particle
  std::string m_opheliaFitParamsKey; // Ophelia Imp. LineFit parameters
  
};

#endif
