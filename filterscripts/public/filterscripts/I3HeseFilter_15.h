#ifndef I3HESEFILTER_15_H
#define I3HESEFILTER_15_H

#include <filterscripts/I3JEBFilter.h>

#include <string>

class I3HeseFilter_15: public I3JEBFilter
{
  public:
    I3HeseFilter_15(const I3Context&);
    void Configure();
    bool KeepEvent(I3Frame& frame);
    void Finish();
    
    SET_LOGGER("I3HeseFilter_15");
    
  private:
    double minimumCharge_;
    std::string vetoName_;
    std::string chargeName_;
};


#endif
