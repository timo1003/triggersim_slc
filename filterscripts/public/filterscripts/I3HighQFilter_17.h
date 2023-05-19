#ifndef I3HIGHQFILTER_17_H
#define I3HIGHQFILTER_17_H

#include <filterscripts/I3JEBFilter.h>

#include <string>

class I3HighQFilter_17: public I3JEBFilter
{
  public:
    I3HighQFilter_17(const I3Context&);
    void Configure();
    bool KeepEvent(I3Frame& frame);
    void Finish();
    
    SET_LOGGER("I3HighQFilter_17");
    
  private:
    double minimumCharge_;
    std::string vetoName_;
    std::string chargeName_;
};


#endif
