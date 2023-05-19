#ifndef I3MUONFILTER_13_H
#define I3MUONFILTER_13_H

#include <filterscripts/I3JEBFilter.h>

class I3MuonFilter_13 : public I3JEBFilter
{
  public:
    I3MuonFilter_13(const I3Context&);
    void Configure();
    bool KeepEvent(I3Frame& frame);
    void Finish();

    SET_LOGGER("I3MuonFilter_13");
 
  private:
    double logl_zone1_;

    double slope_zone2_;
    double slope_zone3_;
    double intercept_zone2_;
    double intercept_zone3_;

    std::vector<double> cos_zenith_zone1_;
    std::vector<double> cos_zenith_zone2_;
    std::vector<double> cos_zenith_zone3_;

    std::string pri_particlekey_;
    std::string llh_paramskey_;
    std::string responsekey_;
};

#endif
