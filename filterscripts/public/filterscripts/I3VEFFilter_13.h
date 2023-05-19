#ifndef JEB_FILTER_I3VEFFILTER13_H
#define JEB_FILTER_I3VEFFILTER13_H

#include "filterscripts/I3JEBFilter.h"

class I3VEFFilter_13 : public I3JEBFilter
{
 public:
  I3VEFFilter_13(const I3Context& context);
  bool KeepEvent(I3Frame& frame);
  void Configure();
  void Finish();

  SET_LOGGER("I3VEFFilter_13");

 private:
  int nRejNOmuonllhsrt, nRejNOpulses, nRejIsDownGoingLlh, nRejNOlinefit, nRejIsDownGoingLineFit, nRejNOgeo, nRejTopLayers, nRejMultipleStrings, nDOMs;
  double linefitcut_;
  double muonllhcut_;
  unsigned int toplayerDOMcut_;
  std::string allpulseskey_;
  std::string poleMuonLlhFit_;
  std::string poleMuonLinefit_;
  bool singleStringReq_;
};

#endif
