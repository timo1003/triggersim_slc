#ifndef I3EHEFILTER13_H
#define I3EHEFILTER13_H

#include <filterscripts/I3JEBFilter.h>

class I3EHEFilter_13 : public I3JEBFilter
{
 public:

  I3EHEFilter_13(const I3Context&);
  void Configure();
  bool KeepEvent(I3Frame& frame);
  void Finish();

  SET_LOGGER("I3EHEFilter_13");

 private:
  double threshold_;
  std::string responsekey_;
};

#endif

