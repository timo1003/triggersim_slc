#ifndef I3FILTERMINBIAS_H
#define I3FILTERMINBIAS_H

#include <filterscripts/I3JEBFilter.h>

class I3FilterMinBias : public I3JEBFilter
{
 public:

  I3FilterMinBias(const I3Context&);
  void Configure();
  bool KeepEvent(I3Frame& frame);
  void Finish();

  SET_LOGGER("I3FilterMinBias");

 private:

};

#endif
