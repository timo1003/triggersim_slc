#ifndef I3BOOLFILTER_H
#define I3BOOLFILTER_H

#include <filterscripts/I3JEBFilter.h>

class I3BoolFilter : public I3JEBFilter
{
 public:

  I3BoolFilter(const I3Context&);
  void Configure();
  bool KeepEvent(I3Frame& frame);
  void Finish();

  SET_LOGGER("I3BoolFilter");

 private:
  std::string boolkey_;
};

#endif
