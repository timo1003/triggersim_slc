#ifndef I3ONLINEL2FILTER13_H
#define I3ONLINEL2FILTER13_H

#include "filterscripts/I3JEBFilter.h"
#include "icetray/I3Context.h"

class I3OnlineL2Filter_13 : public I3JEBFilter
{
    public:

        I3OnlineL2Filter_13(const I3Context&);
        void Configure();
        bool KeepEvent(I3Frame& frame);
        void Finish();

        SET_LOGGER("I3OnlineL2Filter_13");

    private:

        std::string pri_particlekey_;
        std::string direct_hit_values_;
        std::string hit_multiplicity_values_;
        std::string hit_statistics_values_;
        std::string llh_paramskey_;

        std::vector<double> cos_zenith_zone1_;
        std::vector<double> cos_zenith_zone2_;
        std::vector<double> cos_zenith_zone3_;

        double ldirc_zone1_;
        unsigned int ndirc_zone1_;
        double plogl_param_zone1_;
        double plogl_zone1_;
        double qtot_zone1_;

        double qtot_slope_zone2_;
        double qtot_intercept_zone2_;
        double plogl_param_zone2_;
        double plogl_zone2_;
        double qtot_or_cut_zone2_;

        double qtot_kink_zone3_;
        double qtot_slope_zone3_;
        double qtot_intercept_zone3_;
        double plogl_param_zone3_;
        double plogl_zone3_;
        double qtot_or_cut_zone3_;

        double qtot_offset_zone3_;

};

#endif
